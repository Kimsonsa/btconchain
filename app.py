#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — 비트코인 온체인 데이터 Streamlit 대시보드 (라이트 모드)
"""

import streamlit as st
from btc_onchain import (
    collect,
    interpret_mvrv,
    interpret_nupl,
    interpret_puell,
    fmt_usd,
    fmt_num,
    fmt_pct,
)

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="₿ 비트코인 온체인 대시보드",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 커스텀 CSS — 화이트 모드
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* 전체 배경 */
.stApp {
    background: linear-gradient(135deg, #fafbfc 0%, #f0f2f5 50%, #fafbfc 100%);
    font-family: 'Inter', sans-serif;
}

/* 헤더 */
header[data-testid="stHeader"] {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(10px);
}

/* 메인 타이틀 */
.main-title {
    text-align: center;
    padding: 1.5rem 0 0.3rem 0;
    background: linear-gradient(135deg, #e8850f, #f7931a, #d4760e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: -1px;
}

.sub-title {
    text-align: center;
    color: #656d76;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
    font-weight: 400;
}

/* 메트릭 카드 */
.metric-card {
    background: #ffffff;
    border: 1px solid #d1d9e0;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
}
.metric-card:hover {
    border-color: #f7931a;
    box-shadow: 0 4px 12px rgba(247, 147, 26, 0.12);
    transform: translateY(-2px);
}

.metric-label {
    color: #656d76;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.4rem;
}

.metric-sublabel {
    color: #8b949e;
    font-size: 0.72rem;
    font-weight: 400;
    margin-bottom: 0.3rem;
    line-height: 1.3;
}

.metric-value {
    color: #1f2328;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.2;
}

.metric-value-sm {
    color: #1f2328;
    font-size: 1.2rem;
    font-weight: 600;
}

.metric-delta-pos { color: #1a7f37; font-size: 0.85rem; font-weight: 600; }
.metric-delta-neg { color: #cf222e; font-size: 0.85rem; font-weight: 600; }
.metric-delta-neutral { color: #656d76; font-size: 0.85rem; }

/* 섹션 헤더 */
.section-header {
    color: #1f2328;
    font-size: 1.2rem;
    font-weight: 700;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f7931a;
    letter-spacing: -0.3px;
}

/* 종합 신호 게이지 */
.gauge-container {
    background: #ffffff;
    border: 1px solid #d1d9e0;
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.gauge-score {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.gauge-label {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.gauge-bar-bg {
    background: #e8ecef;
    border-radius: 10px;
    height: 14px;
    width: 100%;
    margin: 1rem auto;
    max-width: 500px;
    overflow: hidden;
}

.gauge-bar-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 1s ease;
}

/* 공포탐욕 배지 */
.fear-greed-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}

/* 수수료 그리드 */
.fee-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
}

.fee-item {
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 12px;
    padding: 0.8rem;
    text-align: center;
}

.fee-label { color: #656d76; font-size: 0.75rem; margin-bottom: 0.3rem; }
.fee-value { color: #1f2328; font-size: 1.1rem; font-weight: 700; }

/* 인터프리터 배지 */
.interp-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 500;
    background: #f6f8fa;
    color: #656d76;
    margin-top: 0.3rem;
    border: 1px solid #e1e4e8;
}

/* 에러 박스 */
.error-box {
    background: #fff5f5;
    border: 1px solid #fcc;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #cf222e;
    font-size: 0.85rem;
    margin-top: 1rem;
}

/* 면책 */
.disclaimer {
    text-align: center;
    color: #8b949e;
    font-size: 0.75rem;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #e1e4e8;
}

/* 버튼 */
.stButton > button {
    background: linear-gradient(135deg, #f7931a, #e8850f) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 15px rgba(247, 147, 26, 0.35) !important;
    transform: translateY(-1px) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────────────────────────────────
def delta_class(val):
    if val is None:
        return "metric-delta-neutral"
    return "metric-delta-pos" if val >= 0 else "metric-delta-neg"


def delta_arrow(val):
    if val is None:
        return ""
    return "▲" if val >= 0 else "▼"


def gauge_color(score):
    if score is None:
        return "#8b949e"
    if score < 25:
        return "#0969da"
    if score < 45:
        return "#1a7f37"
    if score < 60:
        return "#9a6700"
    if score < 75:
        return "#bc4c00"
    return "#cf222e"


def fg_color(val):
    if val is None:
        return "#656d76", "#f6f8fa"
    if val <= 25:
        return "#cf222e", "#fff5f5"
    if val <= 45:
        return "#bc4c00", "#fff8f0"
    if val <= 55:
        return "#9a6700", "#fff8e1"
    if val <= 75:
        return "#1a7f37", "#f0fff4"
    return "#1a7f37", "#dafbe1"


# ─────────────────────────────────────────────────────────────────────────────
# 데이터 수집
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_data():
    return collect()


# ─────────────────────────────────────────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">₿ 비트코인 온체인 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">무료 공개 API 기반 · 실시간 온체인 데이터 수집</div>', unsafe_allow_html=True)

# 새로고침 버튼
col_r1, col_r2, col_r3 = st.columns([4, 1, 4])
with col_r2:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("📡 데이터 수집 중... (6개 소스에서 가져오는 중)"):
    report = load_data()

pm = report.get("price_market", {})
nw = report.get("network", {})
va = report.get("valuation", {})
se = report.get("sentiment", {})
ad = report.get("advanced", {})
comp = report.get("composite", {})

# 타임스탬프
st.markdown(f'<div class="sub-title">📅 {report.get("timestamp_kst", "")}</div>', unsafe_allow_html=True)

# ═══════ [종합 신호] 상단 게이지 ═════════════════════════════════════════════
score = comp.get("score_0_100")
label = comp.get("label", "-")
gc = gauge_color(score)

st.markdown(f"""
<div class="gauge-container">
    <div style="color:#656d76; font-size:0.85rem; font-weight:600; margin-bottom:0.5rem;">
        📊 종합 시장 온도 (여러 지표를 종합한 과열/과매도 점수)
    </div>
    <div class="gauge-score" style="color: {gc};">{score if score is not None else '-'}</div>
    <div class="gauge-label" style="color: {gc};">{label}</div>
    <div class="gauge-bar-bg">
        <div class="gauge-bar-fill" style="width: {score or 0}%;
             background: linear-gradient(90deg, #0969da, #1a7f37, #9a6700, #bc4c00, #cf222e);"></div>
    </div>
    <div style="color: #8b949e; font-size: 0.8rem; margin-top: 0.5rem;">
        ❄️ 과매도 (싸다) ← 0 ─────── 50 ─────── 100 → 🔥 과열 (비싸다)
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════ [1] 가격 & 시장 ═════════════════════════════════════════════════════
st.markdown('<div class="section-header">💰 가격 & 시장 현황</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    price = pm.get("price_usd")
    chg24 = pm.get("change_24h_pct")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">현재 비트코인 가격</div>
        <div class="metric-value">{fmt_usd(price)}</div>
        <div class="{delta_class(chg24)}">{delta_arrow(chg24)} {fmt_pct(chg24)} (최근 24시간)</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">시가총액</div>
        <div class="metric-sublabel">전체 비트코인의 총 가치</div>
        <div class="metric-value">{fmt_usd(pm.get('market_cap_usd'))}</div>
        <div class="metric-delta-neutral">24시간 거래량 {fmt_usd(pm.get('volume_24h_usd'))}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">역대 최고가</div>
        <div class="metric-sublabel">비트코인이 기록한 최고 가격</div>
        <div class="metric-value">{fmt_usd(pm.get('ath_usd'))}</div>
        <div class="{delta_class(pm.get('ath_change_pct'))}">최고가 대비 {fmt_pct(pm.get('ath_change_pct'))}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    dom = pm.get('btc_dominance_pct')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">비트코인 점유율</div>
        <div class="metric-sublabel">전체 암호화폐 시장에서 비트코인이 차지하는 비중</div>
        <div class="metric-value">{"%.1f%%" % dom if dom else "-"}</div>
        <div class="metric-delta-neutral">유통량 {fmt_num(pm.get('circulating_supply'))} BTC</div>
    </div>
    """, unsafe_allow_html=True)

# 변동률 행
cc1, cc2, cc3, cc4 = st.columns(4)
with cc1:
    chg7 = pm.get("change_7d_pct")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">7일 가격 변동</div>
        <div class="metric-value-sm {delta_class(chg7)}">{delta_arrow(chg7)} {fmt_pct(chg7)}</div>
    </div>
    """, unsafe_allow_html=True)
with cc2:
    chg30 = pm.get("change_30d_pct")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">30일 가격 변동</div>
        <div class="metric-value-sm {delta_class(chg30)}">{delta_arrow(chg30)} {fmt_pct(chg30)}</div>
    </div>
    """, unsafe_allow_html=True)
with cc3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">24시간 최고가</div>
        <div class="metric-value-sm">{fmt_usd(pm.get('high_24h'))}</div>
    </div>
    """, unsafe_allow_html=True)
