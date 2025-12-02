"""Unit tests for technical indicators."""
import pandas as pd
import pytest
from datetime import datetime

from indicators.technicals import sma


class TestTechnicalIndicators:
    """Tests for technical indicator functions."""
    
    def test_sma_basic(self):
        """Test simple moving average calculation."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        }, index=dates)
        
        result = sma(df, window=3, column='close')
        
        # First two values should be NaN
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        
        # Third value should be average of first 3
        assert result.iloc[2] == pytest.approx(101.0)
        
        # Last value should be average of last 3
        assert result.iloc[-1] == pytest.approx(108.0)
    
    def test_sma_window_larger_than_data(self):
        """Test SMA when window is larger than data."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
        }, index=dates)
        
        result = sma(df, window=10, column='close')
        
        # All values should be NaN when window > data length
        assert result.isna().all()
    
    def test_sma_adds_column_to_dataframe(self):
        """Test that SMA adds column to DataFrame."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        }, index=dates)
        
        sma(df, window=5, column='close')
        
        # Should add SMA_5 column
        assert 'SMA_5' in df.columns


class TestStrategySignals:
    """Tests for strategy signal generation."""
    
    def test_moving_average_crossover_signals(self):
        """Test MA crossover signal generation."""
        from strategy.moving_average_crossover import MovingAverageCrossoverStrategy
        
        # Create test data with clear crossover
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        prices = [100] * 50 + [110] * 50  # Price jump at day 50
        
        df = pd.DataFrame({
            'close': prices,
            'open': prices,
            'high': [p + 1 for p in prices],
            'low': [p - 1 for p in prices],
            'volume': [1000000] * 100,
        }, index=dates)
        
        strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        result = strategy.run(df)
        
        # Should have signal column
        assert 'signal' in result.columns
        
        # Should have some buy signals after price jump
        assert (result['signal'] > 0).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
