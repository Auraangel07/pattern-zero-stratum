# Pattern Zero — STRATUM

**Module I of Pattern Zero: automated financial data infrastructure**

> "Complexity is not chaos. It is unread data."

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/TimescaleDB-PostgreSQL%2014-336791?logo=postgresql&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8.0-017CEE?logo=apacheairflow&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## What This Is

STRATUM is a fully automated, self-healing financial data pipeline that
collects stock, crypto, and macroeconomic data on a recurring schedule
and stores it in a time-series-optimized database — with zero manual
intervention required after setup.

This is Project 01 of Pattern Zero's Module I. Two more projects
(a live observatory dashboard and an alternative-data pipeline) are
planned to complete the module.

## Architecture

```
Yahoo Finance / FRED / Crypto APIs
              │
              ▼
      Apache Airflow (orchestration)
   stratum_stocks · stratum_macro · stratum_crypto
              │
              ▼
   Python ingestion scripts (SQLAlchemy)
   fetch → clean → upsert → log
              │
              ▼
        TimescaleDB (PostgreSQL)
   8 hypertables, fully indexed
              │
       ┌──────┴──────┐
       ▼             ▼
    Redis         pgAdmin
   (cache)      (DB admin UI)
```

All components run as isolated Docker containers, orchestrated via a
single `docker-compose.yml`.

## Tech Stack & Why

| Tool | Role | Why |
|---|---|---|
| **TimescaleDB** | Time-series database | PostgreSQL + automatic time-based partitioning for fast queries at scale |
| **Apache Airflow** | Pipeline orchestration | Industry-standard scheduling, retries, and run history — not a silent cron job |
| **Redis** | Cache layer | Fast repeated reads for future API/dashboard layer |
| **pgAdmin** | Database GUI | Visual inspection and debugging |
| **Docker Compose** | Containerization | Reproducible, isolated, one-command environment |
| **SQLAlchemy** | DB connectivity | Connection pooling + transactional safety (`engine.begin()`) |

## Database Schema

8 tables, all TimescaleDB hypertables:

- `stock_prices` — OHLCV data per symbol
- `crypto_prices` — OHLCV + market cap
- `macro_indicators` — GDP, inflation, rates (generic schema, any country/indicator)
- `forex_rates` — currency pairs
- `commodities` — oil, gold, silver
- `news_sentiment` — headline + sentiment (for future NLP integration)
- `symbols_registry` — master metadata for every tracked symbol
- `pipeline_logs` — full audit trail of every ingestion run

## Pipelines

| DAG | Schedule | Source |
|---|---|---|
| `stratum_stocks` | Twice daily | Yahoo Finance |
| `stratum_crypto` | Hourly | Crypto API |
| `stratum_macro` | Weekly | FRED API |

Every run is idempotent (safe to re-run without creating duplicates) and
logged to `pipeline_logs` with record counts and status.

## Running Locally

```bash
git clone https://github.com/Auraangel07/pattern-zero-stratum.git
cd pattern-zero-stratum/docker
cp .env.example .env   # fill in your own credentials
docker-compose up -d
```

Access:
- Airflow: `localhost:8080`
- pgAdmin: `localhost:5050`
- TimescaleDB: `localhost:5432`

## Project Status

Project 01 (this repo's current scope) is stable and running
end-to-end with zero active failures. Module I (STRATUM) also includes
two planned additional projects — a live dashboard and an alternative
data pipeline — not yet built.

## Author

Aurelia — Quantitative AI research portfolio, "Pattern Zero"