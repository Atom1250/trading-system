#!/bin/sh
set -e

MODE="${RUN_MODE:-console}"

if [ "$MODE" = "streamlit" ]; then
  echo "Starting Streamlit UI on port 8501..."
  exec streamlit run ui_streamlit.py --server.port=8501 --server.address=0.0.0.0
else
  echo "Starting console backtester..."
  exec python run_strategy.py
fi
