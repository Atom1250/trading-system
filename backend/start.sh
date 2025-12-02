#!/bin/bash
# Startup script for FastAPI backend

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Initialize database
python -c "from db.database import init_db; init_db(); print('Database initialized')"

# Start server
uvicorn main:app --reload --port 8000
