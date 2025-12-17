"""Technical analysis factors."""
import numpy as np
from strategy_lab.factors.base import Factor, FactorRegistry
from strategy_lab.data.base import MarketDataSlice
from dataclasses import dataclass

@FactorRegistry.register("moving_average_cross")
@dataclass
class MovingAverageCrossFactor(Factor):
    """Moving Average Crossover Factor.
    
    Returns a binary signal:
    1.0 if fast_ma > slow_ma (Bullish)
    0.0 if fast_ma <= slow_ma (Bearish/Neutral)
    """
    fast_window: int = 50
    slow_window: int = 200
    
    def compute(self, data: MarketDataSlice) -> float:
        """Compute the moving average crossover signal.
        
        Args:
            data: Market data slice
            
        Returns:
            1.0 if bullish crossover, 0.0 otherwise
        """
        if len(data.df) < self.slow_window:
            return 0.0
            
        close_prices = data.df['close']
        
        # Calculate moving averages
        fast_ma = close_prices.rolling(window=self.fast_window).mean().iloc[-1]
        slow_ma = close_prices.rolling(window=self.slow_window).mean().iloc[-1]
        
        # Return binary signal
        if np.isnan(fast_ma) or np.isnan(slow_ma):
             return 0.0
             
        return 1.0 if fast_ma > slow_ma else 0.0
