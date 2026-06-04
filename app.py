#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — 비트코인 온체인 데이터 Streamlit 대시보드 (라이트 모드)
"""

import streamlit as st
from btc_onchain import (
    collect,
    fetch_cex_reserves,
    fetch_premium_indicators,
    fetch_long_short_ratio,
    fetch_lightning_network,
    fetch_stablecoin_mcap,
    fetch_defi_tvl,
    fetch_derivatives,
    fetch_trending_coins,
    fetch_top_coins,
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

/* ── 거래소 보유량 테이블 ── */
.cex-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 12px;
    overflow: hidden;
    background: #ffffff;
    border: 1px solid #d1d9e0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cex-table th {
    background: #f6f8fa;
    color: #656d76;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 0.75rem 1rem;
    text-align: right;
    border-bottom: 2px solid #d1d9e0;
}
.cex-table th:first-child { text-align: left; }
.cex-table td {
    padding: 0.65rem 1rem;
    font-size: 0.88rem;
    color: #1f2328;
    border-bottom: 1px solid #e8ecef;
    text-align: right;
    font-variant-numeric: tabular-nums;
}
.cex-table td:first-child {
    text-align: left;
    font-weight: 600;
}
.cex-table tr:last-child td { border-bottom: none; }
.cex-table tr:hover td {
    background: #fff8f0;
}
.cex-table .cex-total-row td {
    background: #f6f8fa;
    font-weight: 700;
    border-top: 2px solid #d1d9e0;
    color: #1f2328;
}
.cex-table .cex-total-row:hover td {
    background: #f0f2f5;
}

/* 거래소 보유량 바 */
.cex-bar-outer {
    background: #e8ecef;
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.cex-bar-inner {
    height: 100%;
    border-radius: 6px;
    transition: width 0.8s ease;
}

/* 보유량 요약 카드 */
.cex-summary-card {
    background: #ffffff;
    border: 1px solid #d1d9e0;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: all 0.3s ease;
}
.cex-summary-card:hover {
    border-color: #f7931a;
    box-shadow: 0 4px 12px rgba(247, 147, 26, 0.12);
    transform: translateY(-2px);
}
.cex-chain-icon {
    font-size: 1.8rem;
    margin-bottom: 0.3rem;
}
.cex-chain-name {
    color: #656d76;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.cex-chain-value {
    color: #1f2328;
    font-size: 1.3rem;
    font-weight: 700;
    margin-top: 0.2rem;
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


@st.cache_data(ttl=600)
def load_cex_reserves():
    import time
    return fetch_cex_reserves(), time.time()


def cex_delta_html(cur, prev, threshold=50000):
    """증감 화살표 HTML 생성. threshold 이하의 변화는 무시."""
    if prev is None or cur is None:
        return ""
    diff = cur - prev
    if abs(diff) < threshold:
        return ""
    arrow = "▲" if diff > 0 else "▼"
    color = "#cf222e" if diff > 0 else "#1a7f37"  # 증가=빨강(매도압력), 감소=초록(축적)
    return f'<span style="color:{color};font-size:0.68rem;font-weight:600;"> {arrow}{fmt_usd(abs(diff))}</span>'


@st.cache_data(ttl=120)
def load_premiums():
    return fetch_premium_indicators()

@st.cache_data(ttl=120)
def load_long_short():
    return fetch_long_short_ratio()

@st.cache_data(ttl=600)
def load_lightning():
    return fetch_lightning_network()

@st.cache_data(ttl=600)
def load_stablecoins():
    return fetch_stablecoin_mcap()

@st.cache_data(ttl=600)
def load_defi_tvl():
    return fetch_defi_tvl()

@st.cache_data(ttl=600)
def load_derivatives():
    return fetch_derivatives()

@st.cache_data(ttl=600)
def load_trending():
    return fetch_trending_coins()

@st.cache_data(ttl=600)
def load_top_coins():
    return fetch_top_coins()

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

try:
    with st.spinner("📡 데이터 수집 중... (6개 소스에서 가져오는 중)"):
        report = load_data()
except Exception as e:
    st.error(f"⚠️ 데이터 수집 중 오류가 발생했습니다: {e}")
    st.info("잠시 후 새로고침을 시도해 주세요.")
    report = {
        "timestamp_kst": "데이터 없음",
        "price_market": {},
        "network": {},
        "valuation": {},
        "sentiment": {},
        "advanced": {},
        "composite": {},
        "errors": {"init": str(e)},
    }

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

mvrv = va.get("mvrv")
nupl = va.get("nupl")
has_valuation = mvrv is not None or nupl is not None or va.get("realized_price_usd") is not None

if has_valuation:
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        interp_m = interpret_mvrv(mvrv)
        badge_m = f'<div class="interp-badge">{interp_m}</div>' if interp_m else ""
        st.markdown(f'<div class="metric-card"><div class="metric-label">시장가/실현가 비율</div><div class="metric-sublabel">현재 시장가치 ÷ 모든 코인의 평균 매입가 기반 가치. 1 미만이면 전체적으로 손실, 높으면 과열</div><div class="metric-value-sm">{"%.2f" % mvrv if mvrv else "-"}</div>{badge_m}</div>', unsafe_allow_html=True)
    with v2:
        interp_n = interpret_nupl(nupl)
        badge_n = f'<div class="interp-badge">{interp_n}</div>' if interp_n else ""
        st.markdown(f'<div class="metric-card"><div class="metric-label">순미실현 손익</div><div class="metric-sublabel">아직 팔지 않은 코인들의 전체 손익 상태. 0 미만이면 시장 전반이 손실 중</div><div class="metric-value-sm">{"%.3f" % nupl if nupl is not None else "-"}</div>{badge_n}</div>', unsafe_allow_html=True)
    with v3:
        rp = va.get('realized_price_usd')
        st.markdown(f'<div class="metric-card"><div class="metric-label">평균 매입 가격</div><div class="metric-sublabel">모든 비트코인이 마지막으로 이동한 시점의 평균 가격 (시장의 평균 원가)</div><div class="metric-value-sm">{fmt_usd(rp)}</div></div>', unsafe_allow_html=True)
    with v4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">실현 시가총액</div><div class="metric-sublabel">각 코인을 마지막 이동 시점 가격으로 계산한 총 가치</div><div class="metric-value-sm">{fmt_usd(va.get("realized_cap_usd"))}</div></div>', unsafe_allow_html=True)
    with v5:
        nvt = va.get('nvt')
        st.markdown(f'<div class="metric-card"><div class="metric-label">네트워크 가치/거래량</div><div class="metric-sublabel">시가총액 ÷ 일일 거래량. 주식의 PER처럼 네트워크 가치를 평가</div><div class="metric-value-sm">{"%.1f" % nvt if nvt else "-"}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div style="background:#fff8e1;border:1px solid #f0d060;border-radius:12px;'
        'padding:1.2rem 1.5rem;color:#6d5c00;font-size:0.88rem;line-height:1.7;">'
        '📊 <b>가치 평가 데이터를 현재 가져올 수 없습니다</b><br>'
        'Coin Metrics 무료 API가 일시적으로 응답하지 않고 있습니다 (403 오류).<br>'
        '이 지표들(MVRV, NUPL, 실현가격 등)은 API가 복구되면 자동으로 표시됩니다.<br>'
        '<span style="color:#8b7500;font-size:0.78rem;">'
        '💡 참고: 아래 "고급 온체인 지표" 섹션의 MVRV Z-Score는 별도 소스에서 제공되어 확인 가능할 수 있습니다.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

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

# ═══════ [8] 거래소 보유량 (CEX Reserves) ═════════════════════════════════════
st.markdown('<div class="section-header">🏦 거래소 보유량 (CEX Reserves) <span style="color:#8b949e;font-size:0.8rem;font-weight:400;">DeFiLlama · 10분 주기 자동 갱신</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 거래소에 보관된 암호화폐의 달러 환산 총액입니다. '
    '거래소 보유량이 <b style="color:#cf222e;">▲ 증가</b>하면 매도 대기 물량이 늘어나는 것이고, '
    '<b style="color:#1a7f37;">▼ 감소</b>하면 투자자들이 코인을 인출(장기 보유 의향)하고 있다는 신호입니다.'
    '</div>',
    unsafe_allow_html=True,
)

with st.spinner("🏦 거래소 보유량 수집 중... (10개 거래소 조회)"):
    cex_data, cex_fetch_time = load_cex_reserves()

# ── 이전 데이터와 비교하여 증감 계산 ──
prev_cex = None
if "cex_fetch_time" not in st.session_state:
    st.session_state.cex_fetch_time = cex_fetch_time
    st.session_state.cex_prev_data = None
elif cex_fetch_time != st.session_state.cex_fetch_time:
    # 캐시가 갱신됨 → 이전 데이터 저장
    st.session_state.cex_prev_data = st.session_state.get("cex_current_data")
    st.session_state.cex_fetch_time = cex_fetch_time

st.session_state.cex_current_data = cex_data
prev_cex = st.session_state.get("cex_prev_data")

# 이전 거래소 맵 생성
prev_ex_map = {}
prev_totals = {}
prev_grand = None
if prev_cex and prev_cex.get("exchanges"):
    prev_ex_map = {e["slug"]: e for e in prev_cex["exchanges"]}
    prev_totals = prev_cex.get("totals", {})
    prev_grand = prev_cex.get("grand_total_usd")

if cex_data and cex_data.get("exchanges"):
    cex_exchanges = cex_data["exchanges"]
    cex_totals = cex_data["totals"]
    grand_total = cex_data["grand_total_usd"]

    # ── 요약 카드 ──
    gt_delta = cex_delta_html(grand_total, prev_grand, threshold=100000)
    btc_total = cex_totals.get("BTC", 0)
    btc_pct = (btc_total / grand_total * 100) if grand_total else 0
    btc_delta = cex_delta_html(btc_total, prev_totals.get("BTC"), threshold=100000)
    eth_total = cex_totals.get("ETH", 0)
    eth_pct = (eth_total / grand_total * 100) if grand_total else 0
    eth_delta = cex_delta_html(eth_total, prev_totals.get("ETH"), threshold=100000)
    sol_total = cex_totals.get("SOL", 0)
    sol_pct = (sol_total / grand_total * 100) if grand_total else 0
    sol_delta = cex_delta_html(sol_total, prev_totals.get("SOL"), threshold=50000)

    has_delta = bool(prev_grand is not None)
    delta_hint = '<div style="color:#8b949e;font-size:0.65rem;margin-top:0.2rem;">이전 대비 변화</div>' if has_delta and gt_delta else ''

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f'<div class="cex-summary-card"><div class="cex-chain-icon">🏦</div><div class="cex-chain-name">전체 거래소 합산</div><div class="cex-chain-value">{fmt_usd(grand_total)}</div><div style="margin-top:0.2rem;">{gt_delta}</div><div style="color:#8b949e;font-size:0.72rem;margin-top:0.2rem;">{cex_data["exchange_count"]}개 거래소 · 10분 갱신</div></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div class="cex-summary-card"><div class="cex-chain-icon">₿</div><div class="cex-chain-name">BTC 보유량</div><div class="cex-chain-value">{fmt_usd(btc_total)}</div><div style="margin-top:0.2rem;">{btc_delta}</div><div style="color:#8b949e;font-size:0.72rem;margin-top:0.2rem;">전체의 {btc_pct:.1f}%</div></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="cex-summary-card"><div class="cex-chain-icon">⟠</div><div class="cex-chain-name">ETH 보유량</div><div class="cex-chain-value">{fmt_usd(eth_total)}</div><div style="margin-top:0.2rem;">{eth_delta}</div><div style="color:#8b949e;font-size:0.72rem;margin-top:0.2rem;">전체의 {eth_pct:.1f}%</div></div>', unsafe_allow_html=True)
    with sc4:
        st.markdown(f'<div class="cex-summary-card"><div class="cex-chain-icon">◎</div><div class="cex-chain-name">SOL 보유량</div><div class="cex-chain-value">{fmt_usd(sol_total)}</div><div style="margin-top:0.2rem;">{sol_delta}</div><div style="color:#8b949e;font-size:0.72rem;margin-top:0.2rem;">전체의 {sol_pct:.1f}%</div></div>', unsafe_allow_html=True)

    # ── 거래소별 상세 테이블 ──
    max_total = max(e["total_usd"] for e in cex_exchanges) if cex_exchanges else 1
    table_rows = []
    sorted_exchanges = sorted(cex_exchanges, key=lambda x: x["total_usd"], reverse=True)
    bar_colors = [
        "#f7931a", "#627eea", "#00d4aa", "#e84142",
        "#7b3fe4", "#26a17b", "#f0b90b", "#1da1f2",
        "#00adef", "#ff6b35"
    ]

    for idx, ex in enumerate(sorted_exchanges):
        pct = (ex["total_usd"] / grand_total * 100) if grand_total else 0
        bar_width = (ex["total_usd"] / max_total * 100) if max_total else 0
        bar_color = bar_colors[idx % len(bar_colors)]

        btc_v = ex["chains"].get("BTC", 0)
        eth_v = ex["chains"].get("ETH", 0)
        sol_v = ex["chains"].get("SOL", 0)
        total_v = ex["total_usd"]

        # 이전 대비 증감
        prev_ex = prev_ex_map.get(ex["slug"])
        d_btc = cex_delta_html(btc_v, prev_ex["chains"].get("BTC", 0)) if prev_ex else ""
        d_eth = cex_delta_html(eth_v, prev_ex["chains"].get("ETH", 0)) if prev_ex else ""
        d_sol = cex_delta_html(sol_v, prev_ex["chains"].get("SOL", 0), threshold=10000) if prev_ex else ""
        d_total = cex_delta_html(total_v, prev_ex["total_usd"]) if prev_ex else ""

        table_rows.append(
            f'<tr><td>{ex["icon"]} {ex["name"]}</td>'
            f'<td>{fmt_usd(btc_v) if btc_v else "-"}{d_btc}</td>'
            f'<td>{fmt_usd(eth_v) if eth_v else "-"}{d_eth}</td>'
            f'<td>{fmt_usd(sol_v) if sol_v else "-"}{d_sol}</td>'
            f'<td>{fmt_usd(total_v)}{d_total}</td>'
            f'<td><div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;">'
            f'<span style="font-size:0.75rem;color:#656d76;min-width:36px;text-align:right;">{pct:.1f}%</span>'
            f'<div class="cex-bar-outer" style="width:70px;">'
            f'<div class="cex-bar-inner" style="width:{bar_width:.1f}%;background:{bar_color};"></div>'
            f'</div></div></td></tr>'
        )

    # 합계 행 + 증감
    d_bt = cex_delta_html(cex_totals.get("BTC",0), prev_totals.get("BTC"), threshold=100000) if prev_grand else ""
    d_et = cex_delta_html(cex_totals.get("ETH",0), prev_totals.get("ETH"), threshold=100000) if prev_grand else ""
    d_st = cex_delta_html(cex_totals.get("SOL",0), prev_totals.get("SOL"), threshold=50000) if prev_grand else ""
    d_gt = cex_delta_html(grand_total, prev_grand, threshold=100000) if prev_grand else ""
    total_row = (
        f'<tr class="cex-total-row"><td>합계 ({cex_data["exchange_count"]}개)</td>'
        f'<td>{fmt_usd(cex_totals.get("BTC", 0))}{d_bt}</td>'
        f'<td>{fmt_usd(cex_totals.get("ETH", 0))}{d_et}</td>'
        f'<td>{fmt_usd(cex_totals.get("SOL", 0))}{d_st}</td>'
        f'<td>{fmt_usd(grand_total)}{d_gt}</td>'
        f'<td style="text-align:right;font-size:0.75rem;color:#656d76;">100%</td></tr>'
    )

    full_table = (
        '<table class="cex-table"><thead><tr>'
        '<th>거래소</th><th>BTC 보유량</th><th>ETH 보유량</th>'
        '<th>SOL 보유량</th><th>총 보유량</th><th style="width:120px;">비중</th>'
        '</tr></thead><tbody>'
        + "".join(table_rows)
        + total_row
        + '</tbody></table>'
    )
    st.markdown(full_table, unsafe_allow_html=True)

    # ── 해석 도움말 ──
    delta_status = ''
    if prev_grand is not None:
        import datetime
        elapsed = int(cex_fetch_time - st.session_state.get("cex_fetch_time", cex_fetch_time))
        delta_status = '<br>🔄 <b>증감 화살표</b>: 이전 갱신(10분 전) 대비 변화량. <span style="color:#cf222e;">▲빨강</span> = 거래소 유입(매도 경계) / <span style="color:#1a7f37;">▼초록</span> = 거래소 유출(축적 신호)'
    elif not prev_grand:
        delta_status = '<br>🔄 <b>증감 화살표</b>: 다음 갱신(10분 후) 부터 이전 대비 변화량이 표시됩니다.'

    st.markdown(
        '<div style="background:#f6f8fa;border:1px solid #e1e4e8;border-radius:12px;'
        'padding:1rem 1.25rem;margin-top:1rem;font-size:0.8rem;color:#656d76;line-height:1.7;">'
        '📖 <b>읽는 법:</b><br>'
        '• <b>BTC/ETH/SOL 보유량</b> = 해당 체인 위에 보유한 자산의 달러 가치<br>'
        '• <b>총 보유량</b> = 모든 체인을 합산한 금액'
        + delta_status +
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="error-box">'
        '⚠️ 거래소 보유량 데이터를 가져오지 못했습니다. 잠시 후 새로고침해 주세요.'
        '</div>',
        unsafe_allow_html=True,
    )

# ═══════ [9] 프리미엄 지표 ═══════════════════════════════════════════════════
st.markdown('<div class="section-header">🌍 프리미엄 지표 (코인베이스 / 김치) <span style="color:#8b949e;font-size:0.8rem;font-weight:400;">2분 주기 갱신</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 <b>코인베이스 프리미엄</b> = 미국 Coinbase 가격이 Binance보다 비쌀 정도. 양수면 미국 기관 매수세, 음수면 매도세. '
    '<b>김치 프리미엄</b> = 한국 업비트 가격이 글로벌보다 비쌀 정도. '
    '양수면 한국 투자자 매수 열기가 높음.'
    '</div>',
    unsafe_allow_html=True,
)
pm_data = load_premiums()
if pm_data:
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        cb_p = pm_data.get("coinbase_premium_pct")
        if cb_p is not None:
            cb_color = "#1a7f37" if cb_p > 0 else "#cf222e" if cb_p < 0 else "#656d76"
            cb_signal = "🟢 미국 기관 매수세" if cb_p > 0.05 else "🔴 미국 매도 압력" if cb_p < -0.05 else "⚪ 중립"
            cb_usd = pm_data.get("coinbase_premium_usd", 0)
            st.markdown(f'<div class="metric-card"><div class="metric-label">코인베이스 프리미엄</div><div class="metric-sublabel">Coinbase(USD) vs Binance(USDT) 가격 차이</div><div class="metric-value-sm" style="color:{cb_color};">{cb_p:+.3f}%</div><div style="color:#656d76;font-size:0.72rem;">${cb_usd:+.0f}</div><div class="interp-badge">{cb_signal}</div></div>', unsafe_allow_html=True)
        else:
            src = pm_data.get("global_price_source", "")
            err_hint = "VPN 사용 시 Binance/Coinbase 접속 차단 가능" if not src else "Coinbase API 응답 없음"
            st.markdown(f'<div class="metric-card"><div class="metric-label">코인베이스 프리미엄</div><div class="metric-sublabel">Coinbase(USD) vs Binance(USDT) 가격 차이</div><div class="metric-value-sm" style="color:#8b949e;">데이터 없음</div><div style="color:#bc4c00;font-size:0.72rem;">⚠️ {err_hint}</div></div>', unsafe_allow_html=True)
    with p2:
        kp = pm_data.get("kimchi_premium_pct")
        if kp is not None:
            kp_color = "#cf222e" if kp > 3 else "#1a7f37" if kp > 0 else "#cf222e" if kp < -1 else "#656d76"
            kp_signal = "🟡 과열 주의" if kp > 5 else "🟢 한국 매수세" if kp > 0.5 else "⚪ 중립" if kp > -0.5 else "🔴 역프리미엄"
            upbit_p = pm_data.get("upbit_krw_price", 0)
            global_p = pm_data.get("global_btc_krw", 0)
            st.markdown(f'<div class="metric-card"><div class="metric-label">김치 프리미엄</div><div class="metric-sublabel">한국 업비트 vs 글로벌 가격 차이</div><div class="metric-value-sm" style="color:{kp_color};">{kp:+.3f}%</div><div style="color:#656d76;font-size:0.72rem;">₩{upbit_p:,.0f} vs ₩{global_p:,.0f}</div><div class="interp-badge">{kp_signal}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><div class="metric-label">김치 프리미엄</div><div class="metric-sublabel">한국 업비트 vs 글로벌 가격 차이</div><div class="metric-value-sm" style="color:#8b949e;">데이터 없음</div><div style="color:#bc4c00;font-size:0.72rem;">⚠️ 환율 또는 가격 데이터 수집 실패</div></div>', unsafe_allow_html=True)
    with p3:
        addr = pm_data.get("active_addresses", 0)
        st.markdown(f'<div class="metric-card"><div class="metric-label">활성 주소 수</div><div class="metric-sublabel">24시간 내 비트코인 거래에 참여한 고유 지갑 수</div><div class="metric-value-sm">{fmt_num(addr)}</div><div class="interp-badge">네트워크 활성도</div></div>', unsafe_allow_html=True)
    with p4:
        rate = pm_data.get("usd_krw_rate", 0)
        rate_src = pm_data.get("usd_krw_source", "")
        src_label = rate_src if rate_src else "참고용"
        st.markdown(f'<div class="metric-card"><div class="metric-label">환율 (USD/KRW)</div><div class="metric-sublabel">USDT/KRW 기준 환산 환율</div><div class="metric-value-sm">₩{rate:,.0f}</div><div class="interp-badge">{src_label}</div></div>', unsafe_allow_html=True)

    # 프리미엄 해석
    st.markdown(
        '<div style="background:#f6f8fa;border:1px solid #e1e4e8;border-radius:12px;padding:0.8rem 1.25rem;margin-top:0.5rem;font-size:0.78rem;color:#656d76;line-height:1.6;">'
        '📖 <b>프리미엄 해석:</b> '
        '코인베이스 프리미엄 양수 = 미국 기관 매수 열기 ↑ | '
        '김치 프리미엄 3%+ = 한국 과열 주의 | '
        '둘 다 높은 양수 = 강한 매수 심리'
        '</div>',
        unsafe_allow_html=True,
    )

# ═══════ [10] 라이트닝 네트워크 ════════════════════════════════════════════════
st.markdown('<div class="section-header">⚡ 라이트닝 네트워크 (Lightning Network)</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 비트코인의 <b>2계층 결제 네트워크</b>입니다. 소액 결제를 빠르고 저렴하게 처리합니다. '
    '채널/노드 수가 늘어나면 비트코인의 실제 결제 수단 활용도가 높아지고 있다는 의미입니다.'
    '</div>',
    unsafe_allow_html=True,
)
ln_data = load_lightning()
if ln_data:
    l1, l2, l3, l4, l5 = st.columns(5)
    with l1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">활성 채널 수</div><div class="metric-sublabel">결제를 주고받는 통로의 수. 많을수록 네트워크가 촘촘함</div><div class="metric-value-sm">{fmt_num(ln_data.get("channel_count"))}</div></div>', unsafe_allow_html=True)
    with l2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">노드 수</div><div class="metric-sublabel">네트워크에 참여 중인 컴퓨터(서버) 수. 탈중앙화 지표</div><div class="metric-value-sm">{fmt_num(ln_data.get("node_count"))}</div></div>', unsafe_allow_html=True)
    with l3:
        cap = ln_data.get("total_capacity_btc", 0)
        st.markdown(f'<div class="metric-card"><div class="metric-label">총 용량</div><div class="metric-sublabel">채널에 잠긴 BTC 총량. 네트워크의 유동성 규모</div><div class="metric-value-sm">{cap:,.2f} BTC</div></div>', unsafe_allow_html=True)
    with l4:
        avg = ln_data.get("avg_capacity_sat", 0)
        st.markdown(f'<div class="metric-card"><div class="metric-label">채널당 평균 용량</div><div class="metric-sublabel">채널 하나의 평균 BTC 보유량 (사토시 단위)</div><div class="metric-value-sm">{fmt_num(avg)} sat</div></div>', unsafe_allow_html=True)
    with l5:
        fee = ln_data.get("med_fee_rate", 0)
        st.markdown(f'<div class="metric-card"><div class="metric-label">중간 수수료율</div><div class="metric-sublabel">결제를 중계할 때 받는 수수료의 중간값</div><div class="metric-value-sm">{fee} ppm</div></div>', unsafe_allow_html=True)

# ═══════ [10] 스테이블코인 시가총액 ═══════════════════════════════════════════
st.markdown('<div class="section-header">💵 스테이블코인 시가총액</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 USDT, USDC 같은 <b>달러 연동 코인</b>의 총 발행량입니다. '
    '스테이블코인 시총이 <b>증가</b>하면 시장에 대기 자금(매수 화력)이 늘어나는 것이고, '
    '<b>감소</b>하면 자금이 빠져나가고 있다는 신호입니다.'
    '</div>',
    unsafe_allow_html=True,
)
sc_data = load_stablecoins()
if sc_data and sc_data.get("coins"):
    st.markdown(
        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;text-align:center;">'
        f'<span style="font-size:0.85rem;color:#166534;">스테이블코인 전체 시가총액</span><br>'
        f'<span style="font-size:1.6rem;font-weight:700;color:#166534;">{fmt_usd(sc_data["total_mcap_usd"])}</span>'
        f'<span style="color:#4ade80;font-size:0.8rem;margin-left:0.5rem;">({sc_data.get("coin_count",0)}종)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    sc_rows = []
    for c in sc_data["coins"]:
        pct = (c["mcap_usd"] / sc_data["total_mcap_usd"] * 100) if sc_data["total_mcap_usd"] else 0
        sc_rows.append(
            f'<tr><td style="font-weight:600;">{c["symbol"]}</td><td>{c["name"]}</td>'
            f'<td>{fmt_usd(c["mcap_usd"])}</td><td>{pct:.1f}%</td></tr>'
        )
    sc_table = (
        '<table class="cex-table"><thead><tr><th style="text-align:left;">심볼</th><th style="text-align:left;">이름</th>'
        '<th>시가총액</th><th>비중</th></tr></thead><tbody>'
        + "".join(sc_rows) + '</tbody></table>'
    )
    st.markdown(sc_table, unsafe_allow_html=True)

# ═══════ [11] DeFi TVL ════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🏗️ DeFi TVL (탈중앙금융 예치 자산)</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 <b>TVL(Total Value Locked)</b> = 디파이 프로토콜에 예치된 자산 총액. '
    '이더리움, 솔라나 등 각 블록체인 위의 대출·스왑·스테이킹에 묶인 돈의 규모입니다. '
    'TVL이 <b>높을수록</b> 해당 체인의 생태계가 활발하다는 뜻입니다.'
    '</div>',
    unsafe_allow_html=True,
)
tvl_data = load_defi_tvl()
if tvl_data and tvl_data.get("chains"):
    st.markdown(
        f'<div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;text-align:center;">'
        f'<span style="font-size:0.85rem;color:#1e40af;">DeFi 전체 TVL</span><br>'
        f'<span style="font-size:1.6rem;font-weight:700;color:#1e40af;">{fmt_usd(tvl_data["total_tvl_usd"])}</span>'
        f'<span style="color:#60a5fa;font-size:0.8rem;margin-left:0.5rem;">({tvl_data.get("chain_count",0)}개 체인)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    tvl_rows = []
    max_tvl = tvl_data["chains"][0]["tvl_usd"] if tvl_data["chains"] else 1
    chain_colors = ["#627eea","#f0b90b","#00d4aa","#e84142","#7b3fe4","#1da1f2","#ff6b35","#26a17b"]
    for i, ch in enumerate(tvl_data["chains"]):
        pct = (ch["tvl_usd"] / tvl_data["total_tvl_usd"] * 100) if tvl_data["total_tvl_usd"] else 0
        bar_w = (ch["tvl_usd"] / max_tvl * 100) if max_tvl else 0
        color = chain_colors[i % len(chain_colors)]
        tvl_rows.append(
            f'<tr><td style="font-weight:600;">{ch["name"]}</td>'
            f'<td>{fmt_usd(ch["tvl_usd"])}</td>'
            f'<td><div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;">'
            f'<span style="font-size:0.75rem;color:#656d76;">{pct:.1f}%</span>'
            f'<div class="cex-bar-outer" style="width:80px;"><div class="cex-bar-inner" style="width:{bar_w:.0f}%;background:{color};"></div></div>'
            f'</div></td></tr>'
        )
    tvl_table = (
        '<table class="cex-table"><thead><tr><th style="text-align:left;">블록체인</th>'
        '<th>TVL</th><th style="width:140px;">비중</th></tr></thead><tbody>'
        + "".join(tvl_rows) + '</tbody></table>'
    )
    st.markdown(tvl_table, unsafe_allow_html=True)

# ═══════ [12] 롱/숏 비율 ═════════════════════════════════════════════════════
st.markdown('<div class="section-header">⚖️ BTC 롱/숏 비율 (Long/Short Ratio) <span style="color:#8b949e;font-size:0.8rem;font-weight:400;">2분 주기 갱신</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 <b>롱(Long)</b> = 가격 상승에 베팅한 포지션, <b>숏(Short)</b> = 하락에 베팅한 포지션. '
    '롱 비율이 높으면 시장이 상승을 기대하고 있다는 뜻이고, '
    '너무 한쪽으로 쏠리면 <b>반대 방향 급등락(숏스퀴즈/롱스퀴즈)</b>이 올 수 있습니다.'
    '</div>',
    unsafe_allow_html=True,
)
ls_data = load_long_short()
if ls_data and ls_data.get("exchanges"):
    avg_l = ls_data["avg_long_pct"]
    avg_s = ls_data["avg_short_pct"]
    avg_r = ls_data["avg_ratio"]
    signal_color = "#cf222e" if avg_l > 70 else "#1a7f37" if avg_s > 55 else "#656d76"
    signal_text = "⚠️ 롱 과열 (숏스퀴즈 주의)" if avg_l > 70 else "⚠️ 숏 과열 (롱스퀴즈 주의)" if avg_s > 55 else "균형 상태"
    st.markdown(
        f'<div style="background:#f8f9fa;border:1px solid #e1e4e8;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">'
        f'<div><span style="font-size:0.85rem;color:#656d76;">거래소 평균</span><br>'
        f'<span style="font-size:1.3rem;font-weight:700;color:#1a7f37;">롱 {avg_l:.1f}%</span>'
        f'<span style="color:#8b949e;margin:0 0.5rem;">vs</span>'
        f'<span style="font-size:1.3rem;font-weight:700;color:#cf222e;">숏 {avg_s:.1f}%</span></div>'
        f'<div style="text-align:right;"><span style="font-size:0.85rem;color:#656d76;">롱/숏 비율</span><br>'
        f'<span style="font-size:1.3rem;font-weight:700;">{avg_r:.2f}</span></div>'
        f'<div style="text-align:right;"><span style="font-size:0.85rem;color:{signal_color};font-weight:600;">{signal_text}</span></div>'
        f'</div>'
        f'<div style="margin-top:0.8rem;height:20px;border-radius:10px;overflow:hidden;display:flex;">'
        f'<div style="width:{avg_l}%;background:linear-gradient(90deg,#22c55e,#4ade80);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:#fff;font-weight:600;">롱 {avg_l:.1f}%</div>'
        f'<div style="width:{avg_s}%;background:linear-gradient(90deg,#f87171,#ef4444);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:#fff;font-weight:600;">숏 {avg_s:.1f}%</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # 거래소별 테이블
    ls_rows = []
    for ex in ls_data["exchanges"]:
        l_w = ex["long_pct"]
        s_w = ex["short_pct"]
        ls_rows.append(
            f'<tr><td style="font-weight:600;">{ex["icon"]} {ex["name"]}</td>'
            f'<td style="color:#1a7f37;font-weight:600;">{ex["long_pct"]:.1f}%</td>'
            f'<td style="color:#cf222e;font-weight:600;">{ex["short_pct"]:.1f}%</td>'
            f'<td>{ex["ratio"]:.2f}</td>'
            f'<td><div style="height:14px;border-radius:7px;overflow:hidden;display:flex;">'
            f'<div style="width:{l_w}%;background:#4ade80;"></div>'
            f'<div style="width:{s_w}%;background:#f87171;"></div>'
            f'</div></td></tr>'
        )
    # 실패한 거래소 행 추가
    for fail in ls_data.get("failed_exchanges", []):
        ls_rows.append(
            f'<tr><td style="font-weight:600;color:#8b949e;">⚠️ {fail["name"]}</td>'
            f'<td colspan="4" style="color:#bc4c00;font-size:0.78rem;text-align:left;">'
            f'데이터 수집 실패 (VPN/지역 차단 가능)</td></tr>'
        )
    ls_table = (
        '<table class="cex-table"><thead><tr>'
        '<th style="text-align:left;">거래소</th><th>롱 비율</th><th>숏 비율</th>'
        '<th>비율</th><th style="width:120px;">분포</th>'
        '</tr></thead><tbody>'
        + "".join(ls_rows) + '</tbody></table>'
    )
    st.markdown(ls_table, unsafe_allow_html=True)

# ═══════ [13] BTC 선물 시장 ═══════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 BTC 선물 시장 (Derivatives)</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 <b>미결제약정(OI)</b> = 아직 청산/만기되지 않은 선물 계약의 총액. OI가 급증하면 큰 변동이 임박할 수 있습니다. '
    '<b>펀딩레이트</b> = 롱(매수)·숏(매도) 포지션 간 균형 비용. '
    '양수이면 매수세 우위, 음수이면 매도세 우위를 뜻합니다.'
    '</div>',
    unsafe_allow_html=True,
)
dv_data = load_derivatives()
if dv_data and dv_data.get("top_exchanges"):
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">BTC 미결제약정 (OI)</div><div class="metric-sublabel">전 세계 거래소의 BTC 선물 미결제 포지션 합계</div><div class="metric-value-sm">{fmt_usd(dv_data.get("total_open_interest_usd"))}</div></div>', unsafe_allow_html=True)
    with d2:
        fr = dv_data.get("avg_funding_rate", 0)
        fr_color = "#cf222e" if fr and fr > 0.01 else "#1a7f37" if fr and fr < -0.01 else "#656d76"
        fr_signal = "매수 과열" if fr and fr > 0.05 else "매수 우위" if fr and fr > 0 else "매도 우위" if fr and fr < 0 else "중립"
        st.markdown(f'<div class="metric-card"><div class="metric-label">평균 펀딩레이트</div><div class="metric-sublabel">양수=롱(매수)이 수수료 지불, 음수=숏(매도)이 지불</div><div class="metric-value-sm" style="color:{fr_color};">{fr:.4f}%</div><div class="interp-badge">{fr_signal}</div></div>', unsafe_allow_html=True)
    with d3:
        vol = dv_data.get("total_volume_24h_usd", 0)
        st.markdown(f'<div class="metric-card"><div class="metric-label">24시간 거래량</div><div class="metric-sublabel">BTC 선물 일일 거래 규모</div><div class="metric-value-sm">{fmt_usd(vol) if vol else "N/A"}</div></div>', unsafe_allow_html=True)

    # 거래소별 OI 테이블
    dv_rows = []
    for ex in dv_data["top_exchanges"][:5]:
        fr_v = ex.get("funding_rate", 0)
        fr_str = f'{fr_v:.4f}%' if fr_v else '-'
        dv_rows.append(
            f'<tr><td style="font-weight:600;">{ex["market"]}</td>'
            f'<td>{fmt_usd(ex["open_interest_usd"])}</td>'
            f'<td>{fr_str}</td>'
            f'<td>{ex.get("spread_pct", 0):.4f}%</td></tr>'
        )
    dv_table = (
        '<table class="cex-table"><thead><tr><th style="text-align:left;">거래소</th>'
        '<th>미결제약정</th><th>펀딩레이트</th><th>스프레드</th></tr></thead><tbody>'
        + "".join(dv_rows) + '</tbody></table>'
    )
    st.markdown(dv_table, unsafe_allow_html=True)

# ═══════ [13] 시가총액 TOP 10 ════════════════════════════════════════════════
st.markdown('<div class="section-header">🏆 시가총액 TOP 10</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 시가총액 기준 상위 10개 암호화폐의 현재 가격, 24시간/7일 변동률입니다. '
    '비트코인 외 다른 코인들의 흐름을 한눈에 파악할 수 있습니다.'
    '</div>',
    unsafe_allow_html=True,
)
tc_data = load_top_coins()
if tc_data and tc_data.get("coins"):
    tc_rows = []
    for i, coin in enumerate(tc_data["coins"]):
        chg24 = coin.get("change_24h_pct") or 0
        chg7d = coin.get("change_7d_pct") or 0
        c24 = "#cf222e" if chg24 < 0 else "#1a7f37"
        c7d = "#cf222e" if chg7d < 0 else "#1a7f37"
        tc_rows.append(
            f'<tr><td style="font-weight:600;">{i+1}</td>'
            f'<td style="font-weight:600;">{coin["symbol"].upper()}</td>'
            f'<td>{coin["name"]}</td>'
            f'<td>{fmt_usd(coin["price_usd"])}</td>'
            f'<td>{fmt_usd(coin["market_cap_usd"])}</td>'
            f'<td style="color:{c24};font-weight:600;">{chg24:+.1f}%</td>'
            f'<td style="color:{c7d};font-weight:600;">{chg7d:+.1f}%</td></tr>'
        )
    tc_table = (
        '<table class="cex-table"><thead><tr>'
        '<th style="text-align:left;">#</th><th style="text-align:left;">심볼</th>'
        '<th style="text-align:left;">이름</th><th>가격</th><th>시가총액</th>'
        '<th>24h</th><th>7일</th></tr></thead><tbody>'
        + "".join(tc_rows) + '</tbody></table>'
    )
    st.markdown(tc_table, unsafe_allow_html=True)

# ═══════ [14] 트렌딩 코인 ════════════════════════════════════════════════════
st.markdown('<div class="section-header">🔥 지금 뜨는 코인 (Trending)</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#656d76;font-size:0.82rem;margin-bottom:1rem;line-height:1.6;">'
    '💡 CoinGecko에서 <b>최근 24시간 동안 가장 많이 검색된</b> 코인입니다. '
    '시장 참여자들이 어떤 코인에 관심을 갖고 있는지 보여주는 심리 지표입니다.'
    '</div>',
    unsafe_allow_html=True,
)
tr_data = load_trending()
if tr_data and tr_data.get("coins"):
    tr_cols = st.columns(min(len(tr_data["coins"]), 7))
    for i, coin in enumerate(tr_data["coins"][:7]):
        with tr_cols[i]:
            rank = coin.get("market_cap_rank") or "-"
            st.markdown(
                f'<div class="metric-card" style="text-align:center;padding:1rem;">'
                f'<div style="font-size:1.5rem;margin-bottom:0.3rem;">🔥</div>'
                f'<div style="font-weight:700;font-size:0.9rem;">{coin["symbol"].upper()}</div>'
                f'<div style="color:#656d76;font-size:0.72rem;">{coin["name"]}</div>'
                f'<div style="color:#8b949e;font-size:0.7rem;margin-top:0.3rem;">시총 순위: #{rank}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ═══════ Raw JSON ═════════════════════════════════════════════════════════════
with st.expander("📋 원본 JSON 데이터 보기 (개발자용)"):
    st.json(report)

# ═══════ 면책 ═════════════════════════════════════════════════════════════════
st.markdown("""
<div class="disclaimer">
    ※ 본 대시보드의 '신호/해석'은 통계적 참고용이며 투자 자문이 아닙니다.<br>
    데이터 출처: CoinGecko · mempool.space · alternative.me · Coin Metrics · blockchain.info · bitcoin-data.com · DeFiLlama
</div>
""", unsafe_allow_html=True)
