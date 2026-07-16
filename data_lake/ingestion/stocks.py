# ═══════════════════════════════════════════
# PATTERN ZERO — Stock Price Ingestion
# MODULE I: STRATUM
# "Every tick. Every day. Every market."
# ═══════════════════════════════════════════

import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import text
import sys
import os

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from data_lake.storage.db_connection import get_engine

# ───────────────────────────────────────────
# SYMBOLS — The universe we watch
# ───────────────────────────────────────────
SYMBOLS = {
    # US Markets
    "AAPL":  "Apple Inc",
    "MSFT":  "Microsoft Corporation",
    "GOOGL": "Alphabet Inc",
    "AMZN":  "Amazon.com Inc",
    "NVDA":  "NVIDIA Corporation",
    "META":  "Meta Platforms Inc",
    "TSLA":  "Tesla Inc",

    # Indian Markets
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS":      "Tata Consultancy Services",
    "INFY.NS":     "Infosys Limited",
    "HDFCBANK.NS": "HDFC Bank",
    "WIPRO.NS":    "Wipro Limited",

    # ETFs
    "SPY":  "S&P 500 ETF",
    "QQQ":  "NASDAQ 100 ETF",
    "GLD":  "Gold ETF",
}

def register_symbols(engine):
    """
    Register all symbols in the
    symbols_registry table.
    """
    print("📋 Registering symbols...")

    with engine.begin() as conn:
        for symbol, name in SYMBOLS.items():
            conn.execute(text("""
                INSERT INTO symbols_registry
                    (symbol, name, asset_type)
                VALUES
                    (:symbol, :name, 'STOCK')
                ON CONFLICT (symbol)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW()
            """), {"symbol": symbol, "name": name})

    print(f"✅ {len(SYMBOLS)} symbols registered")

def fetch_stock_prices(symbol: str,
                       period: str = "5d",
                       interval: str = "1d"):
    """
    Fetch stock prices from Yahoo Finance.

    period:   1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            period=period,
            interval=interval
        )

        if df.empty:
            print(f"⚠️  No data for {symbol}")
            return None

        # Clean and format
        df = df.reset_index()
        df['symbol'] = symbol
        df['source'] = 'yahoo_finance'

        # Rename columns to match schema
        df = df.rename(columns={
            'Datetime': 'time',
            'Date':     'time',
            'Open':     'open',
            'High':     'high',
            'Low':      'low',
            'Close':    'close',
            'Volume':   'volume',
        })

        # Select only schema columns
        df = df[[
            'time', 'symbol', 'open',
            'high', 'low', 'close',
            'volume', 'source'
        ]]

        # Ensure timezone aware
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize(
                'UTC'
            )
        else:
            df['time'] = df['time'].dt.tz_convert(
                'UTC'
            )

        return df

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


def insert_stock_prices(df: pd.DataFrame, engine) -> int:
    """
    Upsert stock prices into TimescaleDB.
    Uses ON CONFLICT to handle re-runs safely —
    updates existing (symbol, time) rows instead
    of crashing or duplicating.
    """
    if df is None or df.empty:
        return 0

    inserted = 0
    try:
        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO stock_prices
                        (time, symbol, open, high, low, close, volume, source)
                    VALUES
                        (:time, :symbol, :open, :high, :low, :close, :volume, :source)
                    ON CONFLICT (symbol, time)
                    DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """), {
                    "time":   row['time'],
                    "symbol": row['symbol'],
                    "open":   float(row['open']),
                    "high":   float(row['high']),
                    "low":    float(row['low']),
                    "close":  float(row['close']),
                    "volume": int(row['volume']),
                    "source": row['source'],
                })
                inserted += 1
        return inserted

    except Exception as e:
        print(f"❌ Insert error: {e}")
        return 0
    
def log_pipeline(engine,
                 pipeline_name: str,
                 status: str,
                 records_fetched: int = 0,
                 records_inserted: int = 0,
                 error_message: str = None):
    """
    Log pipeline execution to pipeline_logs.
    Pattern Zero tracks everything.
    """
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_logs
                (pipeline_name, status,
                 records_fetched,
                 records_inserted,
                 error_message,
                 completed_at)
            VALUES
                (:name, :status,
                 :fetched,
                 :inserted,
                 :error,
                 NOW())
        """), {
            "name":     pipeline_name,
            "status":   status,
            "fetched":  records_fetched,
            "inserted": records_inserted,
            "error":    error_message
        })

def run_stock_ingestion(period: str = "5d"):
    """
    Main ingestion function.
    Pulls all symbols and stores in DB.
    """
    print("═" * 50)
    print("PATTERN ZERO — Stock Ingestion")
    print(f"Time: {datetime.now()}")
    print(f"Symbols: {len(SYMBOLS)}")
    print(f"Period: {period}")
    print("═" * 50)

    engine = get_engine()

    # Register symbols first
    register_symbols(engine)

    total_fetched = 0
    total_inserted = 0
    failed = []

    for symbol in SYMBOLS:
        print(f"\n📈 Fetching {symbol}...")

        # Fetch from Yahoo Finance
        df = fetch_stock_prices(symbol, period)

        if df is not None:
            records = len(df)
            inserted = insert_stock_prices(
                df, engine
            )

            total_fetched += records
            total_inserted += inserted

            print(f"   ✅ {inserted} records inserted")
        else:
            failed.append(symbol)

    # Log the pipeline run
    status = "SUCCESS" if not failed else "PARTIAL"
    log_pipeline(
        engine,
        pipeline_name="stock_ingestion",
        status=status,
        records_fetched=total_fetched,
        records_inserted=total_inserted,
        error_message=str(failed) if failed else None
    )

    print("\n" + "═" * 50)
    print(f"✅ COMPLETE")
    print(f"   Fetched:  {total_fetched} records")
    print(f"   Inserted: {total_inserted} records")
    if failed:
        print(f"   Failed:   {failed}")
    print("═" * 50)

if __name__ == "__main__":
    run_stock_ingestion(period="1mo")