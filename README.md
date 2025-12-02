# Trading System

A research-focused trading strategy backtesting system with multiple data sources, risk management, and optimization capabilities.

## Quick Start

```bash
# 1. Clone and navigate to the repository
cd trading-system

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. Edit .env with your API keys (optional - Yahoo Finance works without keys)
nano .env

# 4. Run a backtest
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python run_strategy.py
```

## Features

✅ **Multiple Data Sources**: FMP, Yahoo Finance, or local repository  
✅ **Risk Management**: ATR-based stops, position sizing, drawdown limits  
✅ **Strategy Optimization**: Optuna-based hyperparameter tuning  
✅ **Interactive UI**: Streamlit dashboard with real-time charts  
✅ **Multiple Strategies**: Moving Average, MACD, RSI mean reversion  
✅ **Portfolio Backtesting**: Multi-symbol portfolio analysis  

## Requirements

- **Python**: 3.10+ (3.10.13 recommended)
- **API Keys** (optional):
  - FMP API key for FinancialModelingPrep data (get free key at [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/))
  - Yahoo Finance works without API keys

## Installation

### Option 1: Automated Setup (Recommended)

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Create a virtual environment
- Install all dependencies
- Copy `.env.example` to `.env`
- Verify the installation

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your API keys (optional)
nano .env
```

### Option 3: Using pyenv (Python Version Management)

```bash
# Install Python 3.10.13 via pyenv
pyenv install 3.10.13
pyenv local 3.10.13

# Verify Python version
python --version  # Should show 3.10.13

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# FMP API Configuration (optional - Yahoo Finance works without this)
FMP_API_KEY=your_api_key_here
FMP_BASE_URL=https://financialmodelingprep.com/stable

# Data Source (options: fmp, yahoo_finance, local_repository)
TS_PRICE_DATA_SOURCE=yahoo_finance

# Data Directory
TS_DATA_ROOT=data
```

**Note**: If you don't have an FMP API key, the system will automatically fall back to Yahoo Finance.

## Usage

### Console Mode (Interactive)

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run backtest
python run_strategy.py

# Or with command-line arguments
python run_strategy.py --symbol AAPL --strategy moving_average_crossover --short-window 10 --long-window 20
```

**Interactive Prompts**:
1. Choose data source (Local/FMP/Yahoo Finance)
2. Choose mode (Single backtest/Optimization)
3. Enter symbol(s) (e.g., `AAPL` or `AAPL,MSFT,GOOGL`)
4. Enter strategy parameters

**Results**: Generated in `reports/` directory
- `results.csv` - Detailed backtest data
- `{SYMBOL}_backtest.png` - Price chart with signals

### Streamlit UI (Web Interface)

```bash
# Activate virtual environment
source .venv/bin/activate

# Launch Streamlit
streamlit run ui_streamlit.py --server.address=0.0.0.0 --server.port=8501
```

Then open your browser to `http://localhost:8501`

**Features**:
- Interactive parameter controls
- Real-time chart updates
- Multiple indicator overlays (MACD, RSI, Bollinger Bands)
- Risk management settings
- Strategy optimization

### Command-Line Options

```bash
# Single symbol backtest
python run_strategy.py --symbol AAPL --short-window 10 --long-window 20

# Multiple symbols (portfolio)
python run_strategy.py --symbol AAPL,MSFT,GOOGL

# Use specific strategy
python run_strategy.py --symbol AAPL --strategy macd_crossover

# Force refresh data (bypass cache)
python run_strategy.py --symbol AAPL --force-refresh

# Skip cache entirely
python run_strategy.py --symbol AAPL --no-cache
```

## Available Strategies

### 1. Moving Average Crossover
```yaml
strategy: moving_average_crossover
params:
  short_window: 20
  long_window: 50
```

### 2. MACD Crossover
```yaml
strategy: macd_crossover
params:
  fast_span: 12
  slow_span: 26
  signal_span: 9
```

### 3. RSI Mean Reversion
```yaml
strategy: rsi_mean_reversion
params:
  period: 14
  lower_threshold: 30
  upper_threshold: 70
```

