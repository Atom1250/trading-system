"""Export service for CSV and Excel."""
import pandas as pd
from typing import Dict, Any, Optional
import io
import json

class ExportService:
    """Service for exporting data to files."""
    
    def export_portfolio(self, portfolio_data: Dict[str, Any], format: str = "csv") -> bytes:
        """
        Export portfolio data to CSV or Excel.
        Returns bytes content of the file.
        """
        positions = portfolio_data.get("positions", [])
        trades = portfolio_data.get("trades", [])
        
        df_positions = pd.DataFrame(positions)
        df_trades = pd.DataFrame(trades)
        
        output = io.BytesIO()
        
        if format.lower() == "csv":
            # For CSV, we can only return one "sheet", so we'll return positions by default
            # Or we could return a zip, but let's keep it simple: positions only for CSV
            if not df_positions.empty:
                df_positions.to_csv(output, index=False)
            else:
                output.write(b"No positions data")
        
        elif format.lower() == "excel" or format.lower() == "xlsx":
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not df_positions.empty:
                    df_positions.to_excel(writer, sheet_name='Positions', index=False)
                if not df_trades.empty:
                    df_trades.to_excel(writer, sheet_name='Trades', index=False)
                
                # Add summary sheet
                summary = {
                    "Total Value": portfolio_data.get("total_value"),
                    "Cash": portfolio_data.get("cash"),
                    "Name": portfolio_data.get("name")
                }
                pd.DataFrame([summary]).to_excel(writer, sheet_name='Summary', index=False)
                
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return output.getvalue()

# Global instance
export_service = ExportService()
