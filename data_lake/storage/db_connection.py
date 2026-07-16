# ═══════════════════════════════════════════
# PATTERN ZERO — Database Connection
# MODULE I: STRATUM
# The single source of truth for DB access
# ═══════════════════════════════════════════

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def get_engine():
    """
    Returns SQLAlchemy engine connected
    to Pattern Zero TimescaleDB
    """
    connection_string = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )
    
    engine = create_engine(
        connection_string,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    
    return engine

def test_connection():
    """
    Tests database connection.
    Run this to verify everything works.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT version()")
            )
            version = result.fetchone()[0]
            print("✅ Connection successful!")
            print(f"📊 Database: {version[:50]}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()