"""Write and update member records in Google Sheets."""

from __future__ import annotations

import gspread

from src.storage.sheet_client import open_sheet

REQUIRED_KEYS = ("name", "email")
MEMBER_FIELDS = (
    "id",
    "name",
    "email",
    "major",
    "year",
    "start_date",
    "expiration_date",
    "membership_status",
    "student_id",
)


def _open_sheet() -> gspread.Worksheet:
    """Return the configured worksheet.

    This wrapper keeps tests able to patch `src.storage.storage_handler._open_sheet`
    while the connection details live in one shared module.
    """
    return open_sheet()


def _find_member_row(sheet: gspread.Worksheet, member_lookup: str) -> int | None:
    """Return the row number matching an email, member ID, or student ID."""
    lookup = str(member_lookup).strip().lower()
    if not lookup:
        return None

    headers = sheet.row_values(1)
    if headers:
        lookup_headers = ("email", "id", "student_id")
        records = sheet.get_all_records()
        for row_index, record in enumerate(records, start=2):
            for header in lookup_headers:
                if header in headers and str(record.get(header, "")).strip().lower() == lookup:
                    return row_index
        return None

    cell = sheet.find(str(member_lookup).strip(), in_column=2)
    if cell is None or cell.row == 1:
        return None
    return cell.row


def save_member(member_data: dict) -> str:
    """Save a new club member row to Google Sheets.

    Args:
        member_data (dict): Member fields containing `name`, `email`,
            `student_id`, and `major`.

    Returns:
        str: `"success"` when the row is appended, `"exists"` when another
        row already has the same email address, or `"error"` when required
        keys are missing or any storage operation fails.
    """
    try:
        if not all(str(member_data.get(key, "")).strip() for key in REQUIRED_KEYS):
            return "error"

        sheet = _open_sheet()
        existing_records = sheet.get_all_records()

        email_lower = str(member_data.get("email", "")).strip().lower()
        for record in existing_records:
            if str(record.get("email", "")).strip().lower() == email_lower:
                return "exists"

        member_data = dict(member_data)
        member_data["email"] = email_lower

        headers = sheet.row_values(1)
        if headers:
            row_data = [str(member_data.get(header, "")).strip() for header in headers]
        else:
            row_data = [str(member_data.get(field, "")).strip() for field in MEMBER_FIELDS]
        sheet.append_row(row_data)

        return "success"
    except Exception:
        # Convert all exceptions to "error" per contract
        return "error"


def update_member(email: str, updates: dict) -> str:
    """Update stored fields for the member row matching an email address.

    Args:
        email (str): Email address used to find the member row.
        updates (dict): Field names and replacement values to write. Keys that
            are not present in the sheet header are ignored.

    Returns:
        str: `"success"` when a matching row is updated, `"not_found"` when no
        non-header row matches `email`, or `"error"` when any storage operation
        fails.
    """
    try:
        sheet = _open_sheet()
        email = str(email).strip()
        clean_updates = {
            key: str(value).strip()
            for key, value in updates.items()
            if key in MEMBER_FIELDS and key != "email" and str(value).strip()
        }
        if not email or not clean_updates:
            return "error"

        headers = sheet.row_values(1)
        row_index = _find_member_row(sheet, email)
        if row_index is None:
            return "not_found"

        for key, val in clean_updates.items():
            if key in headers:
                col = headers.index(key) + 1
                sheet.update_cell(row_index, col, val)

        return "success"
    except Exception:
        return "error"
