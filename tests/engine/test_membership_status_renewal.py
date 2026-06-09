import json
from unittest.mock import MagicMock, patch

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


def test_status_returns_active_for_future_expiration():
    member = {
        "id": "member_alice",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "expiration_date": "2099-06-01",
    }

    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="status",
            data={"member_lookup": "alice@example.com"},
            complete=True,
        )
        with patch("src.engine.engine.get_member_by_lookup", return_value=member):
            result = process_request("Check membership status for alice@example.com.")

    assert result["status"] == "active"
    assert result["data"]["membership_status"] == "active"


def test_status_returns_expired_for_past_expiration():
    member = {
        "id": "member_alice",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "expiration_date": "2000-06-01",
    }

    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="status",
            data={"member_lookup": "alice@example.com"},
            complete=True,
        )
        with patch("src.engine.engine.get_member_by_lookup", return_value=member):
            result = process_request("Check membership status for alice@example.com.")

    assert result["status"] == "expired"


def test_renew_membership_updates_expiration_date():
    member = {
        "id": "member_alice",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "expiration_date": "2099-06-01",
    }

    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="renew",
            data={"member_lookup": "alice@example.com", "expiration_date": "2100-06-01"},
            complete=True,
        )
        with patch("src.engine.engine.get_member_by_lookup", return_value=member):
            with patch("src.engine.engine.update_member", return_value="success") as mock_update:
                result = process_request("Renew alice@example.com until 2100-06-01.")

    assert result["status"] == "success"
    assert result["data"]["expiration_date"] == "2100-06-01"
    mock_update.assert_called_once()


def test_renew_rejects_date_before_current_expiration():
    member = {
        "id": "member_alice",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "expiration_date": "2099-06-01",
    }

    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="renew",
            data={"member_lookup": "alice@example.com", "expiration_date": "2098-06-01"},
            complete=True,
        )
        with patch("src.engine.engine.get_member_by_lookup", return_value=member):
            with patch("src.engine.engine.update_member") as mock_update:
                result = process_request("Renew alice@example.com until 2098-06-01.")

    assert result["status"] == "validation_error"
    mock_update.assert_not_called()


def test_malformed_model_json_falls_back_for_expired_registration_prompt():
    response_obj = MagicMock()
    response_obj.text = '{"intent": "register", "data": {"name": "John'

    model_mock = MagicMock()
    model_mock.generate_content.return_value = response_obj

    with patch("src.engine.engine.genai.GenerativeModel", return_value=model_mock):
        with patch("src.engine.engine.save_member", return_value="success") as mock_save:
            result = process_request(
                "Register John Doe, john@example.com, Computer Science major, "
                "junior, start date 2023-01-01, expiration date 2024-01-01."
            )

    assert result["status"] == "success"
    saved_member = mock_save.call_args.args[0]
    assert saved_member["name"] == "John Doe"
    assert saved_member["email"] == "john@example.com"
    assert saved_member["expiration_date"] == "2024-01-01"
    assert saved_member["membership_status"] == "expired"