with cc4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">24시간 최저가</div>
        <div class="metric-value-sm">{fmt_usd(pm.get('low_24h'))}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [2] 네트워크 & 채굴 ═════════════════════════════════════════════════
st.markdown('<div class="section-header">⛏️ 네트워크 & 채굴 현황</div>', unsafe_allow_html=True)

n1, n2, n3, n4 = st.columns(4)
with n1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">블록 높이</div>
        <div class="metric-sublabel">지금까지 생성된 블록 수</div>
        <div class="metric-value-sm">{fmt_num(nw.get('block_height'))}</div>
    </div>
    """, unsafe_allow_html=True)
with n2:
    hr = nw.get('hashrate_ehs')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">해시레이트</div>
        <div class="metric-sublabel">채굴에 투입된 전체 연산 능력 (높을수록 네트워크가 안전)</div>
        <div class="metric-value-sm">{"%.1f EH/s" % hr if hr else "-"}</div>
    </div>
    """, unsafe_allow_html=True)
with n3:
    diff = nw.get('difficulty')
    diff_str = "%.2fT" % (diff / 1e12) if diff else "-"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">채굴 난이도</div>
        <div class="metric-sublabel">블록을 채굴하기 위한 난이도 수치</div>
        <div class="metric-value-sm">{diff_str}</div>
    </div>
    """, unsafe_allow_html=True)
with n4:
    dp = nw.get('diff_progress_pct')
    dc = nw.get('diff_change_pct')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">다음 난이도 조정</div>
        <div class="metric-sublabel">약 2주마다 자동으로 난이도가 조정됨</div>
        <div class="metric-value-sm">{"%.1f%%" % dp if dp is not None else "-"} 진행</div>
        <div class="{delta_class(dc)}">예상 변화 {fmt_pct(dc)} | {nw.get('diff_remaining_blocks','-')}블록 남음</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [3] 멤풀 & 수수료 ═══════════════════════════════════════════════════
st.markdown('<div class="section-header">📦 대기 중인 거래 & 수수료</div>', unsafe_allow_html=True)

f1, f2 = st.columns([3, 2])
with f1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">추천 거래 수수료</div>
        <div class="metric-sublabel">비트코인 전송 시 블록에 포함되기 위해 필요한 수수료 (단위: 사토시/가상바이트)</div>
        <div class="fee-grid">
            <div class="fee-item">
                <div class="fee-label">⚡ 즉시 (10분)</div>
                <div class="fee-value">{nw.get('fee_fastest', '-')}</div>
            </div>
            <div class="fee-item">
                <div class="fee-label">🕐 30분 이내</div>
                <div class="fee-value">{nw.get('fee_half_hour', '-')}</div>
            </div>
            <div class="fee-item">
                <div class="fee-label">🕑 1시간 이내</div>
                <div class="fee-value">{nw.get('fee_hour', '-')}</div>
            </div>
            <div class="fee-item">
                <div class="fee-label">🐢 느려도 OK</div>
                <div class="fee-value">{nw.get('fee_economy', '-')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with f2:
    mp_count = nw.get('mempool_tx_count')
    mp_fee = nw.get('mempool_total_fee_btc') or 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">멤풀 (대기열) 상태</div>
        <div class="metric-sublabel">아직 블록에 포함되지 않고 대기 중인 거래들</div>
        <div class="metric-value-sm">{fmt_num(mp_count)} 건 대기 중</div>
        <div class="metric-delta-neutral">대기 중인 총 수수료 {mp_fee:.3f} BTC</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [4] 온체인 활동 ═════════════════════════════════════════════════════
ac = report.get("activity", {})
st.markdown('<div class="section-header">🔗 블록체인 위의 실제 활동</div>', unsafe_allow_html=True)

a1, a2, a3, a4 = st.columns(4)
with a1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">활성 주소 수</div>
        <div class="metric-sublabel">최근 24시간 동안 거래에 참여한 고유 지갑 수</div>
        <div class="metric-value-sm">{fmt_num(va.get('active_addresses'))}</div>
    </div>
    """, unsafe_allow_html=True)
