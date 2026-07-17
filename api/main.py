# ═══════════════════════════════════════════
# PATTERN ZERO — Market API
# Module I: STRATUM
# The API layer over the financial data lake
# ═══════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import stocks, crypto, macro, symbols, pipeline

app = FastAPI(
    title="Pattern Zero — Market API",
    description="API layer for STRATUM's financial data lake",
    version="1.0.0"
)

# Allow requests from anywhere for now
# (tighten this later when Observatory dashboard exists)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(crypto.router)
app.include_router(macro.router)
app.include_router(symbols.router)
app.include_router(pipeline.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Pattern Zero — Market API",
        "module": "STRATUM",
        "docs": "/docs"
    }