# ═══════════════════════════════════════════
# PATTERN ZERO — News Sentiment Ingestion
# MODULE I: STRATUM · PROJECT 03
# "Where you stop being basic."
# ═══════════════════════════════════════════

import os
import requests
from datetime import datetime, timezone
from sqlalchemy import text
import sys

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from data_lake.storage.db_connection import get_engine

# ───────────────────────────────────────────
# SYMBOLS + SEARCH TERMS
# NewsAPI searches by keyword, not ticker —
# so we map tickers to company names
# ───────────────────────────────────────────
SYMBOL_SEARCH_TERMS = {
    "AAPL":  "Apple Inc",
    "MSFT":  "Microsoft",
    "GOOGL": "Google OR Alphabet",
    "AMZN":  "Amazon",
    "NVDA":  "Nvidia",
    "META":  "Meta Platforms",
    "TSLA":  "Tesla",
}

NEWSAPI_URL = "https://newsapi.org/v2/everything"

def fetch_news_for_symbol(symbol: str, search_term: str,
                          api_key: str, page_size: int = 5):
    """
    Fetch recent news headlines for a symbol
    from NewsAPI.
    """
    try:
        response = requests.get(
            NEWSAPI_URL,
            params={
                "q": search_term,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"⚠️  NewsAPI error for {symbol}: {data}")
            return []

        return data.get("articles", [])

    except Exception as e:
        print(f"❌ Error fetching news for {symbol}: {e}")
        return []

def insert_news(engine, symbol: str, articles: list) -> int:
    """
    Insert news articles into news_sentiment table.
    Uses ON CONFLICT (url, time) to handle re-runs safely.
    """
    inserted = 0

    with engine.begin() as conn:
        for article in articles:
            try:
                published = article.get("publishedAt")
                pub_time = (
                    datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if published else datetime.now(timezone.utc)
                )

                result = conn.execute(text("""
                    INSERT INTO news_sentiment
                        (time, headline, source, url, symbols, summary)
                    VALUES
                        (:time, :headline, :source, :url, :symbols, :summary)
                    ON CONFLICT (url, time) DO NOTHING
                """), {
                    "time": pub_time,
                    "headline": article.get("title", "")[:500],
                    "source": article.get("source", {}).get("name", "unknown"),
                    "url": article.get("url"),
                    "symbols": [symbol],
                    "summary": (article.get("description") or "")[:1000]
                })

                if result.rowcount > 0:
                    inserted += 1

            except Exception as e:
                print(f"❌ Insert error for article: {e}")
                continue

    return inserted

def log_pipeline(engine, pipeline_name: str, status: str,
                 records_fetched: int = 0,
                 records_inserted: int = 0,
                 error_message: str = None):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_logs
                (pipeline_name, status, records_fetched,
                 records_inserted, error_message, completed_at)
            VALUES
                (:name, :status, :fetched, :inserted,
                 :error, NOW())
        """), {
            "name": pipeline_name,
            "status": status,
            "fetched": records_fetched,
            "inserted": records_inserted,
            "error": error_message
        })

def run_news_ingestion():
    print("═" * 50)
    print("PATTERN ZERO — News Ingestion")
    print(f"Time: {datetime.now()}")
    print(f"Symbols: {len(SYMBOL_SEARCH_TERMS)}")
    print("═" * 50)

    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY not set in environment")

    engine = get_engine()
    total_fetched = 0
    total_inserted = 0
    failed = []

    for symbol, search_term in SYMBOL_SEARCH_TERMS.items():
        print(f"\n📰 Fetching news for {symbol}...")

        articles = fetch_news_for_symbol(symbol, search_term, api_key)

        if articles:
            fetched = len(articles)
            inserted = insert_news(engine, symbol, articles)

            total_fetched += fetched
            total_inserted += inserted

            print(f"   ✅ {inserted}/{fetched} articles inserted")
        else:
            failed.append(symbol)

    status = "SUCCESS" if not failed else "PARTIAL"
    log_pipeline(
        engine,
        pipeline_name="news_ingestion",
        status=status,
        records_fetched=total_fetched,
        records_inserted=total_inserted,
        error_message=str(failed) if failed else None
    )

    print("\n" + "═" * 50)
    print(f"✅ COMPLETE")
    print(f"   Fetched:  {total_fetched} articles")
    print(f"   Inserted: {total_inserted} articles")
    if failed:
        print(f"   Failed:   {failed}")
    print("═" * 50)

if __name__ == "__main__":
    run_news_ingestion()