"""Data API models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PriceData(BaseModel):
    """Price data point."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class PriceDataResponse(BaseModel):
    """Price data API response."""

    symbol: str
    source: str
    data: list[PriceData]
    count: int


class DataSourceInfo(BaseModel):
    """Data source information."""

    name: str
    description: str
    available: bool


class PriceDataRequest(BaseModel):
    """Price data request."""

    symbol: str = Field(..., description="Stock symbol")
    source: Optional[str] = Field(
        None,
        description="Data source (fmp, yahoo, kaggle, local)",
    )
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    validate_data: bool = Field(True, description="Validate and clean data")
