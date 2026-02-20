from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from backend.schemas.backtest import BacktestRequest, BacktestResponse, BacktestMetrics, EquityPoint, TradeRecord
from backend.storage.results_store import ResultsStore
from strategy_lab.backtest.engine import StrategyBacktestEngine
from strategy_lab.data.providers import YFinanceHistoricalProvider
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.config import RiskConfig
from strategy_lab.strategies.simple.moving_average import MovingAverageCrossoverStrategy
from strategy_lab.strategies.simple.rsi import RSIMeanReversionStrategy
from strategy_lab.strategies.simple.trend_pullback import TrendPullbackStrategy

router = APIRouter()
results_store = ResultsStore()

# Strategy Registry (Simple mapping for now)
STRATEGIES = {
    "MovingAverageCrossover": MovingAverageCrossoverStrategy,
    "RSIMeanReversion": RSIMeanReversionStrategy,
    "TrendPullback": TrendPullbackStrategy,
}

@router.get("/history", response_model=list[dict])
def get_backtest_history():
    """Get history of past backtests."""
    raw = results_store.get_all_results()
    # Return simplified metadata list
    return [{
        "id": r.get("id"), 
        "timestamp": r.get("timestamp"), 
        "strategy": r.get("strategy_name"), 
        "symbol": r.get("symbol"), 
        "metrics": r.get("metrics")
    } for r in raw]

@router.post("/run", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest):
    """
    Run a strategy backtest.
    """
    try:
        # 1. Resolve Strategy Class
        if request.strategy_name not in STRATEGIES:
            raise HTTPException(status_code=400, detail=f"Strategy '{request.strategy_name}' not found.")
        
        StrategyClass = STRATEGIES[request.strategy_name]
        
        # 2. Initialize Components
        data_provider = YFinanceHistoricalProvider()
        risk_config = RiskConfig()
        risk_engine = RiskEngine(risk_config=risk_config)
        
        engine = StrategyBacktestEngine(
            data_provider=data_provider,
            risk_engine=risk_engine,
        )
        
        # 3. Instantiate Strategy
        # Note: strategy_lab strategies expect a StrategyConfig
        from strategy_lab.config import StrategyConfig
        strat_cfg = StrategyConfig(
            name=request.strategy_name,
            initial_capital=request.initial_capital,
            parameters=request.parameters,
            risk_config=risk_config
        )
        strategy = StrategyClass(config=strat_cfg)
        
        # 4. Convert Dates to Datetime (UTC aware)
        start_dt = datetime.combine(request.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(request.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # 5. Run Backtest
        try:
            results = engine.run(
                strategy=strategy,
                start_date=start_dt,
                end_date=end_dt,
                universe=[request.symbol],
                initial_capital=request.initial_capital
            )
        except ValueError as e:
             raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")

        # 6. Serialize Results
        # Metrics
        res_metrics = results.get_metrics()
        metrics = BacktestMetrics(
            total_return=res_metrics.get("total_return", 0.0) * 100, # Convert to percentage
            cagr=res_metrics.get("cagr", 0.0) * 100,
            sharpe_ratio=res_metrics.get("sharpe_ratio", 0.0),
            max_drawdown=res_metrics.get("max_drawdown", 0.0) * 100,
            win_rate=res_metrics.get("win_rate", 0.0) * 100,
            total_trades=int(res_metrics.get("num_trades", 0))
        )
        
        # Equity Curve
        equity_curve = []
        if results.portfolio_history is not None and not results.portfolio_history.empty:
            df_eq = results.portfolio_history.reset_index()
            for _, row in df_eq.iterrows():
                equity_curve.append(EquityPoint(
                    timestamp=row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                    equity=float(row["equity"]),
                    drawdown=float(row.get("drawdown", 0.0))
                ))
        
        # Trades
        trades = []
        if results.trade_log is not None and not results.trade_log.empty:
             for _, row in results.trade_log.iterrows():
                trades.append(TradeRecord(
                    timestamp=row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                    symbol=row["symbol"],
                    type=row["type"],
                    price=float(row["price"]),
                    quantity=float(row["quantity"]),
                    pnl=float(row["pnl"])
                ))
        
        response_obj = BacktestResponse(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades
        )

        # Save to Store
        results_store.save_result(response_obj.dict())
        
        return response_obj

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
