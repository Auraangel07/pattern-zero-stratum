# ═══════════════════════════════════════════
# PATTERN ZERO — Crypto API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/crypto", tags=["Crypto"])

@router.get("/{symbol}/latest")
def get_latest_crypto_price(symbol: str):
    symbol = symbol.upper()
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT symbol, time, open, high, low,
                   close, volume, market_cap, source
            FROM crypto_prices
            WHERE symbol = :symbol
            ORDER BY time DESC
            LIMIT 1
        """), {"symbol": symbol}).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for symbol '{symbol}'"
        )

    return dict(result)

@router.get("/{symbol}/history")
def get_crypto_history(
    symbol: str,
    days: int = Query(default=7, ge=1, le=365)
):
    symbol = symbol.upper()
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT symbol, time, open, high, low,
                   close, volume
            FROM crypto_prices
            WHERE symbol = :symbol
              AND time >= NOW() - (:days || ' days')::interval
            ORDER BY time DESC
        """), {"symbol": symbol, "days": days}).mappings().all()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for symbol '{symbol}'"
        )

    return {
        "symbol": symbol,
        "days": days,
        "count": len(result),
        "data": [dict(row) for row in result]
    }