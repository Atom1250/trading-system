"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import (
    portfolios,
    data,
    strategies,
    signals,
    ai,
    integration,
    optimization
)

app = FastAPI(
    title="Trading System API",
    description="Modern backend for algorithmic trading system",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolios.router, prefix="/api/v1/portfolios", tags=["portfolios"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["strategies"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["signals"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(integration.router, prefix="/api/v1/integration", tags=["integration"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Trading System API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
