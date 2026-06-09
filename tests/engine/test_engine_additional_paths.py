import json
from unittest.mock import MagicMock, patch

import pytest

from src.engine.engine import process_request


def mock_gemini_response(intent: str, data: dict, complete: bool, missing: list = None):
    if missing is None:
        missing = []

    response_obj = MagicMock()
    response_obj.text = json.dumps({
        "intent": intent,
        "data": data,
        "complete": complete,
        "missing": missing,
    })

    model_mock = MagicMock()
    model_mock.generate_content.return_value = response_obj
    return model_mock


def test_register_storage_error_returns_error_status():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="register",
            data={"name": "Alice", "email": "alice@ucr.edu", "student_id": "1", "major": "CS"},
            complete=True,
        )
        with patch("src.engine.engine.save_member", return_value="error"):
            result = process_request("Register Alice.")

    assert result["status"] == "error"


def test_delete_success_not_found_and_error_paths():
    cases = [
        ("success", "success"),
        ("not_found", "not_found"),
        ("error", "error"),
    ]

    for storage_status, expected_status in cases:
        with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
            mock_model_class.return_value = mock_gemini_response(
                intent="delete",
                data={"email": "alice@ucr.edu"},
                complete=True,
            )
            with patch("src.engine.engine.delete_member", return_value=storage_status):
                result = process_request("Delete alice@ucr.edu.")

        assert result["status"] == expected_status


def test_update_incomplete_when_no_update_fields_are_present():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="update",
            data={"email": "alice@ucr.edu"},
            complete=True,
        )
        result = process_request("Update alice@ucr.edu.")

    assert result["status"] == "incomplete"
    assert "missing" in result


def test_update_not_found_and_error_paths():
    cases = [
        ("not_found", "not_found"),
        ("error", "error"),
    ]

    for storage_status, expected_status in cases:
        with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
            mock_model_class.return_value = mock_gemini_response(
                intent="update",
                data={"email": "alice@ucr.edu", "major": "Math"},
                complete=True,
            )
            with patch("src.engine.engine.update_member", return_value=storage_status):
                result = process_request("Update alice@ucr.edu to Math.")

        assert result["status"] == expected_status


def test_model_exception_returns_error_status():
    with patch("src.engine.engine.genai.GenerativeModel", side_effect=ValueError("model unavailable")):
        result = process_request("Show members.")

    assert result["status"] == "error"
    assert "model unavailable" in result["message"]


def test_not_implemented_error_is_not_swallowed():
    with patch("src.engine.engine.genai.GenerativeModel", side_effect=NotImplementedError):
        with pytest.raises(NotImplementedError):
            process_request("Show members.")
