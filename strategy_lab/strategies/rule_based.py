"""Rule-based trading strategies.

This module implements strategies that generate signals based on predefined rules
and weighted factors.
"""


import pandas as pd

from ..config import StrategyConfig
from .base import FactorPanels, MarketDataSlices, Strategy


class MultiSignalRuleStrategy(Strategy):
    """Rule-based strategy combining technical, fundamental, and sentiment factors.

    Logic:
        1. Read weights (w_tech, w_fund, w_sent) from config.parameters.
        2. Combine factors into a composite score for each symbol:
           score = w_tech * tech_score + w_fund * fund_score + w_sent * sent_score
        3. Generate target signal based on score sign/magnitude:
           > 0 -> 1 (Long)
           < 0 -> -1 (Short)
           0 -> 0 (Neutral)

    The input factor_panels are expected to have columns 'technical', 'fundamental',
    and 'sentiment' which are pre-normalized scores.
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.w_tech = self.config.parameters.get("w_tech", 0.4)
        self.w_fund = self.config.parameters.get("w_fund", 0.3)
        self.w_sent = self.config.parameters.get("w_sent", 0.3)
        self.threshold = self.config.parameters.get("threshold", 0.0)

    def generate_signals(
        self, data: MarketDataSlices, factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate signals based on weighted factor scores.

        Args:
            data: Market data slices (unused in this simple rule, but available)
            factor_panels: Dictionary of DataFrames with factor columns

        Returns:
            Dictionary of signal Series per symbol

        """
        signals = {}

        for symbol, factors_df in factor_panels.items():
            # Ensure required columns exist, fill missing with 0
            # Ensure required columns exist, fill missing with 0, but keep as Series
            tech_score = (
                factors_df["technical"]
                if "technical" in factors_df.columns
                else pd.Series(0.0, index=factors_df.index)
            )
            fund_score = (
                factors_df["fundamental"]
                if "fundamental" in factors_df.columns
                else pd.Series(0.0, index=factors_df.index)
            )
            sent_score = (
                factors_df["sentiment"]
                if "sentiment" in factors_df.columns
                else pd.Series(0.0, index=factors_df.index)
            )

            # Calculate composite score
            composite_score = (
                self.w_tech * tech_score
                + self.w_fund * fund_score
                + self.w_sent * sent_score
            )

            # Generate signal based on threshold
            # Using numpy where for vectorized conditional logic
            # result is a Series
            symbol_signals = pd.Series(0, index=factors_df.index)

            # Long signals
            symbol_signals[composite_score > self.threshold] = 1

            # Short signals
            symbol_signals[composite_score < -self.threshold] = -1

            signals[symbol] = symbol_signals

        return signals
