"""Google Sheets integration service."""
import os
import json
from typing import List, Dict, Any, Optional
import pandas as pd
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

class GoogleSheetsService:
    """Service for interacting with Google Sheets."""
    
    def __init__(self, credentials_path: str = "/app/config/credentials.json"):
        self.credentials_path = credentials_path
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        if not gspread or not Credentials:
            print("gspread or google-auth not installed.")
            return

        if not os.path.exists(self.credentials_path):
            print(f"Credentials file not found at {self.credentials_path}")
            return
            
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            self.client = gspread.authorize(creds)
        except Exception as e:
            print(f"Failed to authenticate with Google Sheets: {e}")

    def is_connected(self) -> bool:
        """Check if connected to Google Sheets."""
        return self.client is not None

    def export_portfolio(self, portfolio_data: Dict[str, Any], spreadsheet_name: str = "Trading Portfolio"):
        """Export portfolio data to a Google Sheet."""
        if not self.is_connected():
            raise RuntimeError("Not connected to Google Sheets. Check credentials.")
            
        try:
            # Open or create spreadsheet
            try:
                sh = self.client.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                sh = self.client.create(spreadsheet_name)
                # Share with user email if possible, but we don't have it here easily without more config
            
            # Export Positions
            positions = portfolio_data.get("positions", [])
            if positions:
                df_pos = pd.DataFrame(positions)
                worksheet = self._get_or_create_worksheet(sh, "Positions")
                worksheet.clear()
                worksheet.update([df_pos.columns.values.tolist()] + df_pos.values.tolist())
                
            # Export Trades
            trades = portfolio_data.get("trades", [])
            if trades:
                df_trades = pd.DataFrame(trades)
                worksheet = self._get_or_create_worksheet(sh, "Trades")
                worksheet.clear()
                worksheet.update([df_trades.columns.values.tolist()] + df_trades.values.tolist())
                
            return {"status": "success", "spreadsheet_url": sh.url}
            
        except Exception as e:
            raise RuntimeError(f"Failed to export to Google Sheets: {e}")

    def _get_or_create_worksheet(self, sh, title):
        try:
            return sh.worksheet(title)
        except gspread.WorksheetNotFound:
            return sh.add_worksheet(title=title, rows=100, cols=20)

# Global instance
google_sheets_service = GoogleSheetsService()
