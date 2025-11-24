import os

from dotenv import load_dotenv

load_dotenv()

# Required API key for Alpha Vantage requests. Read from environment or .env.
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Allow overriding the base URL via environment for testing, defaulting to production.
BASE_URL = os.getenv("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")
