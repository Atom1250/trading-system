#!/bin/bash
# Startup script for Streamlit frontend

cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update requirements
pip install -r requirements.txt

# Start Streamlit
streamlit run app.py
