# ═══════════════════════════════════════════
# PATTERN ZERO — Crypto Price Ingestion
# MODULE I: STRATUM
# "No open hours. No holidays. Just chaos, ticking."
# ═══════════════════════════════════════════

import yfinance as yf
import pandas as pd
from datetime import datetime
from sqlalchemy import text
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from data_lake.storage.db_connection import get_engine

# ───────────────────────────────────────────
# SYMBOLS — The chaos we track
# ───────────────────────────────────────────
SYMBOLS = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "BNB-USD": "Binance Coin",
    "XRP-USD": "XRP",
}


def register_symbols(engine):
    print("📋 Registering crypto symbols...")

    with engine.begin() as conn:
        for symbol, name in SYMBOLS.items():
            conn.execute(text("""
                INSERT INTO symbols_registry
                    (symbol, name, asset_type)
                VALUES
                    (:symbol, :name, 'CRYPTO')
                ON CONFLICT (symbol)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW()
            """), {"symbol": symbol, "name": name})

    print(f"✅ {len(SYMBOLS)} symbols registered")


def fetch_crypto_prices(symbol: str, period: str = "1mo", interval: str = "1d"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            print(f"⚠️  No data for {symbol}")
            return None

        df = df.reset_index()
        df['symbol'] = symbol
        df['source'] = 'yahoo_finance'

        df = df.rename(columns={
            'Datetime': 'time',
            'Date':     'time',
            'Open':     'open',
            'High':     'high',
            'Low':      'low',
            'Close':    'close',
            'Volume':   'volume',
        })

        df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'source']]

        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
        else:
            df['time'] = df['time'].dt.tz_convert('UTC')

        return df

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def insert_crypto_prices(df: pd.DataFrame, engine) -> int:
    """
    Upsert crypto prices into TimescaleDB.
    Uses ON CONFLICT to handle re-runs safely.
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


def run_crypto_ingestion(period: str = "1mo"):
    print("═" * 50)
    print("PATTERN ZERO — Crypto Ingestion")
    print(f"Time: {datetime.now()}")
    print(f"Symbols: {len(SYMBOLS)}")
    print(f"Period: {period}")
    print("═" * 50)

    engine = get_engine()
    register_symbols(engine)

    total_fetched = 0
    total_inserted = 0
    failed = []

    for symbol in SYMBOLS:
        print(f"\n🪙 Fetching {symbol}...")
        df = fetch_crypto_prices(symbol, period)

        if df is not None:
            records = len(df)
            inserted = insert_crypto_prices(df, engine)

            total_fetched += records
            total_inserted += inserted

            print(f"   ✅ {inserted} records inserted")
        else:
            failed.append(symbol)

    status = "SUCCESS" if not failed else "PARTIAL"
    log_pipeline(
        engine,
        pipeline_name="crypto_ingestion",
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
    run_crypto_ingestion(period="1mo")