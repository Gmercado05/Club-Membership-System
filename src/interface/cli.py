"""Command-line interface for the Club Membership System.

The interface layer collects raw text input from the user, forwards it to
process_request(), and formats the engine response for display.
"""

from __future__ import annotations

# Import process_request at the top so the path
# "src.interface.cli.process_request" is valid in tests.
from src.engine.engine import process_request

_WELCOME_BANNER = """
========================================
  Club Membership System
  Type 'quit' or 'exit' to stop.
========================================
"""

_HELP_TEXT = (
    "I can help you:\n"
    "  - Register a new member\n"
    "  - List all registered members\n"
    "  - Search/filter registered members\n"
    "  - Check membership status\n"
    "  - Renew a membership\n"
    "  - Update member details\n"
    "  - Remove a member\n"
    "  - Generate membership reports\n"
    "Just describe what you want in plain English."
)


def format_response(result: dict) -> str:
    """Convert an engine result dict to a human-readable string.

    Args:
        result (dict): Engine result from `process_request`.

    Returns:
        str: Terminal-friendly text for `"success"`, `"exists"`,
        `"incomplete"`, `"not_found"`, `"unknown"`, and `"error"` results.
        Unknown status values fall back to the result message.
    """
    status = result.get("status")
    message = result.get("message", "Unexpected response.")

    if status == "success":
        data = result.get("data")
        if isinstance(data, list) and data:
            lines = [message]
            for item in data:
                name = item.get("name", "Unknown")
                email = item.get("email", "Unknown")
                lines.append(f"  - {name} ({email})")
            return "\n".join(lines)
        # Report data may be a mapping of major->count
        if isinstance(data, dict) and data:
            lines = [message]
            for key, val in sorted(data.items()):
                lines.append(f"  - {key}: {val}")
            return "\n".join(lines)
        return message

    if status == "exists":
        return message

    if status == "incomplete":
        missing = result.get("missing") or []
        missing_text = ", ".join(str(field) for field in missing)
        return f"{message}\n  Missing: {missing_text}" if missing_text else message

    if status == "unknown":
        return f"{message}\n\n{_HELP_TEXT}"

    return message


def run_session(process_fn=None):
    """Run the interactive command-line session.

    Args:
        process_fn (callable | None): Function that accepts user input as
            `str` and returns an engine result `dict`. Defaults to
            `process_request`; tests can inject a mock to avoid live AI and
            Google Sheets calls.

    Returns:
        None: Prints output until the user enters `quit`, `exit`, sends EOF, or
        the input stream returns `None`.
    """
    if process_fn is None:
        process_fn = process_request

    print(_WELCOME_BANNER)

    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            print("Goodbye!")
            return

        if user_input is None:
            print("Goodbye!")
            return

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            return

        result = process_fn(user_input)
        print("Assistant: " + format_response(result))
        print()


if __name__ == "__main__":  # pragma: no cover
    run_session()
