from fastapi import APIRouter

from backend.api.v1 import dashboard, backtest, optimize

api_router = APIRouter()

# We will include sub-routers here as we build them.
# For now, we'll create placeholders or just basic routes.

@api_router.get("/info")
def get_system_info():
    """Return system information."""
    return {
        "system": "Trading Strategy Lab",
        "status": "active"
    }

# Placeholder includes (commented out until modules exist)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(optimize.router, prefix="/optimize", tags=["optimize"])
