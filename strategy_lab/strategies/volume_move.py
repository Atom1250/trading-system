"""Volume Move Breakout Strategy."""

from typing import Any

import pandas as pd

from strategy_lab.strategies.base import Strategy


class VolumeMoveBreakoutStrategy(Strategy):
    """Strategy that enters on high volume price moves and manages exit with TP/SL."""

    def generate_signals(
        self,
        data: dict[str, Any],  # MarketDataSlices
        factor_panels: dict[str, pd.DataFrame],
    ) -> dict[str, pd.Series]:
        signals = {}
        params = self.config.parameters

        move_threshold = params.get("move_threshold_pct", 0.03)
        avg_vol_window = params.get(
            "avg_volume_window",
            20,
        )  # Used if computing locally, but we might rely on factors
        min_vol_mult = params.get("min_volume_multiple", 1.0)
        tp_pct = params.get("take_profit_pct", 0.20)
        sl_pct = params.get("stop_loss_pct", -0.10)

        for symbol, slice_data in data.items():
            # Get full dataframe for the symbol
            df = slice_data.df.copy()

            # Pre-compute indicators locally for speed/simplicity in this loop
            # (Alternatively could pull from factor_panels if strict separation desired)
            df["returns"] = df["close"].pct_change()
            df["avg_volume"] = df["volume"].rolling(window=avg_vol_window).mean()

            # State tracking
            position = 0  # 0: Flat, 1: Long, -1: Short
            entry_price = 0.0

            signal_series = pd.Series(0, index=df.index)

            # Iterate
            # Note: We need to be careful not to look-ahead.
            # Signals calculated at index `i` are applied at `i` (or `i+1` depending on engine).
            # Engine logic: `signals_at_time = raw_signals.loc[timestamp]`.
            # And it uses `bar['close']` at that timestamp to execute.
            # So if we signal at T, we trade at T close (simplified).

            # We skip first few rows due to rolling window
            for i in range(avg_vol_window, len(df)):
                idx = df.index[i]
                price = df["close"].iloc[i]
                ret = df["returns"].iloc[i]
                vol = df["volume"].iloc[i]
                avg_vol = df["avg_volume"].iloc[i]

                # Logic
                output_signal = 0

                if position == 0:
                    # Check Entry
                    # Breakout Up
                    if ret > move_threshold and vol > (min_vol_mult * avg_vol):
                        output_signal = 1
                        position = 1
                        entry_price = price

                    # Breakout Down (Optional? The request implies general move, usually breakout means directional)
                    # "move_threshold_pct: 0.03 # 3% daily move"
                    # If ret < -0.03? User didn't specify short side explicitly but implied "move".
                    # Let's assume symmetric for now or just Long?
                    # "take_profit_pct: 0.20", "stop_loss_pct: -0.10".
                    # Positive TP usu implies Long.
                    # Let's support Long only for this spec unless "move" implies abs(ret).
                    # "move_threshold_pct" is positive.
                    # If ret > move_threshold -> Long.

                elif position == 1:
                    # Check Exit
                    pct_change = (price - entry_price) / entry_price

                    if pct_change >= tp_pct or pct_change <= sl_pct:
                        output_signal = -1  # Close Long
                        position = 0
                        entry_price = 0.0

                # We do not support Short entries in this interpretation yet

                signal_series.loc[idx] = output_signal

            signals[symbol] = signal_series

        return signals
