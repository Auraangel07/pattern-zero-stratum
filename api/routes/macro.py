# ═══════════════════════════════════════════
# PATTERN ZERO — Macro Indicators API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/macro", tags=["Macro"])

@router.get("/{indicator}")
def get_macro_indicator(
    indicator: str,
    country: str = Query(default="US")
):
    """
    Get the latest value for a macro indicator,
    e.g. GDP, CPI, UNEMPLOYMENT
    """
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT indicator, country, time, value,
                   unit, frequency, source
            FROM macro_indicators
            WHERE indicator = :indicator
              AND country = :country
            ORDER BY time DESC
            LIMIT 1
        """), {
            "indicator": indicator,
            "country": country
        }).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No data for indicator '{indicator}' in '{country}'"
        )

    return dict(result)

@router.get("/{indicator}/history")
def get_macro_history(
    indicator: str,
    country: str = Query(default="US"),
    limit: int = Query(default=20, ge=1, le=200)
):
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT indicator, country, time, value, unit
            FROM macro_indicators
            WHERE indicator = :indicator
              AND country = :country
            ORDER BY time DESC
            LIMIT :limit
        """), {
            "indicator": indicator,
            "country": country,
            "limit": limit
        }).mappings().all()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No data for indicator '{indicator}' in '{country}'"
        )

    return {
        "indicator": indicator,
        "country": country,
        "count": len(result),
        "data": [dict(row) for row in result]
    }