"""Technical indicators service."""
import sys
from pathlib import Path
from typing import Dict, Any
from decimal import Decimal
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indicators.technicals import sma, rsi, macd
from services.data.price_service import PriceDataService


class TechnicalIndicatorsService:
    """Service for calculating technical indicators."""
    
    def __init__(self):
        self.price_service = PriceDataService()
    
    def calculate_indicators(
        self,
        symbol: str,
        data_source: str = "local"
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators for a symbol.
        
        Returns dict with indicator values and signals.
        """
        # Get price data
        df = self.price_service.get_prices(symbol=symbol, source=data_source)
        
        if df.empty:
            raise ValueError(f"No price data available for {symbol}")
        
        if "close" not in df.columns:
            raise ValueError("No 'close' column in price data")
        
        indicators = []
        
        # SMA indicators
        df["sma_20"] = sma(df, window=20)
        df["sma_50"] = sma(df, window=50)
        df["sma_200"] = sma(df, window=200)
        
        current_price = float(df["close"].iloc[-1])
        sma_20_val = float(df["sma_20"].iloc[-1]) if pd.notna(df["sma_20"].iloc[-1]) else None
        sma_50_val = float(df["sma_50"].iloc[-1]) if pd.notna(df["sma_50"].iloc[-1]) else None
        sma_200_val = float(df["sma_200"].iloc[-1]) if pd.notna(df["sma_200"].iloc[-1]) else None
        
        if sma_20_val:
            signal = "buy" if current_price > sma_20_val else "sell"
            indicators.append({
                "name": "SMA_20",
                "value": sma_20_val,
                "signal": signal
            })
        
        if sma_50_val:
            signal = "buy" if current_price > sma_50_val else "sell"
            indicators.append({
                "name": "SMA_50",
                "value": sma_50_val,
                "signal": signal
            })
        
        if sma_200_val:
            signal = "buy" if current_price > sma_200_val else "sell"
            indicators.append({
                "name": "SMA_200",
                "value": sma_200_val,
                "signal": signal
            })
        
        # RSI
        rsi(df, period=14)
        rsi_val = float(df["RSI_14"].iloc[-1]) if pd.notna(df["RSI_14"].iloc[-1]) else None
        
        if rsi_val:
            if rsi_val < 30:
                signal = "buy"
            elif rsi_val > 70:
                signal = "sell"
            else:
                signal = "neutral"
            
            indicators.append({
                "name": "RSI_14",
                "value": rsi_val,
                "signal": signal
            })
        
        # MACD
        macd(df, fast_span=12, slow_span=26, signal_span=9)
        macd_line = float(df["MACD_line"].iloc[-1]) if pd.notna(df["MACD_line"].iloc[-1]) else None
        macd_signal = float(df["MACD_signal"].iloc[-1]) if pd.notna(df["MACD_signal"].iloc[-1]) else None
        
        if macd_line and macd_signal:
            signal = "buy" if macd_line > macd_signal else "sell"
            indicators.append({
                "name": "MACD",
                "value": macd_line,
                "signal": signal
            })
        
        # Calculate overall signal
        buy_signals = sum(1 for ind in indicators if ind.get("signal") == "buy")
        sell_signals = sum(1 for ind in indicators if ind.get("signal") == "sell")
        total_signals = len(indicators)
        
        if buy_signals > sell_signals:
            overall_signal = "buy"
            strength = Decimal(str((buy_signals / total_signals) * 100))
        elif sell_signals > buy_signals:
            overall_signal = "sell"
            strength = Decimal(str((sell_signals / total_signals) * 100))
        else:
            overall_signal = "neutral"
            strength = Decimal("50")
        
        return {
            "symbol": symbol,
            "indicators": indicators,
            "overall_signal": overall_signal,
            "strength": strength
        }


# Global service instance
technical_service = TechnicalIndicatorsService()
