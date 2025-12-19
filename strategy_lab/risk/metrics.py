"""Risk metric calculations.

This module provides risk metric calculations integrating with
the existing quantstats library where applicable.
"""

import numpy as np
import pandas as pd


class RiskMetrics:
    """Risk metrics calculator.

    Provides various risk metrics for strategy evaluation.
    """

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252,
    ) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns: Return series
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Number of periods per year

        Returns:
            Sharpe ratio

        """
        excess_returns = returns - risk_free_rate / periods_per_year
        if excess_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def sortino_ratio(
        returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252,
    ) -> float:
        """Calculate Sortino ratio.

        Args:
            returns: Return series
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Number of periods per year

        Returns:
            Sortino ratio

        """
        excess_returns = returns - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        return (
            excess_returns.mean() / downside_returns.std() * np.sqrt(periods_per_year)
        )

    @staticmethod
    def max_drawdown(returns: pd.Series) -> float:
        """Calculate maximum drawdown.

        Args:
            returns: Return series

        Returns:
            Maximum drawdown (as positive number)

        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())

    @staticmethod
    def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate Calmar ratio.

        Args:
            returns: Return series
            periods_per_year: Number of periods per year

        Returns:
            Calmar ratio

        """
        max_dd = RiskMetrics.max_drawdown(returns)
        if max_dd == 0:
            return 0.0

        annual_return = (1 + returns.mean()) ** periods_per_year - 1
        return annual_return / max_dd

    @staticmethod
    def value_at_risk(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR).

        Args:
            returns: Return series
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR (as positive number)

        """
        return abs(returns.quantile(1 - confidence_level))

    @staticmethod
    def conditional_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Conditional VaR (CVaR) / Expected Shortfall.

        Args:
            returns: Return series
            confidence_level: Confidence level

        Returns:
            CVaR (as positive number)

        """
        var = RiskMetrics.value_at_risk(returns, confidence_level)
        return abs(returns[returns <= -var].mean())

    @staticmethod
    def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized volatility.

        Args:
            returns: Return series
            periods_per_year: Number of periods per year

        Returns:
            Annualized volatility

        """
        return returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def downside_deviation(
        returns: pd.Series, target_return: float = 0.0, periods_per_year: int = 252,
    ) -> float:
        """Calculate downside deviation.

        Args:
            returns: Return series
            target_return: Target return threshold
            periods_per_year: Number of periods per year

        Returns:
            Annualized downside deviation

        """
        downside = returns[returns < target_return] - target_return
        return downside.std() * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_all(
        returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252,
    ) -> dict:
        """Calculate all risk metrics.

        Args:
            returns: Return series
            risk_free_rate: Risk-free rate
            periods_per_year: Number of periods per year

        Returns:
            Dictionary of all risk metrics

        """
        return {
            "sharpe_ratio": RiskMetrics.sharpe_ratio(
                returns, risk_free_rate, periods_per_year,
            ),
            "sortino_ratio": RiskMetrics.sortino_ratio(
                returns, risk_free_rate, periods_per_year,
            ),
            "max_drawdown": RiskMetrics.max_drawdown(returns),
            "calmar_ratio": RiskMetrics.calmar_ratio(returns, periods_per_year),
            "var_95": RiskMetrics.value_at_risk(returns, 0.95),
            "cvar_95": RiskMetrics.conditional_var(returns, 0.95),
            "volatility": RiskMetrics.volatility(returns, periods_per_year),
            "downside_deviation": RiskMetrics.downside_deviation(
                returns, 0.0, periods_per_year,
            ),
            "total_return": (1 + returns).prod() - 1,
            "mean_return": returns.mean() * periods_per_year,
        }
