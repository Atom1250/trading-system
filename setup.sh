#!/bin/bash
# Trading System Setup Script
# This script automates the initial setup of the trading system

set -e  # Exit on error

echo "========================================="
echo "Trading System Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if ! python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.10+ is required. Found: $PYTHON_VERSION"
    echo ""
    echo "Please install Python 3.10+ or use pyenv:"
    echo "  pyenv install 3.10.13"
    echo "  pyenv local 3.10.13"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python -m venv .venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create .env file
echo "Setting up environment configuration..."
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping creation."
    echo "   To reset, delete .env and run this script again."
else
    cp .env.example .env
    echo "✅ .env file created from .env.example"
    echo ""
    echo "📝 IMPORTANT: Edit .env to add your API keys (optional)"
    echo "   FMP API key: Get free key at https://financialmodelingprep.com/developer/docs/"
    echo "   Yahoo Finance works without API keys"
fi
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p data/prices data/fundamentals data/universe reports logs
echo "✅ Data directories created"
echo ""

# Verify installation
echo "Verifying installation..."
if python -c "import pandas, numpy, yfinance, ta, optuna, streamlit, backtesting" 2>/dev/null; then
    echo "✅ All core dependencies verified"
else
    echo "❌ Some dependencies failed to import"
    echo "   Try running: pip install -r requirements.txt"
    exit 1
fi
echo ""

# Success message
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. (Optional) Edit .env with your API keys:"
echo "     nano .env"
echo ""
echo "  3. Run a backtest:"
echo "     python run_strategy.py"
echo ""
echo "  4. Or launch the Streamlit UI:"
echo "     streamlit run ui_streamlit.py"
echo ""
echo "For more information, see README.md"
echo ""
