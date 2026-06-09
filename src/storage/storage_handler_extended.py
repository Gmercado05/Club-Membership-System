"""Read, delete, search, and report member records from Google Sheets."""

from __future__ import annotations

from datetime import date, datetime

import gspread

from src.storage.sheet_client import open_sheet

SEARCHABLE_FIELDS = {
    "id",
    "name",
    "email",
    "student_id",
    "major",
    "year",
    "membership_status",
}


def _open_sheet() -> gspread.Worksheet:
    """Return the configured worksheet.

    This wrapper keeps tests able to patch
    `src.storage.storage_handler_extended._open_sheet`.
    """
    return open_sheet()


def get_members() -> list[dict]:
    """Fetch all stored club member records.

    Returns:
        list[dict]: Member records keyed by the sheet header row, or `[]` when
        the sheet has no data rows or any storage operation fails.
    """
    try:
        sheet = _open_sheet()
        return sheet.get_all_records()
    except Exception:
        return []


def delete_member(email: str) -> str:
    """Delete the first stored member row whose email or ID matches.

    Args:
        email (str): Email address used to find the member row.

    Returns:
        str: `"success"` when a matching row is deleted, `"not_found"` when no
        non-header row matches `email`, or `"error"` when any storage operation
        fails.
    """
    try:
        sheet = _open_sheet()
        email = str(email).strip()
        if not email:
            return "not_found"

        headers = sheet.row_values(1)
        cell = None
        for lookup_header in ("email", "id", "student_id"):
            if lookup_header in headers:
                cell = sheet.find(email, in_column=headers.index(lookup_header) + 1)
                if cell is not None:
                    break
        if cell is None and not headers:
            cell = sheet.find(email, in_column=2)
        if cell is None:
            return "not_found"
        if cell.row == 1:
            return "not_found"
        sheet.delete_rows(cell.row)
        return "success"
    except Exception:
        return "error"


def get_stats_by_major() -> dict:
    """Count stored members by major.

    Returns:
        dict: Mapping of `major -> count`. Members with a blank major are
        grouped under `"(Unknown)"`. Returns `{}` when any storage operation
        fails.
    """
    try:
        members = get_members()
        stats: dict = {}
        for m in members:
            major = (m.get("major") or "").strip()
            if not major:
                major = "(Unknown)"
            stats[major] = stats.get(major, 0) + 1
        return stats
    except Exception:
        return {}


def search_members(filters: dict) -> list[dict]:
    """Find members matching all provided filter values.

    Args:
        filters (dict): Field names and desired values. Empty or blank filter
            values are ignored.

    Returns:
        list[dict]: Members whose field values contain every non-empty filter
        value using case-insensitive substring matching. Empty `filters` returns
        all members. Returns `[]` when any storage operation fails.
    """
    try:
        members = get_members()
        if not filters:
            return members

        normalized_filters = {
            key: str(value).strip().lower()
            for key, value in filters.items()
            if key in SEARCHABLE_FIELDS and value is not None and str(value).strip()
        }
        if not normalized_filters:
            return members

        def matches(member: dict) -> bool:
            for key, filter_value in normalized_filters.items():
                member_value = str(member.get(key, "")).strip().lower()
                if filter_value not in member_value:
                    return False
            return True

        return [member for member in members if matches(member)]
    except Exception:
        return []


def get_member_by_lookup(member_lookup: str) -> dict | None:
    """Find one member by email, generated member ID, or student ID."""
    try:
        lookup = str(member_lookup).strip().lower()
        if not lookup:
            return None

        for member in get_members():
            values = [
                member.get("email", ""),
                member.get("id", ""),
                member.get("student_id", ""),
            ]
            if any(str(value).strip().lower() == lookup for value in values):
                return member
        return None
    except Exception:
        return None


def get_stats_by_status() -> dict:
    """Count stored members by calculated membership status."""
    try:
        stats: dict = {}
        for member in get_members():
            status = _calculated_membership_status(member)
            stats[status] = stats.get(status, 0) + 1
        return stats
    except Exception:
        return {}


def _calculated_membership_status(member: dict) -> str:
    """Calculate status from expiration date, falling back to stored status."""
    expiration_text = str(member.get("expiration_date") or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            expiration = datetime.strptime(expiration_text, fmt).date()
            return "active" if expiration >= date.today() else "expired"
        except ValueError:
            continue
    return str(member.get("membership_status") or "").strip() or "(Unknown)"
