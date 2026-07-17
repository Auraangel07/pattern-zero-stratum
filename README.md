# Pattern Zero — STRATUM

**Module I of Pattern Zero** — an automated, multi-asset-class financial data infrastructure. STRATUM ingests equities, ETFs, cryptocurrency, and macroeconomic indicators on independent schedules, stores them in a time-series-optimized Postgres database, and serves them through a REST API — fully containerized, self-healing, and audit-logged.

> *"Complexity is not chaos. It is unread data."*

---

## What it does

STRATUM is the data foundation layer for Pattern Zero, a broader financial AI research ecosystem. It answers one question reliably, every hour: **is the data fresh, correct, and reachable?**

- 📈 **Equities & ETFs** — US and Indian markets (AAPL, MSFT, GOOGL, RELIANCE.NS, TCS.NS, and more), plus SPY/QQQ/GLD, refreshed twice daily
- 🪙 **Cryptocurrency** — BTC, ETH, SOL, BNB, XRP, refreshed hourly (crypto never sleeps, so neither does this pipeline)
- 🏛️ **Macroeconomic indicators** — GDP, CPI, Fed funds rate, unemployment, 10Y Treasury yield via FRED, refreshed weekly
- 🌐 **REST API** — every dataset above is queryable over HTTP, with interactive auto-generated docs
- 🔍 **Full audit trail** — every pipeline run (success, partial, or failure) is logged with fetch/insert counts and error messages

## Tech stack

![Python](https://img.shields.io/badge/Python-3.8-3776AB?style=flat&logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache_Airflow-2.8.0-017CEE?style=flat&logo=apacheairflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/TimescaleDB-PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4-D71F00?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?style=flat&logo=fastapi&logoColor=white)

## Architecture

```
Yahoo Finance / FRED API
          │
          ▼
  Ingestion Layer (Python)
  stocks.py · crypto.py · macro.py
          │
          ▼
  Orchestration (Apache Airflow)
  stratum_stocks (2x/day) · stratum_crypto (hourly) · stratum_macro (weekly)
          │
          ▼
  Storage (TimescaleDB / PostgreSQL)
  stock_prices · crypto_prices · macro_indicators
  symbols_registry · pipeline_logs
          │
          ▼
  Market API (FastAPI)
  /stocks · /crypto · /macro · /symbols · /pipeline
          │
          ▼
     External consumers
  (dashboards, notebooks, future Pattern Zero modules)
```

All five services (TimescaleDB, Airflow, Redis, pgAdmin, API) run as isolated Docker containers via a single `docker-compose.yml`.

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
| `GET /symbols` | Every symbol currently tracked, filterable by asset type |
| `GET /pipeline/status` | Latest run status per ingestion pipeline |
| `GET /pipeline/history/{pipeline_name}` | Recent run history for a specific pipeline |

## Key design decisions

- **Upsert-safe ingestion** — every insert uses `ON CONFLICT ... DO UPDATE`, making every pipeline run idempotent and safely re-triggerable without duplicating data
- **Asset-class-specific schedules** — crypto (24/7 markets) refreshes hourly; equities (session-based) refresh twice daily; macro indicators (monthly/quarterly releases) refresh weekly — no wasted API calls, no stale data
- **Full observability** — a dedicated `pipeline_logs` table means pipeline health is queryable, not just visible in a UI, and is itself exposed via the API
- **API decoupled from ingestion** — the FastAPI layer only reads from the database; it never writes, keeping ingestion and serving concerns fully separated

## Running it locally

```bash
git clone https://github.com/Auraangel07/pattern-zero-stratum.git
cd pattern-zero-stratum/docker

# Add your FRED API key and DB credentials
cp .env.example .env

docker-compose up -d --build
```

Then:
- Airflow UI → `localhost:8080`
- pgAdmin → `localhost:5050`
- Market API (interactive docs) → `localhost:8000/docs`

Trigger any DAG manually from the Airflow UI, or let the schedules run on their own. Query live data immediately via the API, e.g. `localhost:8000/stocks/AAPL/latest`.

## Project Status

**Project 01 — Financial Data Lake + Market API: complete.** Ingestion, orchestration, storage, and API layer are all running end-to-end with zero active failures.

STRATUM (Module I) also includes two additional planned projects before the module is fully sealed:
- **Project 02 — Market Observatory**: a live dashboard reading from this API
- **Project 03 — Alternative Data Pipeline**: news sentiment, SEC filings, and other non-price data sources

## Roadmap

STRATUM is Project 01 of Module I in the Pattern Zero ecosystem. Next: **Market Observatory** (Project 02) and an **Alternative Data Pipeline** (Project 03), before moving to Module II — THE CALCULUS.

---

*Built as part of Pattern Zero — an independent financial AI research project.*