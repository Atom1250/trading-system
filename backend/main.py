import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the project root is in sys.path so we can import from strategy_lab, etc.
# This assumes backend/main.py is two levels deep from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import routers (to be created)
from backend.api.router import api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading System API",
    description="Backend API for Trading Strategy Lab",
    version="2.0.0",
)

# CORS Configuration
# Allow requests from frontend (default port 3000)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root():
    """Root endpoint info."""
    return {"message": "Trading System API is running. Visit /docs for Swagger UI."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
