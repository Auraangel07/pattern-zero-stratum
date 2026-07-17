# ═══════════════════════════════════════════
# PATTERN ZERO — Stocks API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/{symbol}/latest")
def get_latest_price(symbol: str):
    """
    Get the most recent price for a symbol.
    """
    symbol = symbol.upper()
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT symbol, time, open, high, low,
                   close, volume, source
            FROM stock_prices
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
def get_price_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get historical prices for a symbol,
    default last 30 days.
    """
    symbol = symbol.upper()
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT symbol, time, open, high, low,
                   close, volume
            FROM stock_prices
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