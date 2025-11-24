# Trading System

A research-focused trading strategy backtesting prototype using Alpha Vantage data, Streamlit for optional UI, and containerized execution via Docker.

## Requirements
- Python 3.11 (recommended) or newer
- System packages to support scientific Python (e.g., libatlas/BLAS where applicable)
- Project dependencies from `requirements.txt`:
  - core: `pandas`, `numpy`, `requests`
  - analysis/plotting: `matplotlib`, `quantstats`
  - indicators/backtesting: `ta`, `backtesting`
  - configuration/UI: `python-dotenv`, `PyYAML`, `streamlit`
- Alpha Vantage API key provided via environment variable `ALPHA_VANTAGE_API_KEY` (stored in a local `.env` based on `.env.example`)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Local Usage (Console)
1. Create a `.env` file (copy `.env.example`) and set `ALPHA_VANTAGE_API_KEY`.
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
The app can cache Alpha Vantage daily data under `data_cache/` to reduce API calls. Use the Streamlit data source toggle or console options to run from cache, and optionally refresh the cache from the API.

## Docker
A slim Python 3.11 image is provided for containerized runs.

### Build
```bash
docker build -t trading-system .
```

### Run (Console mode)
```bash
docker run --rm -it \
  -e ALPHA_VANTAGE_API_KEY="<your_key>" \
  trading-system
```

### Run (Streamlit mode)
```bash
docker run --rm -it \
  -e RUN_MODE=streamlit \
  -e ALPHA_VANTAGE_API_KEY="<your_key>" \
  -p 8501:8501 \
  trading-system
```

The container entrypoint respects `RUN_MODE` (`console` by default) and exposes port `8501` for Streamlit.
