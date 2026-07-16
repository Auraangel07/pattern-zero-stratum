# ═══════════════════════════════════════════
# PATTERN ZERO — Macro Indicator Ingestion
# MODULE I: STRATUM
# "GDP. Inflation. Rates. The forces behind the ticks."
# ═══════════════════════════════════════════

import os
import sys
from datetime import datetime
from fredapi import Fred
from dotenv import load_dotenv
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from data_lake.storage.db_connection import get_engine

load_dotenv()

# ───────────────────────────────────────────
# SERIES — The macro forces we track
# FRED series_id : metadata
# ───────────────────────────────────────────
SERIES = {
    "GDP": {
        "indicator": "Gross Domestic Product",
        "country":   "US",
        "unit":      "Billions of Dollars",
        "frequency": "Quarterly",
    },
    "CPIAUCSL": {
        "indicator": "Consumer Price Index",
        "country":   "US",
        "unit":      "Index 1982-84=100",
        "frequency": "Monthly",
    },
    "FEDFUNDS": {
        "indicator": "Federal Funds Rate",
        "country":   "US",
        "unit":      "Percent",
        "frequency": "Monthly",
    },
    "UNRATE": {
        "indicator": "Unemployment Rate",
        "country":   "US",
        "unit":      "Percent",
        "frequency": "Monthly",
    },
    "DGS10": {
        "indicator": "10-Year Treasury Yield",
        "country":   "US",
        "unit":      "Percent",
        "frequency": "Daily",
    },
}


def get_fred_client():
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY not found in .env")
    return Fred(api_key=api_key)


def fetch_series(fred, series_id: str):
    """
    Fetch a single macro series from FRED.
    Returns a pandas Series indexed by date.
    """
    try:
        data = fred.get_series(series_id)
        if data is None or data.empty:
            print(f"⚠️  No data for {series_id}")
            return None
        return data
    except Exception as e:
        print(f"❌ Error fetching {series_id}: {e}")
        return None


def insert_series(engine, series_id: str, meta: dict, data) -> int:
    """
    Insert/update a macro series into macro_indicators.
    Uses upsert on (indicator, time, country) to handle
    FRED revisions safely.
    """
    if data is None or data.empty:
        return 0

    inserted = 0
    with engine.begin() as conn:
        for date, value in data.items():
            if value is None or str(value) == "nan":
                continue
            conn.execute(text("""
                INSERT INTO macro_indicators
                    (time, indicator, country, value,
                     unit, frequency, source)
                VALUES
                    (:time, :indicator, :country, :value,
                     :unit, :frequency, 'fred')
                ON CONFLICT (indicator, time, country)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    unit = EXCLUDED.unit,
                    frequency = EXCLUDED.frequency
            """), {
                "time":      date.to_pydatetime(),
                "indicator": meta["indicator"],
                "country":   meta["country"],
                "value":     float(value),
                "unit":      meta["unit"],
                "frequency": meta["frequency"],
            })
            inserted += 1

    return inserted


def log_pipeline(engine, pipeline_name: str, status: str,
                  records_fetched: int = 0, records_inserted: int = 0,
                  error_message: str = None):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_logs
                (pipeline_name, status, records_fetched,
                 records_inserted, error_message, completed_at)
            VALUES
                (:name, :status, :fetched, :inserted, :error, NOW())
        """), {
            "name":     pipeline_name,
            "status":   status,
            "fetched":  records_fetched,
            "inserted": records_inserted,
            "error":    error_message
        })


def run_macro_ingestion():
    print("═" * 50)
    print("PATTERN ZERO — Macro Ingestion")
    print(f"Time: {datetime.now()}")
    print(f"Series: {len(SERIES)}")
    print("═" * 50)

    fred = get_fred_client()
    engine = get_engine()

    total_fetched = 0
    total_inserted = 0
    failed = []

    for series_id, meta in SERIES.items():
        print(f"\n📊 Fetching {series_id} ({meta['indicator']})...")
        data = fetch_series(fred, series_id)

        if data is not None:
            fetched = len(data)
            inserted = insert_series(engine, series_id, meta, data)

            total_fetched += fetched
            total_inserted += inserted

            print(f"   ✅ {inserted} records inserted/updated")
        else:
            failed.append(series_id)

    status = "SUCCESS" if not failed else "PARTIAL"
    log_pipeline(
        engine,
        pipeline_name="macro_ingestion",
        status=status,
        records_fetched=total_fetched,
        records_inserted=total_inserted,
        error_message=str(failed) if failed else None
    )

    print("\n" + "═" * 50)
    print("✅ COMPLETE")
    print(f"   Fetched:  {total_fetched} records")
    print(f"   Inserted: {total_inserted} records")
    if failed:
        print(f"   Failed:   {failed}")
    print("═" * 50)


if __name__ == "__main__":
    run_macro_ingestion()