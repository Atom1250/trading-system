# FastAPI Backend

Backend API server for the trading system.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
# Development server with auto-reload
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

By default, uses SQLite (`trading_system.db`). To use PostgreSQL:

```bash
export DATABASE_URL="postgresql://user:password@localhost/trading_system"
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── api/
│   └── v1/                # API v1 endpoints
│       ├── portfolios.py
│       ├── strategies.py
│       ├── signals.py
│       ├── ai.py
│       └── data.py
├── db/
│   ├── database.py        # Database configuration
│   └── models.py          # SQLAlchemy models
├── models/
│   └── portfolio.py       # Pydantic models
├── services/
│   └── portfolio_service.py  # Business logic
└── requirements.txt
```
