"""Web interface for the Club Membership System."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from src.engine.engine import process_request
from src.interface.cli import format_response


def create_app(process_fn=None) -> Flask:
    """Create the Flask application.

    Args:
        process_fn: Optional engine-compatible callable used by tests to avoid
            live Gemini or Google Sheets calls.

    Returns:
        Flask: Configured web application.
    """
    app = Flask(__name__)
    engine_fn = process_fn or process_request

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/request")
    def handle_request():
        payload = request.get_json(silent=True) or {}
        user_input = str(payload.get("message", "")).strip()

        if not user_input:
            result = {
                "status": "incomplete",
                "message": "Enter a request first.",
                "missing": ["message"],
            }
        else:
            result = engine_fn(user_input)

        return jsonify(
            {
                "result": result,
                "formatted": format_response(result),
            }
        )

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
