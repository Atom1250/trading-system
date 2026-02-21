"""Feature Engineering Pipeline for ML models."""
import pandas as pd
import numpy as np

class TimeSeriesFeatureGenerator:
    """Generates features and targets from OHLCV data."""

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends technical indicators and rolling returns to the OHLCV dataframe.
        """
        df_feats = df.copy()
        
        # Check required columns
        if 'Close' not in df_feats.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")

        # 1. Simple rolling lagged returns
        for lag in [1, 2, 3, 5, 10]:
            df_feats[f'return_lag_{lag}'] = df_feats['Close'].pct_change(periods=lag)

        # 2. Volatility
        daily_ret = df_feats['Close'].pct_change()
        for window in [10, 20]:
            df_feats[f'volatility_{window}'] = daily_ret.rolling(window=window).std()
        
        # 3. Distance from Simple Moving Average
        for window in [10, 50]:
            sma = df_feats['Close'].rolling(window=window).mean()
            df_feats[f'dist_sma_{window}'] = (df_feats['Close'] - sma) / sma
        
        # 4. RSI (Relative Strength Index)
        delta = df_feats['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        df_feats['rsi_14'] = 100 - (100 / (1 + rs))

        return df_feats

    def generate_targets(self, df: pd.DataFrame, horizon: int = 5) -> pd.Series:
        """
        Calculates forward N-day returns and classifies them into signals
        (1 for Up, 0 for Down). Returns as a pandas Series.
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")
            
        # Forward return: (Price_{t+horizon} - Price_t) / Price_t
        forward_returns = df['Close'].shift(-horizon) / df['Close'] - 1.0
        
        # Binary target: 1 if positive return, 0 otherwise
        targets = pd.Series((forward_returns > 0).astype(int), index=df.index, name="target")
        
        # For the last 'horizon' rows, the forward return is NaN, target should be NaN
        # Using numpy nan to denote unknown future
        targets.iloc[-horizon:] = np.nan
        
        return targets
