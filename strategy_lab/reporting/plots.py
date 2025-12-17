"""Performance plotting utilities.

This module provides visualization tools for strategy performance analysis,
including equity curves, drawdowns, and monthly returns heatmaps.
"""
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
except ImportError:
    plt = None
    Figure = Any

class PerformancePlotter:
    """Class for generating performance plots."""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """Initialize plotter.
        
        Args:
            style: Matplotlib style to use
        """
        self.style = style
        if plt:
            try:
                plt.style.use(style)
            except OSError:
                # Fallback if style not found
                plt.style.use('default')
    
    def plot_equity_curve(
        self, 
        returns: pd.Series, 
        benchmark_returns: Optional[pd.Series] = None,
        title: str = "Equity Curve"
    ) -> Optional[Figure]:
        """Plot cumulative equity curve.
        
        Args:
            returns: Series of period returns
            benchmark_returns: Optional benchmark returns
            title: Plot title
            
        Returns:
            Matplotlib Figure object
        """
        if plt is None:
            return None
            
        cum_returns = (1 + returns).cumprod()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(cum_returns.index, cum_returns.values, label='Strategy', linewidth=2)
        
        if benchmark_returns is not None:
            cum_bench = (1 + benchmark_returns).cumprod()
            # Align dates
            cum_bench = cum_bench.reindex(cum_returns.index).fillna(method='ffill')
            ax.plot(cum_bench.index, cum_bench.values, label='Benchmark', alpha=0.6, linestyle='--')
            
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Return")
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        return fig

    def plot_drawdowns(self, returns: pd.Series, title: str = "Drawdown") -> Optional[Figure]:
        """Plot underwater drawdown chart.
        
        Args:
            returns: Series of period returns
            title: Plot title
            
        Returns:
            Matplotlib Figure object
        """
        if plt is None:
            return None
            
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max
        
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
        ax.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Drawdown")
        ax.grid(True, alpha=0.3)
        
        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        return fig
        
    def plot_monthly_heatmap(self, returns: pd.Series) -> Optional[Figure]:
        """Plot monthly returns heatmap.
        
        Args:
            returns: Series of daily returns
            
        Returns:
            Matplotlib Figure object
        """
        if plt is None:
            return None
            
        # Resample to monthly returns
        monthly_ret = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
        
        # Create pivot table (Year x Month)
        monthly_ret.index = pd.to_datetime(monthly_ret.index)
        df = pd.DataFrame({'return': monthly_ret.values})
        df['year'] = monthly_ret.index.year
        df['month'] = monthly_ret.index.month
        
        pivot = df.pivot(index='year', columns='month', values='return')
        
        fig, ax = plt.subplots(figsize=(10, len(pivot) * 0.5 + 2))
        im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=-0.1, vmax=0.1)
        
        # Add labels
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)
        
        # Add text annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if not np.isnan(val):
                    text = ax.text(j, i, f"{val:.1%}",
                                 ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title("Monthly Returns", fontsize=14)
        fig.colorbar(im, ax=ax, label='Return')
        fig.tight_layout()
        
        return fig
