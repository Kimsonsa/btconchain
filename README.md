# ₿ BTC On-Chain Data Collector

비트코인 온체인 데이터를 **무료 API**만 사용하여 한 번에 수집하는 Python 스크립트입니다.

## ✨ 특징

- **외부 라이브러리 불필요** — Python 표준 라이브러리만 사용 (`pip install` 없음)
- **API 키 불필요** — 모든 데이터 소스가 무료 공개 API
- **8개 카테고리** 데이터 수집: 가격, 네트워크, 멤풀, 온체인 활동, 밸류에이션, 시장심리, 고급 지표, 종합 신호
- **자동화 친화적** — cron / Windows 작업 스케줄러로 주기 실행 가능
- **JSON + CSV 저장** — 스냅샷 저장 및 시계열 로그 누적

## 📊 데이터 소스

| 소스 | 수집 항목 |
|------|-----------|
| CoinGecko | 가격, 시총, 거래량, ATH, 도미넌스 |
| mempool.space | 해시레이트, 난이도, 멤풀, 수수료 |
| alternative.me | 공포·탐욕 지수 |
| Coin Metrics | 실현시총, MVRV, NUPL, NVT 계산 |
| blockchain.info | TX수, 거래량, 채굴자 수익 |
| bitcoin-data.com | SOPR, Puell Multiple, MVRV Z-Score |

## 🚀 사용법

```bash
# 전체 리포트 출력
python btc_onchain.py

# JSON 출력
python btc_onchain.py --json

# 파일 저장 (btc_data/ 폴더에 JSON + CSV)
python btc_onchain.py --save

# 종합 신호 한 줄만
python btc_onchain.py --quiet

# ANSI 색상 끄기
python btc_onchain.py --no-color
```

## 📁 저장 구조 (`--save` 사용 시)

```
btc_data/
├── btc_20250602T124500Z.json   # 시점별 스냅샷
├── btc_20250603T090500Z.json
└── btc_timeseries.csv          # 핵심 지표 시계열 (1행/실행)
```

## ⏰ 자동화 예시 (매일 09:05 KST)

**Linux crontab:**
```
5 0 * * *  /usr/bin/python3 /path/to/btc_onchain.py --save
```

**Windows 작업 스케줄러:**
```
python C:\path\to\btc_onchain.py --save
```

## ⚠️ 면책

본 스크립트의 '신호/해석'은 통계적 참고용이며 **투자 자문이 아닙니다**.

## 📋 요구사항

- Python 3.7+
- 인터넷 연결
