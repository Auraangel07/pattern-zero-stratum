# ═══════════════════════════════════════════
# PATTERN ZERO — API Database Connection
# Reuses the same connection pattern as
# the ingestion layer
# ═══════════════════════════════════════════

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    connection_string = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )
    return create_engine(
        connection_string,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800
    )

engine = get_engine()