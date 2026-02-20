from fastapi import APIRouter
from datetime import datetime
import platform
import psutil
from backend.storage.results_store import ResultsStore

router = APIRouter()
results_store = ResultsStore()

@router.get("/stats")
def get_dashboard_stats():
    """
    Get high-level dashboard statistics and system health.
    """
    return {
        "system_status": "healthy",
        "last_updated": datetime.utcnow().isoformat(),
        "active_strategies": 3,
        "total_backtests": len(results_store.get_all_results()),
        "system_info": {
            "os": platform.system(),
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "memory_usage": f"{psutil.virtual_memory().percent}%"
        }
    }

@router.get("/activity")
def get_recent_activity():
    """
    Get recent system activity from the results store.
    """
    raw = results_store.get_all_results()
    # Sort by timestamp descending and take last 10
    sorted_results = sorted(raw, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    
    activity = []
    for r in sorted_results:
        activity.append({
            "id": r.get("id"),
            "type": "backtest",
            "strategy": r.get("strategy_name"),
            "symbol": r.get("symbol"),
            "status": "completed",
            "timestamp": r.get("timestamp"),
            "metrics": {
                "return": f"{r.get('metrics', {}).get('total_return', 0):.1f}%",
                "sharpe": f"{r.get('metrics', {}).get('sharpe_ratio', 0):.2f}"
            }
        })
    return activity
