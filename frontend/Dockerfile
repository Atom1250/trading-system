# Frontend Dockerfile
FROM python:3.10-slim

WORKDIR /app
# Force rebuild layer
ENV REFRESHED_AT=2025-12-02

# Install system dependencies
RUN apt-get update --fix-missing && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