with a2:
    tx = va.get('tx_count') or ac.get('n_tx_24h')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">거래 건수 (24시간)</div>
        <div class="metric-sublabel">하루 동안 블록체인에 기록된 거래 수</div>
        <div class="metric-value-sm">{fmt_num(tx)}</div>
    </div>
    """, unsafe_allow_html=True)
with a3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">추정 거래 금액</div>
        <div class="metric-sublabel">24시간 동안 이동한 비트코인의 달러 환산 가치</div>
        <div class="metric-value-sm">{fmt_usd(ac.get('tx_volume_usd_est'))}</div>
    </div>
    """, unsafe_allow_html=True)
with a4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">채굴자 수익 (24시간)</div>
        <div class="metric-sublabel">채굴 보상 + 수수료로 채굴자가 벌어들인 금액</div>
        <div class="metric-value-sm">{fmt_usd(ac.get('miners_revenue_usd'))}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [5] 밸류에이션 (가치 평가) ══════════════════════════════════════════
cm_date = va.get("cm_date", "-")
st.markdown(f'<div class="section-header">📐 가치 평가 지표 <span style="color:#8b949e;font-size:0.8rem;font-weight:400;">기준일: {cm_date}</span></div>', unsafe_allow_html=True)

v1, v2, v3, v4, v5 = st.columns(5)

