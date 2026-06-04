#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
btc_onchain.py
==============
비트코인 온체인 데이터 "총정리" 수집 스크립트.

특징
----
- 무료 API만 사용 (대부분 API 키 불필요)
- 외부 라이브러리 없음 (파이썬 표준 라이브러리만 사용 → pip install 불필요)
- 가격 / 네트워크 / 멤풀 / 온체인 활동 / 밸류에이션(MVRV·NUPL 등) / 시장심리 / SOPR 까지
- cron, Windows 작업 스케줄러 등으로 자동화하기 쉬운 구조
- JSON 저장 + CSV 시계열 로그 누적 기능 내장

데이터 출처
-----------
1. CoinGecko            : 가격, 시총, 거래량, ATH, 도미넌스          (키 불필요)
2. mempool.space        : 해시레이트, 난이도, 다음 난이도 조정, 멤풀, 수수료 (키 불필요)
3. alternative.me       : 공포·탐욕 지수                              (키 불필요)
4. Coin Metrics(community): 시총/실현시총/공급량/활성주소/TX수        (키 불필요)
                          → MVRV, NUPL, 실현가격, NVT 직접 계산
5. blockchain.info      : 24h TX수, 거래량(USD), 채굴자 수익, 누적 채굴량 (키 불필요)
6. bitcoin-data.com     : SOPR, Puell Multiple, MVRV Z-Score (선택, 실패 시 자동 스킵)

사용법
------
  python btc_onchain.py            # 전체 리포트를 콘솔에 출력
  python btc_onchain.py --json     # 결과를 JSON으로 stdout 출력 (파이프/다른 프로그램 연동용)
  python btc_onchain.py --save     # ./btc_data/ 에 타임스탬프 JSON 저장 + CSV 로그 1행 누적
  python btc_onchain.py --quiet    # 종합 신호 한 줄만 출력
  python btc_onchain.py --no-color # ANSI 색상 끄기

자동화 예시 (매일 09:05 KST)
  - Linux  crontab:  5 0 * * *  /usr/bin/python3 /path/btc_onchain.py --save  (UTC 00:05 = KST 09:05)
  - Windows: 작업 스케줄러에서 "python C:\\path\\btc_onchain.py --save" 등록

주의: 본 스크립트의 '신호/해석'은 통계적 참고용이며 투자 자문이 아닙니다.
"""

import argparse
import csv
import json
import os
import ssl
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ─────────────────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────────────────
TIMEOUT = 15                     # 각 요청 타임아웃(초)
RETRIES = 2                      # 실패 시 재시도 횟수
USER_AGENT = "btc-onchain-collector/1.0"
ENABLE_BITCOIN_DATA = True       # SOPR/Puell 등 선택 모듈 사용 여부
OUTPUT_DIR = "btc_data"          # --save 시 저장 폴더

# ─────────────────────────────────────────────────────────────────────────────
# HTTP 헬퍼 (표준 라이브러리)
# ─────────────────────────────────────────────────────────────────────────────
def _make_ssl_context():
    """certifi가 있으면 사용, 없으면 기본 SSL 컨텍스트."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def get_json(url, headers=None, timeout=TIMEOUT, retries=RETRIES):
    """URL에서 JSON을 받아 dict/list로 반환. 실패 시 예외를 올림."""
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    ctx = _make_ssl_context()
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=hdrs)
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, ValueError, OSError) as e:
            last_err = e
    raise last_err


def safe_float(v):
    """문자열/None 등을 안전하게 float로. 실패 시 None."""
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 데이터 소스별 수집 함수 (각각 실패해도 부분 결과 + 에러를 남기고 진행)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_coingecko():
    """가격 / 시총 / 거래량 / ATH / 도미넌스."""
    out = {}
    url = ("https://api.coingecko.com/api/v3/coins/markets"
           "?vs_currency=usd&ids=bitcoin"
           "&price_change_percentage=24h,7d,30d")
    data = get_json(url)
    if isinstance(data, list) and data:
        d = data[0]
        out["price_usd"] = safe_float(d.get("current_price"))
        out["market_cap_usd"] = safe_float(d.get("market_cap"))
        out["volume_24h_usd"] = safe_float(d.get("total_volume"))
        out["high_24h"] = safe_float(d.get("high_24h"))
        out["low_24h"] = safe_float(d.get("low_24h"))
        out["ath_usd"] = safe_float(d.get("ath"))
        out["ath_change_pct"] = safe_float(d.get("ath_change_percentage"))
        out["circulating_supply"] = safe_float(d.get("circulating_supply"))
        out["max_supply"] = safe_float(d.get("max_supply"))
        out["change_24h_pct"] = safe_float(d.get("price_change_percentage_24h"))
        out["change_7d_pct"] = safe_float(d.get("price_change_percentage_7d_in_currency"))
        out["change_30d_pct"] = safe_float(d.get("price_change_percentage_30d_in_currency"))
    # 도미넌스
    try:
        g = get_json("https://api.coingecko.com/api/v3/global")
        out["btc_dominance_pct"] = safe_float(
            g.get("data", {}).get("market_cap_percentage", {}).get("btc"))
    except Exception:
        pass
    return out


