"""Fundamental analysis factors."""
from strategy_lab.factors.base import Factor, FactorRegistry
from strategy_lab.data.base import MarketDataSlice
from dataclasses import dataclass

@FactorRegistry.register("pe_ratio")
@dataclass
class PEFactor(Factor):
    """Price-to-Earnings Ratio Factor.
    
    Extracts P/E ratio from fundamental data.
    """
    
    def compute(self, data: MarketDataSlice) -> float:
        """Extract P/E ratio from data slice.
        
        Args:
            data: Market data slice
            
        Returns:
            P/E ratio value or 0.0 if not available
        """
        if 'pe' in data.df.columns:
            return data.df['pe'].iloc[-1]
        elif 'pe_ratio' in data.df.columns:
            return data.df['pe_ratio'].iloc[-1]
            
        return 0.0
