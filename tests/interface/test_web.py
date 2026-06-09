from src.interface.web import create_app


def test_index_page_loads():
    app = create_app(process_fn=lambda message: {"status": "success", "message": "ok", "data": None})

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"Club Membership System" in response.data


def test_api_request_returns_formatted_engine_response():
    def mock_engine(message):
        assert message == "Show me all members."
        return {
            "status": "success",
            "message": "1 member(s) found.",
            "data": [{"name": "Alice Chen", "email": "alice@ucr.edu"}],
        }

    app = create_app(process_fn=mock_engine)

    with app.test_client() as client:
        response = client.post("/api/request", json={"message": "Show me all members."})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["result"]["status"] == "success"
    assert "Alice Chen" in payload["formatted"]


def test_api_request_handles_blank_message_without_engine_call():
    calls = []

    def mock_engine(message):
        calls.append(message)
        return {"status": "success", "message": "should not run", "data": None}

    app = create_app(process_fn=mock_engine)

    with app.test_client() as client:
        response = client.post("/api/request", json={"message": "   "})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["result"]["status"] == "incomplete"
    assert calls == []