def fetch_mempool_space():
    """네트워크 / 채굴 / 멤풀 / 수수료."""
    out = {}
    # 추천 수수료 (sat/vB)
    fees = get_json("https://mempool.space/api/v1/fees/recommended")
    out["fee_fastest"] = fees.get("fastestFee")
    out["fee_half_hour"] = fees.get("halfHourFee")
    out["fee_hour"] = fees.get("hourFee")
    out["fee_economy"] = fees.get("economyFee")
    out["fee_minimum"] = fees.get("minimumFee")

    # 해시레이트 / 난이도
    try:
        hr = get_json("https://mempool.space/api/v1/mining/hashrate/3d")
        chr_ = safe_float(hr.get("currentHashrate"))
        out["hashrate_ehs"] = chr_ / 1e18 if chr_ else None     # EH/s
        out["difficulty"] = safe_float(hr.get("currentDifficulty"))
    except Exception:
        pass

    # 다음 난이도 조정
    try:
        da = get_json("https://mempool.space/api/v1/difficulty-adjustment")
        out["diff_progress_pct"] = safe_float(da.get("progressPercent"))
        out["diff_change_pct"] = safe_float(da.get("difficultyChange"))
        out["diff_remaining_blocks"] = da.get("remainingBlocks")
        rt = safe_float(da.get("remainingTime"))
        out["diff_remaining_days"] = round(rt / 86400000, 1) if rt else None
        ert = da.get("estimatedRetargetDate")
        if ert:
            out["diff_retarget_date"] = datetime.fromtimestamp(
                ert / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        pass

    # 멤풀 상태
    try:
        mp = get_json("https://mempool.space/api/mempool")
        out["mempool_tx_count"] = mp.get("count")
        out["mempool_vsize"] = mp.get("vsize")
        tf = safe_float(mp.get("total_fee"))
        out["mempool_total_fee_btc"] = tf / 1e8 if tf else None
    except Exception:
        pass

    # 블록 높이
    try:
        out["block_height"] = get_json("https://mempool.space/api/blocks/tip/height")
    except Exception:
        pass

    # 가격(폴백용)
    try:
        pr = get_json("https://mempool.space/api/v1/prices")
        out["price_usd_mempool"] = safe_float(pr.get("USD"))
    except Exception:
        pass
    return out


def fetch_fear_greed():
    """공포·탐욕 지수 (오늘 + 어제)."""
    out = {}
    data = get_json("https://api.alternative.me/fng/?limit=2")
    arr = data.get("data", [])
    if arr:
        out["value"] = int(arr[0].get("value"))
        out["classification"] = arr[0].get("value_classification")
    if len(arr) > 1:
        out["value_yesterday"] = int(arr[1].get("value"))
    return out


def fetch_coinmetrics():
    """
    Coin Metrics 커뮤니티 API (키 불필요).
    시총/실현시총/공급량/활성주소/TX수/전송가치 → MVRV·NUPL·실현가격·NVT 계산.
    """
    out = {}
    metrics = ["PriceUSD", "CapMrktCurUSD", "CapRealUSD", "SplyCur",
               "AdrActCnt", "TxCnt", "TxTfrValAdjUSD"]
    start = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    url = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
           "?assets=btc&metrics=" + ",".join(metrics) +
           "&frequency=1d&page_size=100&start_time=" + start)
    data = get_json(url)
    rows = data.get("data", [])
    if not rows:
        return out
    # 필요한 핵심 값이 채워진 가장 최근 행 선택 (커뮤니티 데이터는 1~2일 지연될 수 있음)
    row = None
    for r in reversed(rows):
        if r.get("CapMrktCurUSD") and r.get("CapRealUSD") and r.get("SplyCur"):
            row = r
            break
    if row is None:
        row = rows[-1]

    out["cm_date"] = (row.get("time") or "")[:10]
    mcap = safe_float(row.get("CapMrktCurUSD"))
    rcap = safe_float(row.get("CapRealUSD"))
    sply = safe_float(row.get("SplyCur"))
    tfr = safe_float(row.get("TxTfrValAdjUSD"))

    out["market_cap_usd"] = mcap
    out["realized_cap_usd"] = rcap
    out["supply"] = sply
    out["active_addresses"] = safe_float(row.get("AdrActCnt"))
    out["tx_count"] = safe_float(row.get("TxCnt"))
    out["price_usd_cm"] = safe_float(row.get("PriceUSD"))

    # ── 파생 밸류에이션 지표 직접 계산 ──
    if mcap and rcap:
        out["mvrv"] = mcap / rcap                       # 시총 / 실현시총
        out["nupl"] = (mcap - rcap) / mcap              # 순미실현손익
    if rcap and sply:
        out["realized_price_usd"] = rcap / sply         # 실현가격(평균 취득단가 근사)
    if mcap and tfr:
        out["nvt"] = mcap / tfr                         # Network Value to Transactions
    return out


def fetch_blockchain_stats():
    """blockchain.info /stats : 24h TX수, USD 거래량, 채굴자 수익, 누적 채굴량."""
    out = {}
    data = get_json("https://api.blockchain.info/stats?format=json")
    out["n_tx_24h"] = data.get("n_tx")
    out["tx_volume_usd_est"] = safe_float(data.get("estimated_transaction_volume_usd"))
    out["miners_revenue_usd"] = safe_float(data.get("miners_revenue_usd"))
    totalbc = safe_float(data.get("totalbc"))
    out["total_btc_mined"] = totalbc / 1e8 if totalbc else None
    out["minutes_between_blocks"] = safe_float(data.get("minutes_between_blocks"))
    return out


def fetch_bitcoin_data_advanced():
    """
    bitcoin-data.com 무료 엔드포인트 (선택).
    SOPR / Puell Multiple / MVRV Z-Score 등 UTXO 기반 지표.
    포맷이 바뀌거나 막히면 조용히 스킵된다.
    """
    out = {}
    slugs = {
        "sopr": "sopr",
        "puell_multiple": "puell-multiple",
        "mvrv_zscore": "mvrv-zscore",
        "reserve_risk": "reserve-risk",
    }
    for key, slug in slugs.items():
        try:
            data = get_json("https://bitcoin-data.com/v1/%s/last" % slug, retries=0)
            # 응답은 list[dict] 또는 dict 형태일 수 있어 방어적으로 숫자 필드 추출
            rec = data[0] if isinstance(data, list) and data else data
            if isinstance(rec, dict):
                val = None
                for k, v in rec.items():
                    if k.lower() in ("d", "date", "unixts", "theday", "time"):
                        continue
                    fv = safe_float(v)
                    if fv is not None:
                        val = fv
                        break
                if val is not None:
                    out[key] = val
        except Exception:
            continue
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 라이트닝 네트워크 / 스테이블코인 / DeFi / 파생상품 / 트렌딩 / 시총 상위
# ─────────────────────────────────────────────────────────────────────────────
def fetch_lightning_network():
    """라이트닝 네트워크 통계 (mempool.space)."""
    try:
        data = get_json("https://mempool.space/api/v1/lightning/statistics/latest")
        latest = data.get("latest", {})
        channel_count = latest.get("channel_count")
        node_count = latest.get("node_count")
        total_capacity = safe_float(latest.get("total_capacity"))
        avg_capacity = latest.get("avg_capacity")
        med_fee_rate = latest.get("med_fee_rate")
        return {
            "channel_count": int(channel_count) if channel_count is not None else 0,
            "node_count": int(node_count) if node_count is not None else 0,
            "total_capacity_btc": total_capacity / 100_000_000 if total_capacity else 0.0,
            "avg_capacity_sat": int(avg_capacity) if avg_capacity is not None else 0,
            "med_fee_rate": int(med_fee_rate) if med_fee_rate is not None else 0,
        }
    except Exception as e:
        print("[fetch_lightning_network] 오류: %s" % e)
        return {}


def fetch_stablecoin_mcap():
    """주요 스테이블코인 시가총액 (DefiLlama)."""
    try:
        data = get_json("https://stablecoins.llama.fi/stablecoins?includePrices=false")
        assets = data.get("peggedAssets", [])
        target_symbols = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "FDUSD", "USDD", "PYUSD"}
        coins = []
        total_mcap = 0.0
        for asset in assets:
            circ = asset.get("circulating", {})
            mcap = safe_float(circ.get("peggedUSD"))
            if mcap is None:
                mcap = 0.0
            total_mcap += mcap
            symbol = asset.get("symbol", "")
            if symbol in target_symbols:
                coins.append({
                    "name": asset.get("name", ""),
                    "symbol": symbol,
                    "mcap_usd": mcap,
                })
        coins.sort(key=lambda x: x["mcap_usd"], reverse=True)
        coins = coins[:8]
        return {
            "total_mcap_usd": total_mcap,
            "coins": coins,
            "coin_count": len(coins),
        }
    except Exception as e:
        print("[fetch_stablecoin_mcap] 오류: %s" % e)
        return {}


def fetch_defi_tvl():
    """DeFi 체인별 TVL (DefiLlama)."""
    try:
        data = get_json("https://api.llama.fi/v2/chains")
        chains = []
        total_tvl = 0.0
        for item in data:
            tvl = safe_float(item.get("tvl"))
            if tvl is None:
                tvl = 0.0
            total_tvl += tvl
            chains.append({
                "name": item.get("name", ""),
                "tvl_usd": tvl,
            })
        chains.sort(key=lambda x: x["tvl_usd"], reverse=True)
        top_chains = chains[:8]
        return {
            "total_tvl_usd": total_tvl,
            "chains": top_chains,
            "chain_count": len(data),
        }
    except Exception as e:
        print("[fetch_defi_tvl] 오류: %s" % e)
        return {}


