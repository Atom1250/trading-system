from fastapi import APIRouter

from backend.api import routes_backtest, routes_trading
from backend.api.v1 import backtest, dashboard, ml, optimize

api_router = APIRouter()

# We will include sub-routers here as we build them.
# For now, we'll create placeholders or just basic routes.


@api_router.get("/info")
def get_system_info():
    """Return system information."""
    return {"system": "Trading Strategy Lab", "status": "active"}


# Placeholder includes (commented out until modules exist)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(optimize.router, prefix="/optimize", tags=["optimize"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(routes_backtest.router, tags=["backtests"])
api_router.include_router(routes_trading.router, tags=["trading"])

from portfolio.api.routes import router as portfolio_router
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
