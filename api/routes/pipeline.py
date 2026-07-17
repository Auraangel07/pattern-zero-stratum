# ═══════════════════════════════════════════
# PATTERN ZERO — Pipeline Health API Routes
# ═══════════════════════════════════════════

from fastapi import APIRouter
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/pipeline", tags=["Pipeline Health"])

@router.get("/status")
def get_pipeline_status():
    """
    Latest status of each ingestion pipeline —
    the API window into pipeline_logs.
    """
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT ON (pipeline_name)
                pipeline_name, status,
                records_fetched, records_inserted,
                error_message, started_at, completed_at
            FROM pipeline_logs
            ORDER BY pipeline_name, started_at DESC
        """)).mappings().all()

    return {
        "count": len(result),
        "pipelines": [dict(row) for row in result]
    }

@router.get("/history/{pipeline_name}")
def get_pipeline_history(pipeline_name: str, limit: int = 10):
    """
    Recent run history for a specific pipeline.
    """
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT pipeline_name, status,
                   records_fetched, records_inserted,
                   error_message, started_at, completed_at
            FROM pipeline_logs
            WHERE pipeline_name = :name
            ORDER BY started_at DESC
            LIMIT :limit
        """), {
            "name": pipeline_name,
            "limit": limit
        }).mappings().all()

    return {
        "pipeline_name": pipeline_name,
        "count": len(result),
        "runs": [dict(row) for row in result]
    }