"""Unit tests for the interface layer.

The engine layer is mocked — these tests run without a Gemini API key or
Google Sheets credentials.
"""

from src.interface.cli import format_response, run_session


def test_format_success_with_member_list_shows_name_and_email():
    result = {
        "status": "success",
        "message": "2 member(s) found.",
        "data": [
            {"name": "Alice Chen", "email": "alice@ucr.edu", "student_id": "12345", "major": "CS"},
            {"name": "Bob Smith", "email": "bob@ucr.edu", "student_id": "67890", "major": "EE"},
        ],
    }
    output = format_response(result)
    assert "Alice Chen" in output
    assert "alice@ucr.edu" in output
    assert "Bob Smith" in output


def test_format_exists_shows_duplicate_message():
    result = {"status": "exists", "message": "Member already registered.", "data": None}
    output = format_response(result)
    assert "already registered" in output


def test_format_incomplete_lists_all_missing_fields():
    result = {
        "status": "incomplete",
        "message": "Missing required fields.",
        "missing": ["email", "student_id"],
    }
    output = format_response(result)
    assert "email" in output
    assert "student_id" in output


def test_format_unknown_includes_help_text():
    result = {
        "status": "unknown",
        "message": "I can register, list, or delete members.",
        "data": None,
    }
    output = format_response(result)
    assert "register" in output.lower() or "list" in output.lower() or "delete" in output.lower()


def test_run_session_prints_formatted_engine_response(monkeypatch, capsys):
    def mock_engine(user_input):
        return {"status": "success", "message": "Member registered.", "data": None}

    inputs = iter(["Register Alice Chen, alice@ucr.edu, student_id 12345, CS major.", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_session(process_fn=mock_engine)

    captured = capsys.readouterr()
    assert "Member registered." in captured.out
