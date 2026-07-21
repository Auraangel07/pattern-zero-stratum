# ═══════════════════════════════════════════
# PATTERN ZERO — SEC Filings Ingestion
# MODULE I: STRATUM · PROJECT 03
# ═══════════════════════════════════════════

import os
import sys
import requests
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from data_lake.storage.db_connection import get_engine

# ───────────────────────────────────────────
# SYMBOLS — CIK numbers (SEC's internal IDs)
# ───────────────────────────────────────────
SYMBOL_CIK = {
    "AAPL":  "0000320193",
    "MSFT":  "0000789019",
    "GOOGL": "0001652044",
    "AMZN":  "0001018724",
    "NVDA":  "0001045810",
    "META":  "0001326801",
    "TSLA":  "0001318605",
}

HEADERS = {
    "User-Agent": "Pattern Zero Research aura@patternzero.io"
}


def fetch_filings_for_symbol(symbol: str, cik: str, limit: int = 5):
    """
    Fetch recent filings (10-K, 10-Q) for a company
    from SEC EDGAR's submissions API.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        company_name = data.get("name", symbol)

        filings = []
        for form, date, accession in zip(forms, dates, accessions):
            if form in ("10-K", "10-Q"):
                filings.append({
                    "form": form,
                    "date": date,
                    "accession": accession,
                    "company_name": company_name
                })
            if len(filings) >= limit:
                break

        return filings

    except Exception as e:
        print(f"❌ Error fetching filings for {symbol}: {e}")
        return []


def insert_filings(engine, symbol: str, filings: list) -> int:
    if not filings:
        return 0

    inserted = 0
    with engine.begin() as conn:
        for f in filings:
            accession_clean = f["accession"]
            accession_no_dashes = accession_clean.replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{SYMBOL_CIK[symbol].lstrip('0')}/{accession_no_dashes}/"
                f"{accession_clean}-index.htm"
            )

            try:
                conn.execute(text("""
                    INSERT INTO sec_filings
                        (symbol, company_name, filing_type,
                         filing_date, accession_number, url)
                    VALUES
                        (:symbol, :company_name, :filing_type,
                         :filing_date, :accession_number, :url)
                    ON CONFLICT (accession_number) DO NOTHING
                """), {
                    "symbol": symbol,
                    "company_name": f["company_name"],
                    "filing_type": f["form"],
                    "filing_date": f["date"],
                    "accession_number": f["accession"],
                    "url": filing_url,
                })
                inserted += 1
            except Exception as e:
                print(f"❌ Insert error for {symbol}: {e}")
                continue

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
            "name": pipeline_name,
            "status": status,
            "fetched": records_fetched,
            "inserted": records_inserted,
            "error": error_message
        })


def run_filings_ingestion():
    print("═" * 50)
    print("PATTERN ZERO — SEC Filings Ingestion")
    print(f"Time: {datetime.now()}")
    print(f"Symbols: {len(SYMBOL_CIK)}")
    print("═" * 50)

    engine = get_engine()
    total_fetched = 0
    total_inserted = 0
    failed = []

    for symbol, cik in SYMBOL_CIK.items():
        print(f"\n📄 Fetching filings for {symbol}...")
        filings = fetch_filings_for_symbol(symbol, cik)

        if filings:
            fetched = len(filings)
            inserted = insert_filings(engine, symbol, filings)

            total_fetched += fetched
            total_inserted += inserted

            print(f"   ✅ {inserted}/{fetched} filings inserted")
        else:
            failed.append(symbol)

    status = "SUCCESS" if not failed else "PARTIAL"
    log_pipeline(
        engine,
        pipeline_name="filings_ingestion",
        status=status,
        records_fetched=total_fetched,
        records_inserted=total_inserted,
        error_message=str(failed) if failed else None
    )

    print("\n" + "═" * 50)
    print("✅ COMPLETE")
    print(f"   Fetched:  {total_fetched} filings")
    print(f"   Inserted: {total_inserted} filings")
    if failed:
        print(f"   Failed:   {failed}")
    print("═" * 50)


if __name__ == "__main__":
    run_filings_ingestion()