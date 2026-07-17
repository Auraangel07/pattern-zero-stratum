# ═══════════════════════════════════════════
# PATTERN ZERO — Symbols Registry API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/symbols", tags=["Symbols"])

@router.get("/")
def list_symbols(asset_type: str = None):
    """
    List every symbol Pattern Zero is tracking.
    Optionally filter by asset_type
    (STOCK, CRYPTO, etc.)
    """
    query = """
        SELECT symbol, name, asset_type, exchange,
               country, is_active
        FROM symbols_registry
        WHERE is_active = TRUE
    """
    params = {}

    if asset_type:
        query += " AND asset_type = :asset_type"
        params["asset_type"] = asset_type.upper()

    query += " ORDER BY symbol"

    with engine.begin() as conn:
        result = conn.execute(text(query), params).mappings().all()

    return {
        "count": len(result),
        "symbols": [dict(row) for row in result]
    }