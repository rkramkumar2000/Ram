#!/usr/bin/env python3
"""
Google Sheets client for accessing and reading spreadsheet data.
"""

import gspread
from google.oauth2.service_account import Credentials

class SheetsClient:
    def __init__(self, credentials_path):
        """Initialize the Google Sheets client."""
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = Credentials.from_service_account_file(
            credentials_path, scopes=self.scope
        )
        self.client = gspread.authorize(self.credentials)

    def get_sheet_data(self, spreadsheet_id, sheet_name='Sheet1'):
        """Fetch data from specified Google Sheet."""
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            raise Exception(f"Error fetching sheet data: {str(e)}")

    def get_sheet_structure(self, spreadsheet_id, sheet_name='Sheet1'):
        """Get column headers and data types from the sheet."""
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            headers = worksheet.row_values(1)
            return headers
        except Exception as e:
            raise Exception(f"Error getting sheet structure: {str(e)}")