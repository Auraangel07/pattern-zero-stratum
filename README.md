# Pattern Zero — STRATUM

**Module I of Pattern Zero** — an automated, multi-asset-class financial data infrastructure. STRATUM ingests equities, ETFs, cryptocurrency, macroeconomic indicators, news sentiment, and SEC filings on independent schedules, stores them in a time-series-optimized Postgres database, and serves them through a REST API — fully containerized, self-healing, and audit-logged.

> *"Complexity is not chaos. It is unread data."*

---

## What it does

STRATUM is the data foundation layer for Pattern Zero, a broader financial AI research ecosystem. It answers one question reliably, every hour: **is the data fresh, correct, and reachable?**

- 📈 **Equities & ETFs** — US and Indian markets (AAPL, MSFT, GOOGL, RELIANCE.NS, TCS.NS, and more), plus SPY/QQQ/GLD, refreshed twice daily
- 🪙 **Cryptocurrency** — BTC, ETH, SOL, BNB, XRP, refreshed hourly (crypto never sleeps, so neither does this pipeline)
- 🏛️ **Macroeconomic indicators** — GDP, CPI, Fed funds rate, unemployment, 10Y Treasury yield via FRED, refreshed weekly
- 🗞️ **News sentiment** — recent headlines per tracked symbol via NewsAPI, refreshed daily
- 📄 **SEC filings** — 10-K/10-Q filing metadata via SEC EDGAR, refreshed daily
- 🌐 **REST API** — every dataset above is queryable over HTTP, with interactive auto-generated docs
- 🔍 **Full audit trail** — every pipeline run (success, partial, or failure) is logged with fetch/insert counts and error messages

## Tech stack

![Python](https://img.shields.io/badge/Python-3.8-3776AB?style=flat&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-2.8.0-017CEE?style=flat&logo=apacheairflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/TimescaleDB-PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Neon](https://img.shields.io/badge/Neon-Serverless_Postgres-00E599?style=flat&logo=neon&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4-D71F00?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?style=flat&logo=fastapi&logoColor=white)

## Architecture

Yahoo Finance / FRED / NewsAPI / SEC EDGAR
│
▼
Ingestion Layer (Python)
stocks.py · crypto.py · macro.py · news.py · filings.py
│
▼
Orchestration (Apache Airflow)
stratum_stocks (2x/day) · stratum_crypto (hourly)
stratum_macro (weekly) · stratum_news (daily) · stratum_filings (daily)
│
▼
Storage (TimescaleDB / Neon Postgres)
stock_prices · macro_indicators · news_sentiment · sec_filings
symbols_registry · pipeline_logs
│
▼
Market API (FastAPI)
/stocks · /crypto · /macro · /news · /filings · /symbols · /pipeline
│
▼
External consumers
(Market Observatory dashboard, notebooks, future Pattern Zero modules)


All ingestion and orchestration services (TimescaleDB, Airflow, Redis, pgAdmin, API) run as isolated Docker containers via a single `docker-compose.yml`. Production data is hosted on Neon (serverless Postgres), which both the ingestion pipelines and the Observatory dashboard read from and write to.

## API Endpoints

Interactive docs available at `/docs` once running (Swagger UI, auto-generated from the code — nothing hand-written or hand-maintained).

| Endpoint | Description |
|---|---|
| `GET /stocks/{symbol}/latest` | Most recent price for a symbol |
| `GET /stocks/{symbol}/history?days=N` | Historical prices, configurable window |
| `GET /crypto/{symbol}/latest` | Most recent crypto price |
| `GET /crypto/{symbol}/history?days=N` | Historical crypto prices |
| `GET /macro/{indicator}?country=US` | Latest value for a macro indicator |
| `GET /macro/{indicator}/history` | Historical values for a macro indicator |
| `GET /news/{symbol}` | Recent headlines for a symbol |
| `GET /filings/{symbol}` | Recent SEC filings for a symbol |
| `GET /symbols` | Every symbol currently tracked, filterable by asset type |
| `GET /pipeline/status` | Latest run status per ingestion pipeline |
| `GET /pipeline/history/{pipeline_name}` | Recent run history for a specific pipeline |

## Key design decisions

- **Upsert-safe ingestion** — every insert uses `ON CONFLICT ... DO UPDATE` (or `DO NOTHING` for append-only sources like news), making every pipeline run idempotent and safely re-triggerable without duplicating data
- **Asset-class-specific schedules** — crypto (24/7 markets) refreshes hourly; equities (session-based) refresh twice daily; macro indicators (monthly/quarterly releases) refresh weekly; news and filings refresh daily — no wasted API calls, no stale data
- **TimescaleDB hypertable constraints** — unique constraints on time-partitioned tables must include the partitioning column itself (e.g. `UNIQUE(url, time)` rather than `UNIQUE(url)`) — a real constraint of hypertable design, not a workaround
- **Full observability** — a dedicated `pipeline_logs` table means pipeline health is queryable, not just visible in a UI, and is itself exposed via the API
- **API decoupled from ingestion** — the FastAPI layer only reads from the database; it never writes, keeping ingestion and serving concerns fully separated
- **Respectful of upstream sources** — SEC EDGAR requires a real, identifying `User-Agent` header per their access policy; this isn't optional boilerplate, it's honored explicitly in `filings.py`

## Running it locally

```bash
git clone https://github.com/Auraangel07/pattern-zero-stratum.git
cd pattern-zero-stratum/docker

# Add your FRED/NewsAPI keys and DB credentials
cp .env.example .env

docker-compose up -d --build
```

Then:
- Airflow UI → `localhost:8080`
- pgAdmin → `localhost:5050`
- Market API (interactive docs) → `localhost:8000/docs`

Trigger any DAG manually from the Airflow UI, or let the schedules run on their own. Query live data immediately via the API, e.g. `localhost:8000/stocks/AAPL/latest`.

## Project Status

**All three Module I projects are complete:**

- **Project 01 — Financial Data Lake + Market API**: ingestion, orchestration, storage, and API layer running end-to-end with zero active failures
- **Project 02 — Market Observatory**: live multi-page dashboard reading from this data ([see repo](https://github.com/Auraangel07/pattern-zero-observatory))
- **Project 03 — Alternative Data Pipeline**: news sentiment and SEC filings ingestion, fully integrated into the same orchestration and API layer

## Roadmap

Module I (STRATUM) is sealed. Next: **Module II — THE CALCULUS.**

---

*Built as part of Pattern Zero — an independent financial AI research project.*