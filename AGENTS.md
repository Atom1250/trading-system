# AGENTS.md

Project: Internal Trading System (FMP-powered prototype)

Context:
- Python 3.10+
- Repo layout with src/, tests/, data/, reports/
- Backtesting.py for backtests
- FinancialModelingPrep (FMP) as the external market data source
- No live trading yet, only research/backtesting

## Core Technologies & Frameworks (do not change unless explicitly requested)

You MUST keep the following choices stable across the codebase, unless the user explicitly requests a change:

- Backtesting framework: **backtesting.py**
- Indicator library: **ta**
- Performance/tearsheet library: **quantstats**
- Data source: **FinancialModelingPrep (FMP)** for historical market data
- Configuration: environment variables via **python-dotenv** and `.env`
- Optional UI: **Streamlit** (if present) for interactive dashboards

When adding new functionality, you MUST:
- Reuse these frameworks rather than introducing alternatives (e.g., do NOT add a second backtesting framework or a second indicator library).
- Reuse existing utilities and helper functions where possible.
- If you believe a new framework is necessary, clearly document why in code comments and README, and keep the old path working unless the user explicitly approves a migration.

## Architecture & Orchestration Consistency

The project should feel like a single, coherent system.

You MUST:
- Preserve the high-level architecture:
  - `src/data` for data access and ingestion
  - `src/strategies` for trading strategies
  - `src/backtest` for backtest/optimization/batch scripts
  - `src/analytics` for reports, dashboards, and portfolio aggregation
  - `tests` for all tests
- Keep existing interfaces stable whenever possible. If you need to change a function or class interface:
  - Update all call sites consistently.
  - Update or add tests to cover the new interface.
  - Update README and/or internal docs to reflect the change.

You MUST NOT:
- Introduce parallel or conflicting orchestration paths (e.g., a second, unrelated way of running backtests) unless you are explicitly asked to do so.
- Partially migrate to a new pattern and leave old code paths inconsistent.
- Change authentication, configuration, or integration mechanisms without reviewing existing patterns and aligning with them.

If you introduce new scripts or modules, they MUST:
- Work with the existing directory structure.
- Use the same data access layer (`fetch_daily_adjusted` and related helpers).
- Emit outputs to `reports/` using consistent naming patterns.

## Shared Templates & Integration Patterns

To keep consistency, use the following patterns as templates when adding new elements.

### 1. API Client Template

When adding a new external API client module (e.g., another data source):

- Place it under `src/data/`.
- Follow this structure:

```python
# src/data/<service>_client.py
import os
from typing import Optional
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://example.com/api"


def fetch_<resource>(
    symbol: str,
    api_key: Optional[str] = None,
    *,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetches <resource> data for the requested symbol.
    Respects caching and free-tier limits.
    """
    api_key = api_key or os.getenv("EXAMPLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set EXAMPLE_API_KEY in .env")

    # Implement caching, rate limiting, and error handling here
    ...
```
