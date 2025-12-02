"""Risk assessment service."""
from typing import Dict, Any
from decimal import Decimal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.data.price_service import PriceDataService


class RiskAssessmentService:
    """Service for portfolio risk assessment."""
    
    def __init__(self):
        self.price_service = PriceDataService()
    
    def assess_risk(
        self,
        symbol: str,
        data_source: str = "local"
    ) -> Dict[str, Any]:
        """
        Assess risk for a symbol.
        
        Returns risk metrics and recommendations.
        """
        # Get price data
        df = self.price_service.get_prices(symbol=symbol, source=data_source)
        
        if df.empty or "close" not in df.columns:
            raise ValueError(f"No price data available for {symbol}")
        
        # Calculate volatility (simplified)
        returns = df["close"].pct_change().dropna()
        volatility = float(returns.std() * (252 ** 0.5))  # Annualized
        
        # Calculate VaR (95%)
        var_95 = float(returns.quantile(0.05))
        
        # Calculate max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())
        
        # Calculate Sharpe ratio (simplified, assuming 0% risk-free rate)
        sharpe_ratio = float(returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
        
        # Beta (simplified - using market proxy of 1.0)
        beta = 1.0
        
        # Calculate risk score (0-100, higher = riskier)
        risk_score = min(100, max(0, volatility * 100))
        
        # Determine risk level
        if risk_score < 20:
            risk_level = "low"
        elif risk_score < 40:
            risk_level = "medium"
        elif risk_score < 70:
            risk_level = "high"
        else:
            risk_level = "extreme"
        
        # Generate recommendations
        recommendations = []
        if risk_score > 60:
            recommendations.append("Consider diversification to reduce volatility")
        if max_drawdown < -0.2:
            recommendations.append("Significant drawdown detected - review position sizing")
        if sharpe_ratio < 0.5:
            recommendations.append("Low risk-adjusted returns - consider alternative strategies")
        
        return {
            "risk_score": Decimal(str(risk_score)),
            "risk_level": risk_level,
            "metrics": {
                "volatility": Decimal(str(volatility)),
                "var_95": Decimal(str(var_95)),
                "sharpe_ratio": Decimal(str(sharpe_ratio)),
                "max_drawdown": Decimal(str(max_drawdown)),
                "beta": Decimal(str(beta))
            },
            "recommendations": recommendations
        }


# Global service instance
risk_service = RiskAssessmentService()
