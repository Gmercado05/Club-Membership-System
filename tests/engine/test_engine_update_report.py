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


def test_update_member_success():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="update",
            data={"email": "alice@ucr.edu", "major": "Math"},
            complete=True,
        )
        with patch("src.engine.engine.update_member", return_value="success"):
            result = process_request("Update alice@ucr.edu to major Math")
    assert result["status"] == "success"


def test_update_expiration_date_also_updates_membership_status():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="update",
            data={"email": "alice@ucr.edu", "expiration_date": "2099-01-01"},
            complete=True,
        )
        with patch("src.engine.engine.update_member", return_value="success") as mock_update:
            result = process_request("Update alice@ucr.edu to expiration date 2099-01-01")

    assert result["status"] == "success"
    assert mock_update.call_args.args[1]["expiration_date"] == "2099-01-01"
    assert mock_update.call_args.args[1]["membership_status"] == "active"


def test_report_returns_stats():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="report",
            data={},
            complete=True,
        )
        with patch("src.engine.engine.get_stats_by_major", return_value={"CS": 2, "EE": 1}):
            result = process_request("Give me a report of members by major")
    assert result["status"] == "success"
    assert isinstance(result["data"], dict)
    assert result["data"]["CS"] == 2


def test_search_members_returns_filtered_list():
    with patch("src.engine.engine.genai.GenerativeModel") as mock_model_class:
        mock_model_class.return_value = mock_gemini_response(
            intent="search",
            data={"major": "CS"},
            complete=True,
        )
        with patch("src.engine.engine.search_members", return_value=[{"name": "Alice", "email": "alice@ucr.edu", "major": "CS"}]):
            result = process_request("Show me members in CS")
    assert result["status"] == "success"
    assert isinstance(result["data"], list)
    assert result["data"][0]["major"] == "CS"