def fetch_derivatives():
    """BTC 파생상품(선물) 현황 (CoinGecko)."""
    try:
        data = get_json("https://api.coingecko.com/api/v3/derivatives")
        btc_items = [d for d in data if d.get("index_id") == "BTC"]
        total_oi = 0.0
        total_vol = 0.0
        funding_rates = []
        exchanges = []
        for item in btc_items:
            oi = safe_float(item.get("open_interest")) or 0.0
            vol_str = item.get("trade_volume_24h_btc", "0")
            vol = safe_float(vol_str) or 0.0
            spread = safe_float(item.get("bid_ask_spread")) or 0.0
            fr = safe_float(item.get("funding_rate")) or 0.0
            total_oi += oi
            total_vol += vol
            if fr != 0.0:
                funding_rates.append(fr)
            exchanges.append({
                "market": item.get("market", ""),
                "open_interest_usd": oi,
                "volume_24h_usd": vol,
                "funding_rate": fr,
                "spread_pct": spread,
            })
        exchanges.sort(key=lambda x: x["open_interest_usd"], reverse=True)
        avg_fr = sum(funding_rates) / len(funding_rates) if funding_rates else 0.0
        return {
            "total_open_interest_usd": total_oi,
            "total_volume_24h_usd": total_vol,
            "top_exchanges": exchanges[:5],
            "avg_funding_rate": avg_fr,
        }
    except Exception as e:
        print("[fetch_derivatives] 오류: %s" % e)
        return {}


