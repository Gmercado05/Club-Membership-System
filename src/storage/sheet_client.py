"""Google Sheets connection helpers for the storage layer."""

from __future__ import annotations

import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_ACCOUNT_PATH = PROJECT_ROOT / "service_account.json"
SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "club-membership-system-members")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def open_sheet() -> gspread.Worksheet:
    """Authenticate with Google and return the first configured worksheet."""
    creds = Credentials.from_service_account_file(str(SERVICE_ACCOUNT_PATH), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1
