"""Data API endpoints."""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from services.data.price_service import PriceDataService
from models.data import PriceData, PriceDataResponse, DataSourceInfo

router = APIRouter()
price_service = PriceDataService()


@router.get("/sources", response_model=list[DataSourceInfo])
async def list_data_sources():
    """List available data sources."""
    sources = price_service.get_available_sources()
    return [
        DataSourceInfo(
            name=source,
            description=f"{source.upper()} data source",
            available=True
        )
        for source in sources
    ]


@router.get("/prices/{symbol}", response_model=PriceDataResponse)
async def get_prices(
    symbol: str,
    source: Optional[str] = Query(None, description="Data source (fmp, yahoo, kaggle, local)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    validate: bool = Query(True, description="Validate and clean data")
):
    """Get price data for a symbol."""
    try:
        df = price_service.get_prices(
            symbol=symbol,
            source=source,
            start=start_date,
            end=end_date,
            validate=validate
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol {symbol}"
            )
        
        # Convert DataFrame to list of PriceData
        price_data = []
        for date, row in df.iterrows():
            price_data.append(PriceData(
                date=date,
                open=float(row['open']) if pd.notna(row['open']) else 0.0,
                high=float(row['high']) if pd.notna(row['high']) else 0.0,
                low=float(row['low']) if pd.notna(row['low']) else 0.0,
                close=float(row['close']) if pd.notna(row['close']) else 0.0,
                volume=float(row['volume']) if pd.notna(row['volume']) else 0.0,
            ))
        
        return PriceDataResponse(
            symbol=symbol,
            source=source or "local",
            data=price_data,
            count=len(price_data)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error fetching data: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