def fetch_trending_coins():
    """트렌딩 코인 (CoinGecko)."""
    try:
        data = get_json("https://api.coingecko.com/api/v3/search/trending")
        coins_raw = data.get("coins", [])
        coins = []
        for entry in coins_raw[:7]:
            item = entry.get("item", {})
            coins.append({
                "name": item.get("name", ""),
                "symbol": item.get("symbol", ""),
                "market_cap_rank": item.get("market_cap_rank"),
                "price_btc": safe_float(item.get("price_btc")) or 0.0,
                "thumb": item.get("thumb", ""),
            })
        return {
            "coins": coins,
            "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    except Exception as e:
        print("[fetch_trending_coins] 오류: %s" % e)
        return {}


def fetch_top_coins():
    """시가총액 상위 10개 코인 (CoinGecko)."""
    try:
        url = ("https://api.coingecko.com/api/v3/coins/markets"
               "?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
               "&price_change_percentage=24h,7d")
        data = get_json(url)
        coins = []
        for d in data:
            coins.append({
                "name": d.get("name", ""),
                "symbol": d.get("symbol", ""),
                "image": d.get("image", ""),
                "price_usd": safe_float(d.get("current_price")) or 0.0,
                "market_cap_usd": safe_float(d.get("market_cap")) or 0.0,
                "volume_24h_usd": safe_float(d.get("total_volume")) or 0.0,
                "change_24h_pct": safe_float(d.get("price_change_percentage_24h_in_currency")),
                "change_7d_pct": safe_float(d.get("price_change_percentage_7d_in_currency")),
            })
        return {
            "coins": coins,
        }
    except Exception as e:
        print("[fetch_top_coins] 오류: %s" % e)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 프리미엄 지표 (코인베이스 프리미엄 + 김치 프리미엄)
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_real_usd_krw():
    """실제 USD/KRW 환율을 여러 무료 API에서 가져온다 (폴백 체인)."""
    # 1차: exchangerate-api (무료, 키 불필요)
    try:
        data = get_json("https://open.er-api.com/v6/latest/USD", timeout=8, retries=1)
        rate = safe_float(data.get("rates", {}).get("KRW"))
        if rate and rate > 1000:
            return rate, "exchangerate-api"
    except Exception:
        pass

    # 2차: frankfurter (ECB 기반, 무료)
    try:
        data = get_json("https://api.frankfurter.dev/v1/latest?base=USD&symbols=KRW",
                        timeout=8, retries=1)
        rate = safe_float(data.get("rates", {}).get("KRW"))
        if rate and rate > 1000:
            return rate, "frankfurter"
    except Exception:
        pass

    # 3차: 한국수출입은행 (공식 환율, 영업일만)
    try:
        data = get_json("https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
                        "?authkey=SAMPLE&data=AP01&searchtype=AP01&cur_unit=USD",
                        timeout=8, retries=0)
        if data and isinstance(data, list):
            for item in data:
                if item.get("cur_unit") == "USD":
                    rate_str = item.get("deal_bas_r", "").replace(",", "")
                    rate = safe_float(rate_str)
                    if rate and rate > 1000:
                        return rate, "koreaexim"
    except Exception:
        pass

    return None, None


def fetch_premium_indicators():
    """코인베이스/김치 프리미엄 + 활성 주소 수 (무료 API)."""
    out = {}
    errors = []

    # ── 글로벌 BTC 가격 (다중 소스) ──
    bn_price = None

    # 1차: 바이낸스
    try:
        bn = get_json("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        bn_price = float(bn["price"])
        out["binance_price"] = bn_price
        out["global_price_source"] = "Binance"
    except Exception as e:
        errors.append("Binance 가격: %s" % e)

    # 2차 폴백: CoinGecko
    if bn_price is None:
        try:
            cg = get_json("https://api.coingecko.com/api/v3/simple/price"
                          "?ids=bitcoin&vs_currencies=usd", timeout=10, retries=1)
            bn_price = safe_float(cg.get("bitcoin", {}).get("usd"))
            if bn_price:
                out["binance_price"] = bn_price
                out["global_price_source"] = "CoinGecko"
        except Exception as e:
            errors.append("CoinGecko 폴백: %s" % e)

    # ── 코인베이스 프리미엄 ──
    try:
        cb = get_json("https://api.coinbase.com/v2/prices/BTC-USD/spot")
        cb_price = float(cb["data"]["amount"])
        out["coinbase_price"] = cb_price
        if bn_price:
            out["coinbase_premium_pct"] = round((cb_price - bn_price) / bn_price * 100, 4)
            out["coinbase_premium_usd"] = round(cb_price - bn_price, 2)
    except Exception as e:
        errors.append("Coinbase: %s" % e)

    # ── 실제 USD/KRW 환율 ──
    real_usd_krw, rate_source = _fetch_real_usd_krw()

    # ── 김치 프리미엄 ──
    try:
        upbit = get_json("https://api.upbit.com/v1/ticker?markets=KRW-BTC")
        krw_price = float(upbit[0]["trade_price"])
        out["upbit_krw_price"] = krw_price

        # Upbit USDT/KRW (참고용으로 유지)
        try:
            usdt_kr = get_json("https://api.upbit.com/v1/ticker?markets=KRW-USDT")
            out["upbit_usdt_krw"] = float(usdt_kr[0]["trade_price"])
        except Exception:
            pass

        # 환율 결정: 실제 환율 우선, 없으면 Upbit USDT/KRW 폴백
        if real_usd_krw:
            usd_krw = real_usd_krw
            out["usd_krw_rate"] = usd_krw
            out["usd_krw_source"] = rate_source
        elif out.get("upbit_usdt_krw"):
            usd_krw = out["upbit_usdt_krw"]
            out["usd_krw_rate"] = usd_krw
            out["usd_krw_source"] = "Upbit USDT/KRW (폴백)"
            errors.append("실제 환율 API 실패 — Upbit USDT/KRW로 대체 (부정확할 수 있음)")
        else:
            usd_krw = None

        if bn_price and usd_krw:
            global_krw = bn_price * usd_krw
            out["global_btc_krw"] = round(global_krw, 0)
            out["kimchi_premium_pct"] = round(
                (krw_price - global_krw) / global_krw * 100, 4)
    except Exception as e:
        errors.append("Upbit/김프: %s" % e)

    # ── 활성 주소 수 ──
    try:
        data = get_json("https://api.blockchain.info/charts/n-unique-addresses"
                        "?timespan=1days&format=json")
        if data.get("values"):
            out["active_addresses"] = int(data["values"][-1]["y"])
    except Exception:
        pass

    if errors:
        out["errors"] = errors
        for err in errors:
            print("[WARN] fetch_premium_indicators: %s" % err)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# 실시간 청산(Liquidation) 데이터
# ─────────────────────────────────────────────────────────────────────────────
def fetch_liquidations():
    """최근 BTC 청산 데이터 수집 (OKX 무료 API)."""
    try:
        data = get_json(
            "https://www.okx.com/api/v5/public/liquidation-orders"
            "?instType=SWAP&uly=BTC-USDT&state=filled",
            timeout=10, retries=1,
        )
        if not data or data.get("code") != "0" or not data.get("data"):
            return {}

        details = data["data"][0].get("details", [])
        if not details:
            return {}

        import time as _time
        now_ms = int(_time.time() * 1000)

        long_liq_vol = 0.0   # 롱 청산량 (BTC)
        short_liq_vol = 0.0  # 숏 청산량 (BTC)
        long_liq_usd = 0.0
        short_liq_usd = 0.0
        long_count = 0
        short_count = 0
        large_liqs = []  # $100K 이상 대형 청산
        recent = []       # 최근 20건

        for d in details:
            side = d.get("side", "")          # sell = 롱 청산, buy = 숏 청산
            sz = safe_float(d.get("sz", 0))   # BTC 수량
            px = safe_float(d.get("bkPx", 0)) # 청산 가격
            ts = int(d.get("ts", 0))
            usd_val = sz * px if sz and px else 0

            # 시간 필터: 최근 1시간 이내만
            if now_ms - ts > 3600 * 1000:
                continue

            is_long_liq = (side == "sell")  # 롱 포지션이 청산되면 sell 주문 발생

            if is_long_liq:
                long_liq_vol += sz
                long_liq_usd += usd_val
                long_count += 1
            else:
                short_liq_vol += sz
                short_liq_usd += usd_val
                short_count += 1

            # 대형 청산 ($100K+)
            if usd_val >= 100000:
                large_liqs.append({
                    "type": "LONG" if is_long_liq else "SHORT",
                    "btc": round(sz, 4),
                    "usd": round(usd_val, 0),
                    "price": round(px, 1),
                    "ts": ts,
                    "mins_ago": round((now_ms - ts) / 60000, 1),
                })

            # 최근 20건
            if len(recent) < 20:
                recent.append({
                    "type": "LONG" if is_long_liq else "SHORT",
                    "btc": round(sz, 4),
                    "usd": round(usd_val, 0),
                    "price": round(px, 1),
                    "ts": ts,
                    "mins_ago": round((now_ms - ts) / 60000, 1),
                })

        total_vol = long_liq_vol + short_liq_vol
        total_usd = long_liq_usd + short_liq_usd

        # 청산 비대칭 (롱 vs 숏)
        if total_usd > 0:
            long_pct = long_liq_usd / total_usd * 100
            short_pct = short_liq_usd / total_usd * 100
        else:
            long_pct = short_pct = 50.0

        # 시장 해석
        if long_pct > 70:
            signal = "bear"
            desc = "롱 청산 압도적 — 하락 압력 강함"
        elif short_pct > 70:
            signal = "bull"
            desc = "숏 청산 압도적 — 숏스퀴즈 발생 중"
        elif total_usd < 500000:
            signal = "neutral"
            desc = "청산량 미미 — 변동성 낮음"
        else:
            signal = "neutral"
            desc = "롱/숏 청산 균형"

        return {
            "long_liq_btc": round(long_liq_vol, 4),
            "short_liq_btc": round(short_liq_vol, 4),
            "long_liq_usd": round(long_liq_usd, 0),
            "short_liq_usd": round(short_liq_usd, 0),
            "total_liq_usd": round(total_usd, 0),
            "long_count": long_count,
            "short_count": short_count,
            "long_pct": round(long_pct, 1),
            "short_pct": round(short_pct, 1),
            "large_liqs": large_liqs[:10],
            "recent": recent,
            "signal": signal,
            "signal_desc": desc,
            "source": "OKX",
            "period": "1h",
        }
    except Exception as e:
        print("[WARN] fetch_liquidations: %s" % e)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 롱/숏 비율 (Binance, OKX, Bybit 무료 API)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_long_short_ratio():
    """거래소별 BTC 롱/숏 비율 수집 (API 키 불필요)."""
    try:
        exchanges = []
        failed = []

        # ── Binance 글로벌 롱숏 ──
        try:
            bn = get_json("https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
                          "?symbol=BTCUSDT&period=5m&limit=1")
            if bn and len(bn) > 0:
                d = bn[0]
                exchanges.append({
                    "name": "Binance",
                    "icon": "🟡",
                    "long_pct": safe_float(d.get("longAccount", 0)) * 100,
                    "short_pct": safe_float(d.get("shortAccount", 0)) * 100,
                    "ratio": safe_float(d.get("longShortRatio", 0)),
                })
        except Exception as e:
            failed.append({"name": "Binance", "error": str(e)})

        # ── Binance 탑 트레이더 포지션 ──
        try:
            bn_top = get_json("https://fapi.binance.com/futures/data/topLongShortPositionRatio"
                              "?symbol=BTCUSDT&period=5m&limit=1")
            if bn_top and len(bn_top) > 0:
                d = bn_top[0]
                exchanges.append({
                    "name": "Binance (Top)",
                    "icon": "🟡",
                    "long_pct": safe_float(d.get("longAccount", 0)) * 100,
                    "short_pct": safe_float(d.get("shortAccount", 0)) * 100,
                    "ratio": safe_float(d.get("longShortRatio", 0)),
                })
        except Exception as e:
            failed.append({"name": "Binance (Top)", "error": str(e)})

        # ── OKX ──
        try:
            okx = get_json("https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio"
                           "?ccy=BTC&period=5m")
            if okx and okx.get("code") == "0" and okx.get("data"):
                r = safe_float(okx["data"][0][1])
                if r:
                    long_pct = r / (1 + r) * 100
                    short_pct = 100 - long_pct
                    exchanges.append({
                        "name": "OKX",
                        "icon": "⚫",
                        "long_pct": round(long_pct, 2),
                        "short_pct": round(short_pct, 2),
                        "ratio": round(r, 4),
                    })
        except Exception as e:
            failed.append({"name": "OKX", "error": str(e)})

        # ── Bybit ──
        try:
            bybit = get_json("https://api.bybit.com/v5/market/account-ratio"
                             "?category=linear&symbol=BTCUSDT&period=5min&limit=1")
            if bybit and bybit.get("retCode") == 0:
                lst = bybit.get("result", {}).get("list", [])
                if lst:
                    d = lst[0]
                    long_pct = safe_float(d.get("buyRatio", 0)) * 100
                    short_pct = safe_float(d.get("sellRatio", 0)) * 100
                    ratio = long_pct / short_pct if short_pct else 0
                    exchanges.append({
                        "name": "Bybit",
                        "icon": "🟠",
                        "long_pct": round(long_pct, 2),
                        "short_pct": round(short_pct, 2),
                        "ratio": round(ratio, 4),
                    })
        except Exception as e:
            failed.append({"name": "Bybit", "error": str(e)})

        # ── Bitget ──
        try:
            bg = get_json("https://api.bitget.com/api/v2/mix/market/account-long-short"
                          "?symbol=BTCUSDT&productType=USDT-FUTURES&period=5m")
            if bg and bg.get("code") == "00000" and bg.get("data"):
                d = bg["data"][0]
                exchanges.append({
                    "name": "Bitget",
                    "icon": "🔵",
                    "long_pct": round(safe_float(d.get("longAccountRatio", 0)) * 100, 2),
                    "short_pct": round(safe_float(d.get("shortAccountRatio", 0)) * 100, 2),
                    "ratio": safe_float(d.get("longShortAccountRatio", 0)),
                })
        except Exception as e:
            failed.append({"name": "Bitget", "error": str(e)})

        # ── HTX (Huobi) ──
        try:
            htx = get_json("https://api.hbdm.com/linear-swap-api/v1/swap_elite_account_ratio"
                           "?contract_code=BTC-USDT&period=5min")
            if htx and htx.get("status") == "ok":
                lst = htx.get("data", {}).get("list", [])
                if lst:
                    d = lst[-1]  # 최신 데이터
                    buy = safe_float(d.get("buy_ratio", 0))
                    sell = safe_float(d.get("sell_ratio", 0))
                    total = buy + sell
                    if total > 0:
                        long_pct = buy / total * 100
                        short_pct = sell / total * 100
                        ratio = long_pct / short_pct if short_pct else 0
                        exchanges.append({
                            "name": "HTX",
                            "icon": "🔷",
                            "long_pct": round(long_pct, 2),
                            "short_pct": round(short_pct, 2),
                            "ratio": round(ratio, 4),
                        })
        except Exception as e:
            failed.append({"name": "HTX", "error": str(e)})

        if not exchanges:
            return {"failed_exchanges": failed} if failed else {}

        # 전체 평균
        avg_long = sum(e["long_pct"] for e in exchanges) / len(exchanges)
        avg_short = sum(e["short_pct"] for e in exchanges) / len(exchanges)
        avg_ratio = avg_long / avg_short if avg_short else 0

        result = {
            "exchanges": exchanges,
            "avg_long_pct": round(avg_long, 2),
            "avg_short_pct": round(avg_short, 2),
            "avg_ratio": round(avg_ratio, 4),
            "exchange_count": len(exchanges),
        }
        if failed:
            result["failed_exchanges"] = failed
            for f in failed:
                print("[WARN] fetch_long_short_ratio %s 실패: %s" % (f["name"], f["error"]))
        return result
    except Exception as e:
        print("[WARN] fetch_long_short_ratio 실패: %s" % e)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 거래소 보유량 (DeFiLlama 무료 API)
# ─────────────────────────────────────────────────────────────────────────────
CEX_SLUGS = [
    ("binance-cex", "Binance", "🟡"),
    ("okx", "OKX", "⚫"),
    ("bybit", "Bybit", "🟠"),
    ("bitfinex", "Bitfinex", "🟢"),
    ("robinhood", "Robinhood", "🟢"),
    ("crypto-com", "Crypto.com", "🔵"),
    ("gate-io", "Gate.io", "🔵"),
    ("htx", "HTX", "🔵"),
    ("kucoin", "KuCoin", "🟢"),
    ("deribit", "Deribit", "⚪"),
]

# 추적할 체인 목록 (체인이름, 표시이름)
CEX_CHAINS = [
    ("Bitcoin", "BTC"),
    ("Ethereum", "ETH"),
    ("Solana", "SOL"),
    ("Tron", "TRON"),
    ("Arbitrum", "ARB"),
    ("Avalanche", "AVAX"),
]


def fetch_cex_reserves():
    """
    DeFiLlama API로 주요 거래소(CEX)의 체인별 보유 자산 규모를 조회.
    거래소에 쌓인 코인이 늘면 매도 압력, 줄면 인출(축적) 신호.
    무료 / 키 불필요 / 1시간 주기 업데이트.
    """
    results = []
    totals = {}  # chain_name -> total USD value

    for slug, display_name, icon in CEX_SLUGS:
        try:
            data = get_json(
                f"https://api.llama.fi/protocol/{slug}",
                timeout=10, retries=1
            )
            chains = data.get("currentChainTvls", {})
            total_usd = sum(
                v for v in chains.values() if isinstance(v, (int, float))
            )

            entry = {
                "slug": slug,
                "name": display_name,
                "icon": icon,
                "total_usd": total_usd,
                "chains": {},
            }

            for chain_key, chain_label in CEX_CHAINS:
                val = chains.get(chain_key, 0)
                entry["chains"][chain_label] = val
                totals[chain_label] = totals.get(chain_label, 0) + val

            results.append(entry)
        except Exception:
            continue

    # 전체 거래소 합산
    grand_total = sum(e["total_usd"] for e in results)

    return {
        "exchanges": results,
        "totals": totals,
        "grand_total_usd": grand_total,
        "exchange_count": len(results),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 해석 / 신호 (참고용 — 투자 자문 아님)
# ─────────────────────────────────────────────────────────────────────────────
def interpret_mvrv(v):
    if v is None:
        return None
    if v < 1:
        return "극도 저평가 (역사적 바닥권, 실현가 하회)"
    if v < 1.5:
        return "저평가 구간"
    if v < 2.5:
        return "중립"
    if v < 3.7:
        return "과열 진입"
    return "역사적 고점권 (과매수)"


def interpret_nupl(v):
    if v is None:
        return None
    if v < 0:
        return "Capitulation (항복 — 시장 전반 손실)"
    if v < 0.25:
        return "Hope / Fear"
    if v < 0.5:
        return "Optimism / Anxiety"
    if v < 0.75:
        return "Belief / Denial"
    return "Euphoria / Greed (도취 — 고점 경계)"


def interpret_puell(v):
    if v is None:
        return None
    if v < 0.5:
        return "채굴자 항복 (역사적 매수 구간)"
    if v > 4:
        return "채굴자 고수익 (역사적 고점 경계)"
    return "중립"


def composite_signal(d):
    """MVRV·NUPL·공포탐욕·Puell을 0~100 점수로 묶어 대략적 시장 온도 표시."""
    score, n = 0.0, 0
    mvrv = d.get("valuation", {}).get("mvrv")
    nupl = d.get("valuation", {}).get("nupl")
    fg = d.get("sentiment", {}).get("value")
    puell = d.get("advanced", {}).get("puell_multiple")

    if mvrv is not None:
        score += max(0, min(100, (mvrv - 0.7) / (4.0 - 0.7) * 100)); n += 1
    if nupl is not None:
        score += max(0, min(100, (nupl + 0.1) / (0.75 + 0.1) * 100)); n += 1
    if fg is not None:
        score += fg; n += 1
    if puell is not None:
        score += max(0, min(100, (puell - 0.3) / (4.0 - 0.3) * 100)); n += 1

    if n == 0:
        return None, None
    s = round(score / n, 1)
    if s < 25:
        label = "❄️  과매도 / 저평가 영역"
    elif s < 45:
        label = "🟢 중립~저평가"
    elif s < 60:
        label = "🟡 중립"
    elif s < 75:
        label = "🟠 과열 진입"
    else:
        label = "🔥 과열 / 고점 경계"
    return s, label


def _lerp_score(value, low, high):
    """value를 [low, high] 범위에서 0~100 점수로 선형 보간. low일수록 100(매수), high일수록 0."""
    if value is None:
        return None
    return max(0.0, min(100.0, (1.0 - (value - low) / (high - low)) * 100.0))


def compute_buy_signal(report, premium=None, long_short=None, derivatives=None):
    """
    온체인 + 파생상품 지표를 종합하여 매수 적기 판단.

    반환값: {
        "score": 0~100 (100 = 극매수 적기),
        "grade": "A+" ~ "F",
        "label": "적극 매수 구간" 등,
        "summary": 한 줄 요약,
        "indicators": [{"name", "value", "score", "weight", "signal", "desc"}, ...],
        "bull_count": 강세 지표 수,
        "bear_count": 약세 지표 수,
        "neutral_count": 중립 지표 수,
    }
    """
    indicators = []

    def add(name, value, score, weight, desc):
        if score is None:
            return
        if score >= 65:
            signal = "bull"
        elif score <= 35:
            signal = "bear"
        else:
            signal = "neutral"
        indicators.append({
            "name": name,
            "value": value,
            "score": round(score, 1),
            "weight": weight,
            "signal": signal,
            "desc": desc,
        })

    va = report.get("valuation", {})
    se = report.get("sentiment", {})
    ad = report.get("advanced", {})

    # ── [1] MVRV (가중치 3) ──────────────────────────────────────────────
    # 시가총액/실현시가총액. <1 극저평가, >3.7 극고평가
    mvrv = va.get("mvrv")
    s = _lerp_score(mvrv, 0.7, 4.0)
    if mvrv is not None:
        if mvrv < 1.0:
            desc = "실현가 하회 — 역사적 바닥권"
        elif mvrv < 1.5:
            desc = "저평가 구간"
        elif mvrv < 2.5:
            desc = "적정 가치 범위"
        elif mvrv < 3.5:
            desc = "과열 진입"
        else:
            desc = "역사적 고점권"
        add("MVRV", "%.2f" % mvrv, s, 3, desc)

    # ── [2] NUPL (가중치 3) ──────────────────────────────────────────────
    # 순미실현손익. <0 항복, >0.75 도취
    nupl = va.get("nupl")
    s = _lerp_score(nupl, -0.1, 0.75)
    if nupl is not None:
        if nupl < 0:
            desc = "시장 전반 손실 — 항복 단계"
        elif nupl < 0.25:
            desc = "희망/두려움 구간"
        elif nupl < 0.5:
            desc = "낙관 구간"
        elif nupl < 0.75:
            desc = "확신/부정 구간"
        else:
            desc = "도취 — 고점 경계"
        add("NUPL", "%.3f" % nupl, s, 3, desc)

    # ── [3] 공포탐욕 지수 (가중치 2) ─────────────────────────────────────
    # 0=극공포(매수), 100=극탐욕(매도)
    fg = se.get("value")
    if fg is not None:
        s = 100.0 - fg  # 공포일수록 매수 점수 높음
        if fg <= 25:
            desc = "극심한 공포 — 역사적 매수 기회"
        elif fg <= 45:
            desc = "공포 — 매수 고려 구간"
        elif fg <= 55:
            desc = "중립"
        elif fg <= 75:
            desc = "탐욕 — 주의"
        else:
            desc = "극심한 탐욕 — 고점 경계"
        add("공포탐욕", str(fg), s, 2, desc)

    # ── [4] Puell Multiple (가중치 2) ────────────────────────────────────
    # 채굴자 수익. <0.5 채굴자 항복(매수), >4 고수익(매도)
    puell = ad.get("puell_multiple")
    s = _lerp_score(puell, 0.3, 4.0)
    if puell is not None:
        if puell < 0.5:
            desc = "채굴자 항복 — 역사적 매수 구간"
        elif puell < 1.0:
            desc = "채굴자 수익 저조"
        elif puell < 2.0:
            desc = "적정 수익"
        else:
            desc = "고수익 — 매도 압력 가능"
        add("Puell", "%.2f" % puell, s, 2, desc)

    # ── [5] SOPR (가중치 2) ──────────────────────────────────────────────
    # 실현 손익 비율. <1 손실 실현(매수), >1.05 이익 실현(매도)
    sopr = ad.get("sopr")
    s = _lerp_score(sopr, 0.92, 1.08)
    if sopr is not None:
        if sopr < 0.97:
            desc = "대규모 손실 실현 — 항복 신호"
        elif sopr < 1.0:
            desc = "손실 실현 중 — 매수 고려"
        elif sopr < 1.03:
            desc = "소폭 이익 실현"
        else:
            desc = "대규모 이익 실현 — 매도 압력"
        add("SOPR", "%.3f" % sopr, s, 2, desc)

    # ── [6] MVRV Z-Score (가중치 2) ──────────────────────────────────────
    zscore = ad.get("mvrv_zscore")
    s = _lerp_score(zscore, -0.5, 7.0)
    if zscore is not None:
        if zscore < 0:
            desc = "극저평가 — 역사적 바닥"
        elif zscore < 2:
            desc = "저평가~적정"
        elif zscore < 5:
            desc = "적정~고평가"
        else:
            desc = "극고평가 — 역사적 고점"
        add("Z-Score", "%.2f" % zscore, s, 2, desc)

    # ── [7] 코인베이스 프리미엄 (가중치 1) ───────────────────────────────
    if premium:
        cb_pct = premium.get("coinbase_premium_pct")
        if cb_pct is not None:
            # 양수 프리미엄 = 기관 매수 = 강세 신호
            s = max(0, min(100, 50 + cb_pct * 100))  # ±0.5% → 0~100
            if cb_pct > 0.1:
                desc = "미국 기관 매수세 유입"
            elif cb_pct > -0.05:
                desc = "중립"
            else:
                desc = "미국 매도 압력"
            add("CB 프리미엄", "%+.3f%%" % cb_pct, s, 1, desc)

    # ── [8] 김치 프리미엄 (가중치 1) ─────────────────────────────────────
    if premium:
        kp = premium.get("kimchi_premium_pct")
        if kp is not None:
            # 높은 김프(>5%) = 과열, 역프리미엄 = 매수 기회
            s = _lerp_score(kp, -3.0, 8.0)
            if kp > 5:
                desc = "한국 과열 — 고점 경계"
            elif kp > 2:
                desc = "한국 매수세 강함"
            elif kp > -1:
                desc = "중립"
            else:
                desc = "역프리미엄 — 매수 기회"
            add("김치 프리미엄", "%+.2f%%" % kp, s, 1, desc)

    # ── [9] 롱/숏 비율 (가중치 1, 역행 지표) ─────────────────────────────
    if long_short and long_short.get("avg_long_pct"):
        avg_l = long_short["avg_long_pct"]
        # 롱 과도 쏠림(>70%) = 숏스퀴즈 위험이지만 과열 신호 → 매수 점수 낮음
        s = _lerp_score(avg_l, 35, 75)
        if avg_l > 70:
            desc = "롱 과열 — 숏스퀴즈 위험"
        elif avg_l > 55:
            desc = "롱 우위 — 상승 기대감"
        elif avg_l > 45:
            desc = "균형 상태"
        else:
            desc = "숏 우위 — 반등 가능성"
        add("롱/숏", "%.1f%% 롱" % avg_l, s, 1, desc)

    # ── [10] 펀딩레이트 (가중치 1) ───────────────────────────────────────
    if derivatives and derivatives.get("avg_funding_rate") is not None:
        fr = derivatives["avg_funding_rate"]
        # 음수 = 숏 비용 지불 = 매수 신호, 양수 과도 = 과열
        s = _lerp_score(fr, -0.02, 0.08)
        if fr < -0.005:
            desc = "숏 과열 — 역발상 매수 구간"
        elif fr < 0.01:
            desc = "중립 범위"
        elif fr < 0.03:
            desc = "롱 비용 증가"
        else:
            desc = "과열 — 레버리지 청산 위험"
        add("펀딩레이트", "%.4f" % fr, s, 1, desc)

    # ── 종합 점수 계산 (가중 평균) ───────────────────────────────────────
    if not indicators:
        return None

    total_weight = sum(ind["weight"] for ind in indicators)
    weighted_sum = sum(ind["score"] * ind["weight"] for ind in indicators)
    final_score = round(weighted_sum / total_weight, 1) if total_weight else 0

    bull_count = sum(1 for i in indicators if i["signal"] == "bull")
    bear_count = sum(1 for i in indicators if i["signal"] == "bear")
    neutral_count = sum(1 for i in indicators if i["signal"] == "neutral")

    # 등급
    if final_score >= 85:
        grade, label = "A+", "💎 적극 매수 구간"
        summary = "대부분의 온체인 지표가 역사적 저평가를 가리킵니다. 장기 투자 관점에서 매우 유리한 구간입니다."
    elif final_score >= 70:
        grade, label = "A", "🟢 매수 유리 구간"
        summary = "다수의 지표가 저평가를 시사합니다. 분할 매수를 고려할 수 있는 구간입니다."
    elif final_score >= 60:
        grade, label = "B+", "🟢 매수 고려 구간"
        summary = "시장이 저평가~적정 범위에 있습니다. 공포 심리가 있다면 기회일 수 있습니다."
    elif final_score >= 50:
        grade, label = "B", "🟡 중립 (관망)"
        summary = "뚜렷한 방향성 없이 균형 상태입니다. 급한 매수보다는 관망이 적절합니다."
    elif final_score >= 40:
        grade, label = "C", "🟡 중립~주의"
        summary = "일부 지표가 과열을 시사합니다. 신규 매수보다는 보유 유지가 적절합니다."
    elif final_score >= 25:
        grade, label = "D", "🟠 과열 주의"
        summary = "다수의 지표가 과열을 가리킵니다. 분할 매도나 차익 실현을 고려할 구간입니다."
    else:
        grade, label = "F", "🔴 고점 경계"
        summary = "대부분의 지표가 극도의 과열을 가리킵니다. 역사적 고점권에 해당하며 리스크 관리가 필요합니다."

    return {
        "score": final_score,
        "grade": grade,
        "label": label,
        "summary": summary,
        "indicators": indicators,
        "bull_count": bull_count,
        "bear_count": bear_count,
        "neutral_count": neutral_count,
        "indicator_count": len(indicators),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 수집 오케스트레이션
# ─────────────────────────────────────────────────────────────────────────────
def collect():
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timestamp_kst": (datetime.now(timezone.utc) + timedelta(hours=9))
                         .strftime("%Y-%m-%d %H:%M:%S KST"),
        "errors": {},
    }

    jobs = [
        ("price_market", fetch_coingecko),
        ("network", fetch_mempool_space),
        ("sentiment", fetch_fear_greed),
        ("valuation", fetch_coinmetrics),
        ("activity", fetch_blockchain_stats),
    ]
    if ENABLE_BITCOIN_DATA:
        jobs.append(("advanced", fetch_bitcoin_data_advanced))

    for key, fn in jobs:
        try:
            report[key] = fn()
        except Exception as e:
            report[key] = {}
            report["errors"][key] = "%s: %s" % (type(e).__name__, e)

    # 가격 폴백: CoinGecko 실패 시 mempool / Coin Metrics 가격 사용
    pm = report.get("price_market", {})
    if not pm.get("price_usd"):
        pm["price_usd"] = (report.get("network", {}).get("price_usd_mempool")
                           or report.get("valuation", {}).get("price_usd_cm"))
        report["price_market"] = pm

    s, label = composite_signal(report)
    report["composite"] = {"score_0_100": s, "label": label}
    return report


# ─────────────────────────────────────────────────────────────────────────────
# 콘솔 렌더링
# ─────────────────────────────────────────────────────────────────────────────
class C:
    def __init__(self, on):
        self.on = on
    def _w(self, code, s):
        return ("\033[%sm%s\033[0m" % (code, s)) if self.on else s
    def b(self, s):   return self._w("1", s)
    def dim(self, s): return self._w("2", s)
    def cy(self, s):  return self._w("36", s)
    def gr(self, s):  return self._w("32", s)
    def ye(self, s):  return self._w("33", s)
    def rd(self, s):  return self._w("31", s)


def fmt_usd(v, dp=0):
    if v is None:
        return "-"
    if abs(v) >= 1e12:
        return "$%.2fT" % (v / 1e12)
    if abs(v) >= 1e9:
        return "$%.2fB" % (v / 1e9)
    if abs(v) >= 1e6:
        return "$%.2fM" % (v / 1e6)
    return "$%s" % format(round(v, dp), ",.0f" if dp == 0 else ",.%df" % dp)


def fmt_num(v, dp=0):
    if v is None:
        return "-"
    return format(round(v, dp), ",.0f" if dp == 0 else ",.%df" % dp)


def fmt_pct(v):
    if v is None:
        return "-"
    return "%+.2f%%" % v


def render(report, color=True, quiet=False):
    c = C(color)
    out = []
    comp = report.get("composite", {})

    if quiet:
        return "[%s] 종합 신호: %s (%s/100)  |  BTC %s" % (
            report["timestamp_kst"],
            comp.get("label", "-"),
            comp.get("score_0_100", "-"),
            fmt_usd(report.get("price_market", {}).get("price_usd")),
        )

    line = "═" * 64
    out.append(c.cy(line))
    out.append(c.b("  ₿  비트코인 온체인 데이터 총정리"))
    out.append(c.dim("  " + report["timestamp_kst"]))
    out.append(c.cy(line))

    # [1] 가격 & 시장
    pm = report.get("price_market", {})
    out.append(c.b("\n[1] 가격 & 시장"))
    out.append("  현재가          %s   (24h %s / 7d %s / 30d %s)" % (
        fmt_usd(pm.get("price_usd")), fmt_pct(pm.get("change_24h_pct")),
        fmt_pct(pm.get("change_7d_pct")), fmt_pct(pm.get("change_30d_pct"))))
    out.append("  시가총액        %s" % fmt_usd(pm.get("market_cap_usd")))
    out.append("  24h 거래량      %s" % fmt_usd(pm.get("volume_24h_usd")))
    out.append("  24h 고가/저가   %s / %s" % (fmt_usd(pm.get("high_24h")), fmt_usd(pm.get("low_24h"))))
    out.append("  ATH            %s  (ATH 대비 %s)" % (
        fmt_usd(pm.get("ath_usd")), fmt_pct(pm.get("ath_change_pct"))))
    out.append("  BTC 도미넌스    %s" % (
        "%.1f%%" % pm["btc_dominance_pct"] if pm.get("btc_dominance_pct") else "-"))
    out.append("  유통량          %s BTC" % fmt_num(pm.get("circulating_supply")))

    # [2] 네트워크 & 채굴
    nw = report.get("network", {})
    out.append(c.b("\n[2] 네트워크 & 채굴"))
    out.append("  블록 높이       %s" % fmt_num(nw.get("block_height")))
    out.append("  해시레이트      %s EH/s" % (
        "%.1f" % nw["hashrate_ehs"] if nw.get("hashrate_ehs") else "-"))
    out.append("  난이도          %s" % fmt_usd(nw.get("difficulty")).replace("$", ""))
    out.append("  다음 난이도조정 진행률 %s%%, 예상변화 %s, 잔여 %s블록(~%s일), %s" % (
        "%.1f" % nw["diff_progress_pct"] if nw.get("diff_progress_pct") is not None else "-",
        fmt_pct(nw.get("diff_change_pct")),
        nw.get("diff_remaining_blocks", "-"),
        nw.get("diff_remaining_days", "-"),
        nw.get("diff_retarget_date", "-")))

    # [3] 멤풀 & 수수료
    out.append(c.b("\n[3] 멤풀 & 수수료 (sat/vB)"))
    out.append("  빠름/30분/1시간/저속  %s / %s / %s / %s" % (
        nw.get("fee_fastest", "-"), nw.get("fee_half_hour", "-"),
        nw.get("fee_hour", "-"), nw.get("fee_economy", "-")))
    out.append("  멤풀 대기 TX    %s 건  (총 수수료 %.3f BTC)" % (
        fmt_num(nw.get("mempool_tx_count")),
        nw.get("mempool_total_fee_btc") or 0))

    # [4] 온체인 활동
    ac = report.get("activity", {})
    va = report.get("valuation", {})
    out.append(c.b("\n[4] 온체인 활동"))
    out.append("  활성 주소(1d)   %s" % fmt_num(va.get("active_addresses")))
    out.append("  TX 수(1d)       %s" % fmt_num(va.get("tx_count") or ac.get("n_tx_24h")))
    out.append("  추정 거래량(USD) %s" % fmt_usd(ac.get("tx_volume_usd_est")))
    out.append("  채굴자 수익(24h) %s" % fmt_usd(ac.get("miners_revenue_usd")))
    out.append("  누적 채굴량      %s BTC" % fmt_num(ac.get("total_btc_mined")))

    # [5] 밸류에이션 (고급 지표 — 무료 계산)
    out.append(c.b("\n[5] 밸류에이션 지표  ") + c.dim("(Coin Metrics 기반 계산, 기준일 %s)" % va.get("cm_date", "-")))
    mvrv = va.get("mvrv")
    nupl = va.get("nupl")
    out.append("  MVRV            %s   %s" % (
        "%.2f" % mvrv if mvrv else "-", c.dim(interpret_mvrv(mvrv) or "")))
    out.append("  NUPL            %s   %s" % (
        "%.3f" % nupl if nupl is not None else "-", c.dim(interpret_nupl(nupl) or "")))
    out.append("  실현가격         %s" % fmt_usd(va.get("realized_price_usd")))
    out.append("  실현 시총        %s" % fmt_usd(va.get("realized_cap_usd")))
    out.append("  NVT             %s" % ("%.1f" % va["nvt"] if va.get("nvt") else "-"))

    # [6] 시장 심리
    se = report.get("sentiment", {})
    out.append(c.b("\n[6] 시장 심리"))
    out.append("  공포·탐욕 지수   %s (%s)   어제: %s" % (
        se.get("value", "-"), se.get("classification", "-"),
        se.get("value_yesterday", "-")))

    # [7] 고급 지표 (선택)
    ad = report.get("advanced", {})
    if ad:
        out.append(c.b("\n[7] 고급 지표  ") + c.dim("(bitcoin-data.com)"))
        if ad.get("sopr") is not None:
            out.append("  SOPR            %.3f   %s" % (
                ad["sopr"], c.dim("1 미만=손실 실현 / 1 초과=이익 실현")))
        if ad.get("puell_multiple") is not None:
            out.append("  Puell Multiple  %.3f   %s" % (
                ad["puell_multiple"], c.dim(interpret_puell(ad["puell_multiple"]) or "")))
        if ad.get("mvrv_zscore") is not None:
            out.append("  MVRV Z-Score    %.2f" % ad["mvrv_zscore"])
        if ad.get("reserve_risk") is not None:
            out.append("  Reserve Risk    %.6f" % ad["reserve_risk"])

    # [8] 종합 신호
    out.append(c.b("\n[8] 종합 신호"))
    score = comp.get("score_0_100")
    label = comp.get("label", "-")
    bar = ""
    if score is not None:
        filled = int(round(score / 5))
        bar = "[" + "█" * filled + "·" * (20 - filled) + "]"
    out.append("  시장 온도        %s  %s/100  %s" % (bar, score if score is not None else "-", label))
    out.append(c.dim("  ※ 통계적 참고용이며 투자 자문이 아닙니다."))

    # 에러
    if report.get("errors"):
        out.append(c.ye("\n[!] 일부 소스 수집 실패:"))
        for k, v in report["errors"].items():
            out.append(c.ye("  - %s: %s" % (k, v)))

    out.append(c.cy(line))
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# 저장 (JSON 스냅샷 + CSV 시계열 로그)
# ─────────────────────────────────────────────────────────────────────────────
CSV_FIELDS = [
    "timestamp_utc", "price_usd", "market_cap_usd", "realized_price_usd",
    "mvrv", "nupl", "nvt", "fear_greed", "hashrate_ehs", "fee_fastest",
    "active_addresses", "sopr", "puell_multiple", "composite_score",
]


def save_outputs(report, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    # 1) JSON 스냅샷
    ts = report["timestamp_utc"].replace(":", "").replace("-", "")
    json_path = os.path.join(out_dir, "btc_%s.json" % ts)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 2) CSV 시계열 누적 (한 줄/실행)
    csv_path = os.path.join(out_dir, "btc_timeseries.csv")
    pm = report.get("price_market", {})
    nw = report.get("network", {})
    va = report.get("valuation", {})
    se = report.get("sentiment", {})
    ad = report.get("advanced", {})
    row = {
        "timestamp_utc": report["timestamp_utc"],
        "price_usd": pm.get("price_usd"),
        "market_cap_usd": pm.get("market_cap_usd") or va.get("market_cap_usd"),
        "realized_price_usd": va.get("realized_price_usd"),
        "mvrv": va.get("mvrv"),
        "nupl": va.get("nupl"),
        "nvt": va.get("nvt"),
        "fear_greed": se.get("value"),
        "hashrate_ehs": nw.get("hashrate_ehs"),
        "fee_fastest": nw.get("fee_fastest"),
        "active_addresses": va.get("active_addresses"),
        "sopr": ad.get("sopr"),
        "puell_multiple": ad.get("puell_multiple"),
        "composite_score": report.get("composite", {}).get("score_0_100"),
    }
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            w.writeheader()
        w.writerow(row)
    return json_path, csv_path


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Windows 콘솔(cp949 등)에서 유니코드 출력 깨짐 방지
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="비트코인 온체인 데이터 총정리 (무료 API)")
    p.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    p.add_argument("--save", action="store_true", help="JSON 저장 + CSV 시계열 누적")
    p.add_argument("--quiet", action="store_true", help="종합 신호 한 줄만 출력")
    p.add_argument("--no-color", action="store_true", help="ANSI 색상 끄기")
    p.add_argument("--save-dir", default=OUTPUT_DIR, help="저장 폴더 (기본: %s)" % OUTPUT_DIR)
    args = p.parse_args()

    report = collect()

    if args.save:
        jp, cp = save_outputs(report, args.save_dir)
        if not args.json and not args.quiet:
            print("저장됨: %s\n시계열: %s\n" % (jp, cp))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        color = sys.stdout.isatty() and not args.no_color
        print(render(report, color=color, quiet=args.quiet))


if __name__ == "__main__":
    main()