Edit `config/strategies.yaml` to customize or add new strategies.

## Data Sources

### 1. Yahoo Finance (Default, No API Key Required)
```python
# In .env
TS_PRICE_DATA_SOURCE=yahoo_finance
```

### 2. FinancialModelingPrep (Requires API Key)
```python
# In .env
FMP_API_KEY=your_key_here
TS_PRICE_DATA_SOURCE=fmp
```

### 3. Local Repository (Cached Data)
```python
# In .env
TS_PRICE_DATA_SOURCE=local_repository
```

The system automatically caches data in `data/prices/` for faster subsequent runs.

## Docker

### Build Image
```bash
docker build -t trading-system .
```

### Run Console Mode
```bash
docker run --rm -it \
  -e FMP_API_KEY="your_key" \
  trading-system
```

### Run Streamlit Mode
```bash
docker run --rm -it \
  -e RUN_MODE=streamlit \
  -e FMP_API_KEY="your_key" \
  -p 8501:8501 \
  trading-system
```

Access the UI at `http://localhost:8501`

## Project Structure

```
trading-system/
├── config/              # Configuration files
│   ├── settings.py      # Environment settings
│   └── strategies.yaml  # Strategy definitions
├── data/                # Data storage
│   ├── prices/          # Cached price data
│   └── fundamentals/    # Fundamental data
├── ingestion/           # Data ingestion clients
│   ├── fmp_client.py    # FMP API client
│   └── yahoo_finance_client.py
├── indicators/          # Technical indicators
│   └── technicals.py    # SMA, MACD, RSI, etc.
├── strategy/            # Trading strategies
│   ├── moving_average_crossover.py
│   ├── macd_crossover.py
│   └── rsi_mean_reversion.py
├── trading_backtester/  # Backtesting engine
│   ├── backtester.py    # Single-symbol backtester
│   └── portfolio_backtester.py
├── repository/          # Data repository layer
│   └── prices_repository.py
├── research/            # Research experiments
│   └── experiments/
│       └── optuna_ma_optimization.py
├── reports/             # Generated reports
├── run_strategy.py      # Console entry point
├── ui_streamlit.py      # Streamlit UI
└── requirements.txt     # Python dependencies
```

## Troubleshooting

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Missing API Key
If you see "FMP_API_KEY is not set":
1. The system will automatically fall back to Yahoo Finance
2. Or get a free FMP API key at [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)
3. Add it to your `.env` file

### No Data Returned
- Check your internet connection
- Verify the symbol is valid (e.g., `AAPL` not `Apple`)
- Try a different data source (Yahoo Finance is most reliable)

### Python Version Issues
```bash
# Check Python version
python --version

# Should be 3.10+
# If not, use pyenv to install correct version
pyenv install 3.10.13
pyenv local 3.10.13
```

## Development

### Running Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests (when implemented)
pytest tests/
```

### Adding a New Strategy

1. Create strategy file in `strategy/`:
```python
# strategy/my_strategy.py
class MyStrategy:
    def __init__(self, param1=10, **kwargs):
        self.param1 = param1
    
    def run(self, df):
        # Generate signals
        df['signal'] = 0
        # Your logic here
        return df
```

2. Add to `config/strategies.yaml`:
```yaml
my_strategy:
  module: strategy.my_strategy
  class: MyStrategy
  params:
    param1: 10
```

3. Run it:
```bash
python run_strategy.py --symbol AAPL --strategy my_strategy
```

## Performance Tips

1. **Use Local Repository**: Cache data locally for faster backtests
2. **Limit Date Range**: Use `--start-date` and `--end-date` for faster processing
3. **Parallel Processing**: Run multiple symbols in separate processes
4. **Optimize Parameters**: Use Optuna mode for automated parameter tuning

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information

## Acknowledgments

- [backtesting.py](https://github.com/kernc/backtesting.py) - Backtesting engine
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance data
- [FinancialModelingPrep](https://financialmodelingprep.com/) - Financial data API
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Optuna](https://optuna.org/) - Hyperparameter optimization