mvrv = va.get("mvrv")
nupl = va.get("nupl")

with v1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">시장가/실현가 비율</div>
        <div class="metric-sublabel">현재 시장가치 ÷ 모든 코인의 평균 매입가 기반 가치. 1 미만이면 전체적으로 손실, 높으면 과열</div>
        <div class="metric-value-sm">{"%.2f" % mvrv if mvrv else "-"}</div>
        <div class="interp-badge">{interpret_mvrv(mvrv) or "데이터 없음"}</div>
    </div>
    """, unsafe_allow_html=True)
with v2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">순미실현 손익</div>
        <div class="metric-sublabel">아직 팔지 않은 코인들의 전체 손익 상태. 0 미만이면 시장 전반이 손실 중</div>
        <div class="metric-value-sm">{"%.3f" % nupl if nupl is not None else "-"}</div>
        <div class="interp-badge">{interpret_nupl(nupl) or "데이터 없음"}</div>
    </div>
    """, unsafe_allow_html=True)
with v3:
    rp = va.get('realized_price_usd')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">평균 매입 가격</div>
        <div class="metric-sublabel">모든 비트코인이 마지막으로 이동한 시점의 평균 가격 (시장의 평균 원가)</div>
        <div class="metric-value-sm">{fmt_usd(rp)}</div>
    </div>
    """, unsafe_allow_html=True)
with v4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">실현 시가총액</div>
        <div class="metric-sublabel">각 코인을 마지막 이동 시점 가격으로 계산한 총 가치</div>
        <div class="metric-value-sm">{fmt_usd(va.get('realized_cap_usd'))}</div>
    </div>
    """, unsafe_allow_html=True)
with v5:
    nvt = va.get('nvt')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">네트워크 가치/거래량</div>
        <div class="metric-sublabel">시가총액 ÷ 일일 거래량. 주식의 PER처럼 네트워크 가치를 평가</div>
        <div class="metric-value-sm">{"%.1f" % nvt if nvt else "-"}</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [6] 시장 심리 ═══════════════════════════════════════════════════════
st.markdown('<div class="section-header">🧠 시장 심리 (투자자들의 감정 상태)</div>', unsafe_allow_html=True)

fg_val = se.get("value")
fg_cls = se.get("classification", "-")
fg_yes = se.get("value_yesterday")
fg_c, fg_bg = fg_color(fg_val)

# 한글 분류
fg_kr = {
    "Extreme Fear": "극심한 공포",
    "Fear": "공포",
    "Neutral": "중립",
    "Greed": "탐욕",
    "Extreme Greed": "극심한 탐욕",
}.get(fg_cls, fg_cls)

