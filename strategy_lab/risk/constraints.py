"""Risk constraint implementations.

This module provides risk constraint classes that can be used
to enforce position sizing and exposure limits.
"""
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd


@dataclass
class PositionConstraint:
    """Position-level constraint.
    
    Attributes:
        max_position_size: Maximum position size (fraction of portfolio)
        max_leverage: Maximum leverage
        min_liquidity: Minimum liquidity requirement
    """
    max_position_size: float = 0.2
    max_leverage: float = 1.0
    min_liquidity: float = 1_000_000.0
    
    def check(self, position_size: float, leverage: float, liquidity: float) -> bool:
        """Check if position meets constraints.
        
        Args:
            position_size: Position size as fraction of portfolio
            leverage: Current leverage
            liquidity: Asset liquidity
            
        Returns:
            True if constraints are met
        """
        if position_size > self.max_position_size:
            return False
        if leverage > self.max_leverage:
            return False
        if liquidity < self.min_liquidity:
            return False
        return True


@dataclass
class PortfolioConstraint:
    """Portfolio-level constraint.
    
    Attributes:
        max_total_exposure: Maximum total exposure
        max_sector_exposure: Maximum exposure to single sector
        max_correlation: Maximum correlation between positions
        max_concentration: Maximum concentration (Herfindahl index)
    """
    max_total_exposure: float = 1.0
    max_sector_exposure: float = 0.4
    max_correlation: float = 0.7
    max_concentration: float = 0.5
    
    def check_exposure(self, total_exposure: float) -> bool:
        """Check total exposure constraint.
        
        Args:
            total_exposure: Total portfolio exposure
            
        Returns:
            True if constraint is met
        """
        return total_exposure <= self.max_total_exposure
    
    def check_sector_exposure(self, sector_exposures: Dict[str, float]) -> bool:
        """Check sector exposure constraints.
        
        Args:
            sector_exposures: Dictionary of sector exposures
            
        Returns:
            True if all constraints are met
        """
        return all(exp <= self.max_sector_exposure for exp in sector_exposures.values())
    
    def check_concentration(self, position_weights: pd.Series) -> bool:
        """Check concentration constraint using Herfindahl index.
        
        Args:
            position_weights: Series of position weights
            
        Returns:
            True if constraint is met
        """
        herfindahl = (position_weights ** 2).sum()
        return herfindahl <= self.max_concentration


@dataclass
class RiskLimitConstraint:
    """Risk limit constraint.
    
    Attributes:
        max_var: Maximum Value at Risk
        max_volatility: Maximum portfolio volatility
        max_drawdown: Maximum allowed drawdown
        stop_loss_pct: Stop loss percentage
    """
    max_var: float = 0.05
    max_volatility: float = 0.3
    max_drawdown: float = 0.2
    stop_loss_pct: float = 0.1
    
    def check_var(self, var: float) -> bool:
        """Check VaR constraint.
        
        Args:
            var: Current VaR
            
        Returns:
            True if constraint is met
        """
        return var <= self.max_var
    
    def check_volatility(self, volatility: float) -> bool:
        """Check volatility constraint.
        
        Args:
            volatility: Current volatility
            
        Returns:
            True if constraint is met
        """
        return volatility <= self.max_volatility
    
    def check_drawdown(self, current_drawdown: float) -> bool:
        """Check drawdown constraint.
        
        Args:
            current_drawdown: Current drawdown
            
        Returns:
            True if constraint is met
        """
        return current_drawdown <= self.max_drawdown
