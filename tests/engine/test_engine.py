"""Unit tests for the engine layer (Tool Use + Reflection patterns).

Storage functions and Gemini API calls are mocked to enable fast, reliable testing
without requiring Google Sheets credentials or consuming API quota.

Run:
    pytest tests/engine/test_engine.py -v

Key concept: the patch path is "src.engine.engine.<function>" because that is
where the function is USED (imported), not where it is defined.
"""

import json
from unittest.mock import MagicMock, patch

from src.engine.engine import process_request


def mock_gemini_response(intent: str, data: dict, complete: bool, missing: list = None):
    """Create a mock Gemini GenerativeModel that returns analysis JSON."""
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


# ---------------------------------------------------------------------------
# Test 1: Register — success path
# ---------------------------------------------------------------------------
def test_register_success_returns_correct_status():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="register",
            data={"name": "Alice Chen", "email": "alice@ucr.edu", "student_id": "12345", "major": "CS"},
            complete=True,
        )
        with patch("src.engine.engine.save_member", return_value="success"):
            result = process_request(
                "Register Alice Chen, email alice@ucr.edu, student_id 12345, CS major."
            )
    assert result["status"] == "success"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 2: Register — duplicate path
# ---------------------------------------------------------------------------
def test_register_duplicate_returns_exists_status():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="register",
            data={"name": "Alice Chen", "email": "alice@ucr.edu", "student_id": "12345", "major": "CS"},
            complete=True,
        )
        with patch("src.engine.engine.save_member", return_value="exists"):
            result = process_request(
                "Register Alice Chen, email alice@ucr.edu, student_id 12345, CS major."
            )
    assert result["status"] == "exists"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 3: List members
# ---------------------------------------------------------------------------
def test_list_members_returns_success_with_data():
    mock_members = [
        {"name": "Alice", "email": "alice@ucr.edu", "student_id": "12345", "major": "CS"}
    ]
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="list",
            data={},
            complete=True,
        )
        with patch("src.engine.engine.get_members", return_value=mock_members):
            result = process_request("Show me all registered members.")
    assert result["status"] == "success"
    assert isinstance(result["data"], list)


# ---------------------------------------------------------------------------
# Test 4: Reflection — incomplete registration blocks storage call
# ---------------------------------------------------------------------------
def test_incomplete_registration_is_blocked_before_storage():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="register",
            data={"name": "Bob"},
            complete=False,
            missing=["email", "student_id", "major"],
        )
        with patch("src.engine.engine.save_member") as mock_save:
            result = process_request("Register Bob.")  # Missing email, student_id, major
    assert result["status"] == "incomplete"
    assert "missing" in result
    # The Reflection step must prevent save_member from ever being called.
    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: Unknown intent — graceful fallback
# ---------------------------------------------------------------------------
def test_unknown_intent_returns_unknown_status():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="unknown",
            data={},
            complete=True,
        )
        result = process_request("What is the meaning of life?")
    assert result["status"] == "unknown"
    assert "message" in result
