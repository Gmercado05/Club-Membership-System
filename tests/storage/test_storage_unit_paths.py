from types import SimpleNamespace
from unittest.mock import patch

from src.storage.storage_handler import save_member, update_member
from src.storage.storage_handler_extended import (
    delete_member,
    get_member_by_lookup,
    get_members,
    get_stats_by_major,
    get_stats_by_status,
    search_members,
)


class FakeStorageSheet:
    def __init__(self, records=None, cell=None, row_values=None):
        self.records = records or []
        self.cell = cell
        self.deleted_rows = []
        self.updated_cells = []
        self.appended_rows = []
        self._row_values = row_values or {
            1: ["name", "email", "student_id", "major"],
            2: ["Alice", "alice@ucr.edu"],
        }

    def get_all_records(self):
        return self.records

    def append_row(self, row):
        self.appended_rows.append(row)

    def find(self, email, in_column):
        return self.cell

    def delete_rows(self, row):
        self.deleted_rows.append(row)

    def row_values(self, row):
        return list(self._row_values.get(row, []))

    def update_cell(self, row, col, val):
        self.updated_cells.append((row, col, val))


def test_save_member_returns_error_when_append_fails():
    sheet = FakeStorageSheet()
    sheet.append_row = lambda row: (_ for _ in ()).throw(RuntimeError("append failed"))

    with patch("src.storage.storage_handler._open_sheet", return_value=sheet):
        result = save_member({"name": "Alice", "email": "alice@ucr.edu", "student_id": "1", "major": "CS"})

    assert result == "error"


def test_update_member_returns_not_found_for_missing_or_header_match():
    with patch("src.storage.storage_handler._open_sheet", return_value=FakeStorageSheet(cell=None)):
        assert update_member("missing@ucr.edu", {"major": "CS"}) == "not_found"

    header_cell = SimpleNamespace(row=1)
    with patch("src.storage.storage_handler._open_sheet", return_value=FakeStorageSheet(cell=header_cell)):
        assert update_member("email", {"major": "CS"}) == "not_found"


def test_update_member_updates_only_known_headers_and_pads_short_rows():
    sheet = FakeStorageSheet(cell=SimpleNamespace(row=2))

    with patch("src.storage.storage_handler._open_sheet", return_value=sheet):
        result = update_member("alice@ucr.edu", {"major": "Math", "unknown": "ignored"})

    assert result == "success"
    assert sheet.updated_cells == [(2, 4, "Math")]


def test_update_member_returns_error_when_sheet_fails():
    with patch("src.storage.storage_handler._open_sheet", side_effect=RuntimeError("sheet down")):
        assert update_member("alice@ucr.edu", {"major": "Math"}) == "error"


def test_get_members_returns_empty_list_on_storage_error():
    with patch("src.storage.storage_handler_extended._open_sheet", side_effect=RuntimeError("sheet down")):
        assert get_members() == []


def test_delete_member_handles_not_found_header_success_and_error():
    with patch("src.storage.storage_handler_extended._open_sheet", return_value=FakeStorageSheet(cell=None)):
        assert delete_member("missing@ucr.edu") == "not_found"

    header_cell = SimpleNamespace(row=1)
    with patch("src.storage.storage_handler_extended._open_sheet", return_value=FakeStorageSheet(cell=header_cell)):
        assert delete_member("email") == "not_found"

    sheet = FakeStorageSheet(cell=SimpleNamespace(row=3))
    with patch("src.storage.storage_handler_extended._open_sheet", return_value=sheet):
        assert delete_member("alice@ucr.edu") == "success"
    assert sheet.deleted_rows == [3]

    with patch("src.storage.storage_handler_extended._open_sheet", side_effect=RuntimeError("sheet down")):
        assert delete_member("alice@ucr.edu") == "error"


def test_get_stats_by_major_counts_blank_major_as_unknown():
    members = [{"major": "CS"}, {"major": "CS"}, {"major": ""}, {}]

    with patch("src.storage.storage_handler_extended.get_members", return_value=members):
        stats = get_stats_by_major()

    assert stats == {"CS": 2, "(Unknown)": 2}


def test_get_stats_by_major_returns_empty_dict_on_error():
    with patch("src.storage.storage_handler_extended.get_members", side_effect=RuntimeError("bad data")):
        assert get_stats_by_major() == {}


def test_get_member_by_lookup_matches_email_id_or_student_id():
    members = [
        {"id": "member_alice", "email": "alice@example.com", "student_id": "111"},
        {"id": "member_bob", "email": "bob@example.com", "student_id": "222"},
    ]

    with patch("src.storage.storage_handler_extended.get_members", return_value=members):
        assert get_member_by_lookup("alice@example.com") == members[0]
        assert get_member_by_lookup("member_bob") == members[1]
        assert get_member_by_lookup("111") == members[0]
        assert get_member_by_lookup("missing") is None


def test_get_stats_by_status_counts_blank_status_as_unknown():
    members = [{"membership_status": "active"}, {"membership_status": "expired"}, {}]

    with patch("src.storage.storage_handler_extended.get_members", return_value=members):
        assert get_stats_by_status() == {"active": 1, "expired": 1, "(Unknown)": 1}


def test_search_members_filters_case_insensitive_substrings_and_empty_filters():
    members = [
        {"name": "Alice Chen", "email": "alice@ucr.edu", "major": "Computer Science"},
        {"name": "Bob Smith", "email": "bob@ucr.edu", "major": "Math"},
    ]

    with patch("src.storage.storage_handler_extended.get_members", return_value=members):
        assert search_members({}) == members
        assert search_members({"major": "computer", "name": "ali"}) == [members[0]]
        assert search_members({"major": "physics"}) == []


def test_search_members_returns_empty_list_on_error():
    with patch("src.storage.storage_handler_extended.get_members", side_effect=RuntimeError("bad data")):
        assert search_members({"major": "CS"}) == []
