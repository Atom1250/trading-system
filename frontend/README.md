# Modern Streamlit Frontend

Modern UI for the trading system that consumes the FastAPI backend.

## Setup

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

**Important**: Start the backend API first!

```bash
# Terminal 1: Start backend
cd backend
./start.sh

# Terminal 2: Start frontend
cd frontend
streamlit run app.py
```

The UI will open at http://localhost:8501

## Features

### Dashboard Tab
- Portfolio metrics overview
- Value over time chart
- Asset allocation pie chart
- Position sizes

### Strategies Tab
- List of available strategies
- Strategy parameters
- Strategy descriptions

### Signals Tab
- Technical indicators (SMA, RSI, MACD)
- Fundamental metrics (P/E, ROE, etc.)
- Sentiment scores (news, social, analyst)
- Aggregated signals with combined score

### Backtests Tab
- Run backtests via API
- Configure strategy parameters
- View equity curve
- Trade history
- Performance metrics

## Architecture

```
frontend/
├── app.py              # Main Streamlit application
├── api_client.py       # API client for backend
└── requirements.txt    # Dependencies
```

The frontend is completely decoupled from the backend. All data flows through REST API calls.
