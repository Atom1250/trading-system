# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update --fix-missing && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY config/ ./config/
COPY ingestion/ ./ingestion/
COPY repository/ ./repository/
COPY backtesting/ ./backtesting/
COPY indicators/ ./indicators/
COPY strategy_lab/ ./strategy_lab/
COPY trading_backtester/ ./trading_backtester/
COPY utils/ ./utils/

# Set working directory to backend
WORKDIR /app/backend

# Add /app to PYTHONPATH so config can be imported
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

