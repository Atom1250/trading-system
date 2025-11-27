# Trading System

A research-focused trading strategy backtesting prototype using FinancialModelingPrep (FMP) data, Streamlit for optional UI, and containerized execution via Docker.

## Requirements
- Python 3.10 (recommended) or newer
- System packages to support scientific Python (e.g., libatlas/BLAS where applicable)
- Project dependencies from `requirements.txt`:
  - core: `pandas`, `numpy`, `requests`
  - analysis/plotting: `matplotlib`, `quantstats`
  - indicators/backtesting: `ta`, `backtesting`
  - configuration/UI: `python-dotenv`, `PyYAML`, `streamlit`
- FMP API key provided via environment variable `FMP_API_KEY` (stored in a local `.env` based on `.env.example`)

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Python version management with pyenv
The repository includes a `.python-version` pin (Python 3.10.13) so pyenv users automatically select the correct interpreter. To set up locally:

```bash
# Install pyenv if not already available (see https://github.com/pyenv/pyenv#installation)
pyenv install 3.10.13
pyenv local 3.10.13  # uses .python-version in this directory

# (Optional) create an isolated virtual environment for dependencies
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If installation errors mention Python 3.11+ (e.g., when building `numba`), it usually means `pip` resolved to a non-pyenv
interpreter. Confirm pyenv is active before installing dependencies:

```bash
pyenv versions          # should show 3.10.13 with a * next to it in this repo
pyenv which python      # should point inside ~/.pyenv/versions/3.10.13
python --version        # should report 3.10.13
python -m pip install -r requirements.txt
```

## Local Usage (Console)
1. Create a `.env` file (copy `.env.example`) and set `FMP_API_KEY`.
2. Run the console workflow:

```bash
python run_strategy.py
```
3. When prompted, enter a single symbol (e.g., `AAPL`) or a comma-separated list (e.g., `AAPL,MSFT`).
4. Results, CSV exports, and charts are written under `reports/`.

## Local Usage (Streamlit)
1. Ensure dependencies are installed and `.env` is configured.
2. Launch the Streamlit UI:

```bash
streamlit run ui_streamlit.py --server.address=0.0.0.0 --server.port=8501
```
3. Open the provided URL in a browser, choose symbol(s), select the data source (cached vs. live API), and run the backtest.

## Caching
The app caches price history under `data/prices/` when using the repository-backed mode. Use the Streamlit data source toggle or console options to run from cache, and optionally refresh the cache from the FMP API.

## Docker
A slim Python 3.10 image is provided for containerized runs.

### Build
```bash
docker build -t trading-system .
```

### Run (Console mode)
```bash
docker run --rm -it \
  -e FMP_API_KEY="<your_key>" \
  trading-system
```

### Run (Streamlit mode)
```bash
docker run --rm -it \
  -e RUN_MODE=streamlit \
  -e FMP_API_KEY="<your_key>" \
  -p 8501:8501 \
  trading-system
```

The container entrypoint respects `RUN_MODE` (`console` by default) and exposes port `8501` for Streamlit.
