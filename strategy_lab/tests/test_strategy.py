import sys
import os
import pandas as pd


# Ensure strategy_lab is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strategy_lab.config import StrategyConfig
from strategy_lab.strategies.rule_based import MultiSignalRuleStrategy

def test_multi_signal_strategy():
    # Setup
    config = StrategyConfig(
        name="TestStrategy",
        parameters={
            "w_tech": 0.5,
            "w_fund": 0.3,
            "w_sent": 0.2,
            "threshold": 0.1
        }
    )
    strategy = MultiSignalRuleStrategy(config)
    
    # Mock data
    dates = pd.date_range("2023-01-01", periods=5)
    
    # Mock factor panels
    # Symbol A: Strong buy signal
    df_a = pd.DataFrame({
        "technical": [0.8, 0.9, 0.8, 0.9, 0.8],
        "fundamental": [0.5, 0.5, 0.5, 0.6, 0.6],
        "sentiment": [0.2, 0.3, 0.2, 0.1, 0.2]
    }, index=dates)
    
    # Symbol B: Strong sell signal
    df_b = pd.DataFrame({
        "technical": [-0.8, -0.9, -0.8, -0.9, -0.8],
        "fundamental": [-0.5, -0.5, -0.5, -0.6, -0.6],
        "sentiment": [-0.2, -0.3, -0.2, -0.1, -0.2]
    }, index=dates)
    
    # Symbol C: Neutral
    df_c = pd.DataFrame({
        "technical": [0.0, 0.05, -0.05, 0.0, 0.0],
        "fundamental": [0.1, 0.1, 0.1, 0.1, 0.1],
        "sentiment": [-0.1, -0.1, -0.1, -0.1, -0.1]
    }, index=dates)
    
    factor_panels = {
        "A": df_a,
        "B": df_b,
        "C": df_c
    }
    
    # Execution
    signals = strategy.generate_signals({}, factor_panels)
    
    # Verification
    # A should be 1 (Long)
    # Score A approx: 0.5*0.8 + 0.3*0.5 + 0.2*0.2 = 0.4 + 0.15 + 0.04 = 0.59 > 0.1
    print("Signals A:", signals["A"].values)
    assert (signals["A"] == 1).all()
    
    # B should be -1 (Short)
    # Score B approx: 0.5*-0.8 + 0.3*-0.5 + 0.2*-0.2 = -0.4 - 0.15 - 0.04 = -0.59 < -0.1
    print("Signals B:", signals["B"].values)
    assert (signals["B"] == -1).all()
    
    # C should be 0 (Neutral)
    # Score C approx: 0.5*0 + 0.3*0.1 + 0.2*-0.1 = 0 + 0.03 - 0.02 = 0.01 < 0.1
    print("Signals C:", signals["C"].values)
    assert (signals["C"] == 0).all()

if __name__ == "__main__":
    try:
        test_multi_signal_strategy()
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
