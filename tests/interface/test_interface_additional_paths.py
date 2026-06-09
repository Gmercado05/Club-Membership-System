from src.interface import cli
from src.interface.cli import format_response, run_session


def test_format_error_or_not_found_returns_message():
    assert format_response({"status": "error", "message": "Storage error.", "data": None}) == "Storage error."
    assert format_response({"status": "not_found", "message": "Member not found.", "data": None}) == "Member not found."


def test_format_success_with_empty_data_returns_message_only():
    output = format_response({"status": "success", "message": "0 member(s) found.", "data": []})
    assert output == "0 member(s) found."


def test_run_session_uses_default_process_request(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "quit")
    monkeypatch.setattr(cli, "process_request", lambda user_input: {"status": "error", "message": "unused"})

    run_session()

    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out


def test_run_session_handles_eof(monkeypatch, capsys):
    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    run_session(process_fn=lambda user_input: {"status": "error", "message": "unused"})

    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out


def test_run_session_ignores_blank_input(monkeypatch, capsys):
    calls = []

    def mock_engine(user_input):
        calls.append(user_input)
        return {"status": "success", "message": "Handled.", "data": None}

    inputs = iter(["   ", "List members.", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_session(process_fn=mock_engine)

    captured = capsys.readouterr()
    assert calls == ["List members."]
    assert "Handled." in captured.out


def test_run_session_handles_none_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: None)

    run_session(process_fn=lambda user_input: {"status": "error", "message": "unused"})

    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out
