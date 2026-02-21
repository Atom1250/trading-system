"""Score-to-signal policy helpers."""

from __future__ import annotations

import pandas as pd


def score_to_signal_series(
    scores: pd.Series,
    *,
    long_threshold: float = 0.1,
    short_threshold: float = -0.1,
) -> pd.Series:
    """Convert model scores into {-1,0,1} signals."""
    out = pd.Series(0.0, index=scores.index)
    out.loc[scores >= long_threshold] = 1.0
    out.loc[scores <= short_threshold] = -1.0
    return out
