# -*- coding: utf-8 -*-
"""
cycle_signal.py
===============
TradeAI(tradingview-ai-chat)의 RSI 파동/멀티지표 분석 엔진(core.rsi_wave)을
'장기(월봉)·스윙(주봉)·단기(일봉)' 3개 시간축으로 돌려서,
상세 전술 리포트가 아니라 **저점권/고점권 수준의 사이클 판정**만 뽑아낸다.
그리고 온체인 매수신호(compute_buy_signal)와 결합해 시간축별 '총 매매 의견'을 만든다.

데이터/지표 계산은 core.market_data(Binance + data-api.binance.vision 미러)를 그대로 사용하므로
미국 배포 서버에서도 캔들 수집이 된다. (OI/펀딩만 선물 API라 미국에선 빠질 수 있으나 엔진이 graceful 처리)
"""

import core.rsi_wave as rw

# 우리 시간축 정의: (라벨, 엔진 TF, 한 줄 설명)
HORIZONS = [
    ("장기", "1개월", "월봉 · 사이클/투자 관점"),
    ("스윙", "1주", "주봉 · 수 주~수 개월"),
    ("단기", "1일", "일봉 · 수 일~수 주"),
]
_TFS = [tf for _, tf, _ in HORIZONS]


def _distill(r):
    """엔진의 풍부한 TF 결과 → 저점/고점 수준 판정으로 축약."""
    if not r or r.get("error"):
        return None
    rsi = r.get("rsi", 50) or 50
    cyc = r.get("cycle_pos", "") or ""
    regime = r.get("regime", "MIXED")
    synth = r.get("synth_div") or {}
    div_kind = (synth.get("overall_bias") or "") if isinstance(synth, dict) else ""

    # 5단계 레벨 판정 (RSI 절대수준 + 엔진 사이클 라벨)
    if "과매도" in cyc or rsi <= 22:
        level, label, color = "low", "저점권", "#166534"
    elif "과매수" in cyc or rsi >= 78:
        level, label, color = "high", "고점권", "#991b1b"
    elif cyc.startswith("🟠 하락") or "반등" in cyc:
        level, label, color = "low_near", "저점 근접", "#1a7f37"
    elif cyc.startswith("🟠 상승"):
        level, label, color = "high_near", "고점 근접", "#bc4c00"
    else:
        level, label, color = "mid", "중립", "#854d0e"

    # 다이버전스 보정 — RSI 레벨로 게이팅 (낮은 RSI에 '천장', 높은 RSI에 '바닥' 오판 방지)
    note = ""
    bias = div_kind.upper()
    if "BULL" in bias and rsi <= 52:          # 하단부 상승 다이버전스 = 바닥 강화
        note = "상승 다이버전스 — 바닥 신호 강화"
        if level == "mid":
            level, label, color = "low_near", "저점 근접", "#1a7f37"
        elif level == "low_near":
            level, label, color = "low", "저점권", "#166534"
    elif "BEAR" in bias and rsi >= 48:        # 상단부 하락 다이버전스 = 천장 강화
        note = "하락 다이버전스 — 천장 신호 강화"
        if level == "mid":
            level, label, color = "high_near", "고점 근접", "#bc4c00"
        elif level == "high_near":
            level, label, color = "high", "고점권", "#991b1b"

    return {
        "rsi": round(rsi, 1),
        "regime": regime,
        "regime_kr": rw.REGIME_LABELS.get(regime, regime),
        "cycle_pos": cyc,
        "cycle_desc": r.get("cycle_desc", ""),
        "ema_trend": r.get("ema_trend", ""),
        "level": level,
        "label": label,
        "color": color,
        "note": note,
        "price": r.get("price"),
    }


def analyze_cycle(symbol="BTCUSDT"):
    """월/주/일봉 RSI 사이클 분석 → 시간축별 판정 dict 반환."""
    rw.WAVE_TIMEFRAMES = _TFS  # 엔진을 우리 3개 TF로 제한
    try:
        res = rw.analyze_rsi_wave(symbol)
    except Exception as e:
        return {"error": str(e)}
    out = {}
    for name, tf, desc in HORIZONS:
        d = _distill(res.get(tf, {}))
        if d:
            d["desc"] = desc
            out[name] = d
    return out


# 레벨 → 한 줄 스탠스 (TA 단독)
_STANCE = {
    "low": "역사적/구간 저점권 — 반등 전환 관찰",
    "low_near": "저점 근접 — 분할 접근 고려",
    "mid": "중립 — 뚜렷한 신호 없음",
    "high_near": "고점 근접 — 차익/주의",
    "high": "고점권 — 리스크 관리",
}


def combine_opinion(cycle, buy_sig):
    """시간축별 TA 판정 + 온체인 매수신호를 결합한 '총 매매 의견'.

    반환: {"horizons": [{name, ta_label, ta_color, opinion, ...}], "headline": str}
    """
    if not cycle or cycle.get("error"):
        return None

    v_tier = (buy_sig or {}).get("value_tier")     # cheap/fair/rich
    t_tier = (buy_sig or {}).get("timing_tier")     # good/neutral/bad
    v_score = (buy_sig or {}).get("value_score")
    t_score = (buy_sig or {}).get("timing_score")

    horizons = []
    for name, tf, _desc in HORIZONS:
        d = cycle.get(name)
        if not d:
            continue
        lv = d["level"]
        ta_stance = _STANCE.get(lv, "")
        opinion = ta_stance

        if name == "장기":
            # 월봉 TA + 온체인 밸류에이션 결합
            if lv in ("low", "low_near") and v_tier == "cheap":
                opinion = "🟢 장기 저점권 — 온체인도 저평가. 현물 분할매수 적극 고려"
            elif lv in ("high", "high_near") and v_tier == "rich":
                opinion = "🔴 장기 고점권 — 온체인도 고평가. 차익실현·리스크 관리"
            elif lv in ("low", "low_near") and v_tier in ("fair", "rich"):
                opinion = "🟡 기술적 저점권이나 온체인 밸류에이션은 아직 싸지 않음 — 신중 접근"
            elif lv in ("high", "high_near") and v_tier == "cheap":
                opinion = "🟡 단기 과열이나 온체인은 저평가 — 눌림 시 매수 관점 유지"
            else:
                opinion = ta_stance + (" · 온체인 저평가" if v_tier == "cheap"
                                       else " · 온체인 고평가" if v_tier == "rich" else "")
        elif name == "단기":
            # 일봉 TA + 온체인 단기 타이밍 결합
            if lv in ("low", "low_near") and t_tier == "bad":
                opinion = "🟠 단기 급락 과매도 — 반등 시도 가능하나 진정 확인 후 분할"
            elif lv in ("low", "low_near"):
                opinion = "🟢 단기 저점권 — 반등 관찰"
            elif lv in ("high", "high_near") and t_tier == "good":
                opinion = "🟠 단기 과열 — 추격 매수 자제"
            else:
                opinion = ta_stance
        # 스윙은 TA 단독 스탠스 사용

        horizons.append({
            "name": name,
            "tf": tf,
            "rsi": d["rsi"],
            "ta_label": d["label"],
            "ta_color": d["color"],
            "regime_kr": d["regime_kr"],
            "cycle_pos": d["cycle_pos"],
            "note": d["note"],
            "opinion": opinion,
        })

    # 헤드라인: 장기 의견 중심으로 한 줄
    head = next((h for h in horizons if h["name"] == "장기"), None)
    headline = head["opinion"] if head else "데이터 부족"

    return {"horizons": horizons, "headline": headline,
            "value_score": v_score, "timing_score": t_score}