s1, s2 = st.columns([1, 1])
with s1:
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="metric-label">공포·탐욕 지수 (오늘)</div>
        <div class="metric-sublabel">0 = 극심한 공포 (사람들이 두려워함) / 100 = 극심한 탐욕 (사람들이 욕심을 부림)</div>
        <div class="metric-value" style="font-size:3rem; color:{fg_c};">{fg_val if fg_val is not None else "-"}</div>
        <div class="fear-greed-badge" style="color:{fg_c}; background:{fg_bg};">{fg_kr}</div>
    </div>
    """, unsafe_allow_html=True)
with s2:
    fg_c2, fg_bg2 = fg_color(fg_yes)
    diff_val = ""
    if fg_val is not None and fg_yes is not None:
        d = fg_val - fg_yes
        diff_val = f"↑ {abs(d)}" if d > 0 else f"↓ {abs(d)}" if d < 0 else "→ 변동 없음"
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="metric-label">공포·탐욕 지수 (어제)</div>
        <div class="metric-sublabel">어제와 비교하여 심리 변화를 확인할 수 있습니다</div>
        <div class="metric-value" style="font-size:3rem; color:{fg_c2};">{fg_yes if fg_yes is not None else "-"}</div>
        <div class="metric-delta-neutral">{diff_val or "-"} 변동</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════ [7] 고급 지표 ═══════════════════════════════════════════════════════
if ad:
    st.markdown('<div class="section-header">🔬 고급 온체인 지표 <span style="color:#8b949e;font-size:0.8rem;font-weight:400;">bitcoin-data.com</span></div>', unsafe_allow_html=True)

    adv_cols = st.columns(4)
    adv_items = [
        (
            "코인 손익 실현 비율",
            "이동된 코인이 이익/손실 중 어떤 상태였는지 보여줌. 1 미만이면 손실 상태에서 코인이 이동됨 (투매 가능성)",
            ad.get("sopr"), "%.3f",
            "1 미만 = 손실 실현 / 1 초과 = 이익 실현"
        ),
        (
            "채굴자 수익 배수",
            "채굴자의 일일 수익이 연평균 대비 얼마나 높은지 보여줌. 낮으면 채굴자가 힘든 시기 (매수 기회 가능성)",
            ad.get("puell_multiple"), "%.3f",
            interpret_puell(ad.get("puell_multiple")) or ""
        ),
        (
            "시장가/실현가 Z점수",
            "현재 가격이 역사적 평균에서 얼마나 벗어났는지 표준편차로 측정. 높을수록 고점 경계",
            ad.get("mvrv_zscore"), "%.2f",
            ""
        ),
        (
            "리저브 리스크",
            "장기 보유자의 확신 대비 현재 가격 수준. 낮으면 장기 보유자 확신 높음 → 매수 매력",
            ad.get("reserve_risk"), "%.6f",
            ""
        ),
    ]

    for i, (name, desc, val, fmt, interp) in enumerate(adv_items):
        if val is not None:
            with adv_cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{name}</div>
                    <div class="metric-sublabel">{desc}</div>
                    <div class="metric-value-sm">{fmt % val}</div>
                    {"<div class='interp-badge'>%s</div>" % interp if interp else ""}
                </div>
                """, unsafe_allow_html=True)

# ═══════ 에러 ═════════════════════════════════════════════════════════════════
errors = report.get("errors", {})
if errors:
    err_items = " | ".join([f"{k}: {v}" for k, v in errors.items()])
    st.markdown(f"""
    <div class="error-box">
        ⚠️ 일부 데이터 소스에서 수집 실패: {err_items}
    </div>
    """, unsafe_allow_html=True)

# ═══════ Raw JSON ═════════════════════════════════════════════════════════════
with st.expander("📋 원본 JSON 데이터 보기 (개발자용)"):
    st.json(report)

# ═══════ 면책 ═════════════════════════════════════════════════════════════════
st.markdown("""
<div class="disclaimer">
    ※ 본 대시보드의 '신호/해석'은 통계적 참고용이며 투자 자문이 아닙니다.<br>
    데이터 출처: CoinGecko · mempool.space · alternative.me · Coin Metrics · blockchain.info · bitcoin-data.com
</div>
""", unsafe_allow_html=True)
