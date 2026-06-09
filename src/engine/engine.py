"""Engine layer for natural-language club membership requests.

The engine owns application orchestration: it asks Gemini to extract intent
and fields from user text, verifies the extracted data against local rules,
and dispatches valid requests to the storage layer.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
import google.generativeai as genai

# Import storage functions at the top so tests can patch them via
# "src.engine.engine.save_member" (the path where they are USED).
from src.storage.storage_handler import save_member, update_member
from src.storage.storage_handler_extended import (
    delete_member,
    get_member_by_lookup,
    get_members,
    get_stats_by_major,
    get_stats_by_status,
    search_members,
)

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")

genai.configure(api_key=_API_KEY)

# --- Prompts ---

_SUPPORTED_INTENTS = {
    "register",
    "list",
    "delete",
    "remove",
    "update",
    "report",
    "search",
    "status",
    "renew",
    "unknown",
}
_REQUIRED_FIELDS = {
    "register": ("name", "email"),
    "delete": ("member_lookup",),
    "remove": ("member_lookup",),
    "update": ("member_lookup",),
    "status": ("member_lookup",),
    "renew": ("member_lookup", "expiration_date"),
}

_ANALYSIS_PROMPT = """
You are a Club Membership System engine. Analyze the user request and return strict JSON only.

Instructions:
- intent: exactly one of "register", "list", "delete", "remove", "update", "report", "search", "status", "renew", or "unknown"
- data: a dict containing only these fields when mentioned: id, member_lookup, name, email, student_id, major, year, start_date, expiration_date, membership_status
- For search requests, put the search filters in data using the same field names.
- For update requests, put the member email and only the fields to change in data.
- For status, renew, delete, and remove requests, put the email or ID in member_lookup.
- complete: true if the request includes the minimal required fields for the detected intent.
- register requires name and email.
- delete/remove/status requires member_lookup.
- renew requires member_lookup and expiration_date.
- update requires member_lookup and at least one changed field besides member_lookup.
- list, report, search, and unknown are complete by default.
- missing: a list of missing required fields when complete is false

Return exactly one JSON object with keys: intent, data, complete, missing.
""".strip()


def _result(status: str, message: str, data=None, missing: list[str] | None = None) -> dict:
    """Build the shared engine response shape."""
    response = {"status": status, "message": message}
    if missing is not None:
        response["missing"] = missing
    else:
        response["data"] = data
    return response


def _parse_analysis(response_text: str) -> dict:
    """Parse and normalize Gemini's JSON analysis response."""
    analysis = json.loads(response_text)
    if not isinstance(analysis, dict):
        raise ValueError("Gemini returned a non-object response.")

    intent = analysis.get("intent", "unknown")
    if intent not in _SUPPORTED_INTENTS:
        intent = "unknown"

    data = analysis.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    return {
        "intent": intent,
        "data": data,
        "complete": bool(analysis.get("complete", intent in {"list", "report", "search", "unknown"})),
        "missing": analysis.get("missing") if isinstance(analysis.get("missing"), list) else [],
    }


def _local_analysis(user_input: str) -> dict:
    """Best-effort parser for common membership commands.

    This is a fallback for quota/API/malformed-JSON failures from Gemini. It
    intentionally covers the standard demo flows and lets unsupported phrasing
    fall through as `unknown`.
    """
    text = str(user_input).strip()
    lowered = text.lower()
    data: dict = {}

    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""
    date_matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", text)

    if any(word in lowered for word in ("register", "add", "sign up")):
        if email:
            data["email"] = email
        name_part = text
        if email_match:
            name_part = text[:email_match.start()]
        name_part = re.sub(r"(?i)\b(register|add|sign up|member)\b", "", name_part)
        name = name_part.strip(" ,.-")
        if name:
            data["name"] = name
        major_match = re.search(r"(?i),?\s*([^,]+?)\s+major\b", text)
        if major_match:
            data["major"] = major_match.group(1).strip(" ,")
        year_match = re.search(r"(?i)\b(freshman|sophomore|junior|senior|graduate)\b", text)
        if year_match:
            data["year"] = year_match.group(1).title()
        start_match = re.search(r"(?i)start date\s+(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})", text)
        if start_match:
            data["start_date"] = start_match.group(1)
        expiration_match = re.search(r"(?i)expiration date\s+(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})", text)
        if expiration_match:
            data["expiration_date"] = expiration_match.group(1)
        missing = _missing_required_fields("register", data)
        return {"intent": "register", "data": data, "complete": not missing, "missing": missing}

    if "renew" in lowered:
        if email:
            data["member_lookup"] = email
        elif words := re.findall(r"\bmember_[\w-]+\b", lowered):
            data["member_lookup"] = words[0]
        if date_matches:
            data["expiration_date"] = date_matches[-1]
        missing = _missing_required_fields("renew", data)
        return {"intent": "renew", "data": data, "complete": not missing, "missing": missing}

    if "status" in lowered or "active" in lowered or "expired" in lowered:
        if email:
            data["member_lookup"] = email
        elif words := re.findall(r"\bmember_[\w-]+\b", lowered):
            data["member_lookup"] = words[0]
        missing = _missing_required_fields("status", data)
        return {"intent": "status", "data": data, "complete": not missing, "missing": missing}

    if any(word in lowered for word in ("remove", "delete")):
        if email:
            data["member_lookup"] = email
        elif words := re.findall(r"\bmember_[\w-]+\b", lowered):
            data["member_lookup"] = words[0]
        missing = _missing_required_fields("remove", data)
        return {"intent": "remove", "data": data, "complete": not missing, "missing": missing}

    if "report" in lowered:
        if "status" in lowered:
            data["membership_status"] = "report"
        return {"intent": "report", "data": data, "complete": True, "missing": []}

    if any(word in lowered for word in ("show", "list", "all members")):
        return {"intent": "list", "data": {}, "complete": True, "missing": []}

    return {"intent": "unknown", "data": {}, "complete": True, "missing": []}


def _lookup_value(data: dict) -> str:
    return str(data.get("member_lookup") or data.get("email") or data.get("id") or data.get("student_id") or "").strip()


def _missing_required_fields(intent: str, data: dict) -> list[str]:
    """Return locally detected missing fields for mutating intents."""
    missing = []
    for field in _REQUIRED_FIELDS.get(intent, ()):
        if field == "member_lookup":
            if not _lookup_value(data):
                missing.append(field)
        elif not str(data.get(field, "")).strip():
            missing.append(field)
    if intent == "update":
        update_fields = ["name", "student_id", "major", "year", "start_date", "expiration_date"]
        if not any(str(data.get(field, "")).strip() for field in update_fields):
            missing.append("field_to_update")
    return missing


def _is_valid_email(email: str) -> bool:
    """Return whether `email` has a basic valid email shape."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(email).strip()))


def _parse_date(value: str) -> date | None:
    """Parse a date in common ISO or slash-separated formats."""
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _format_date(value: date) -> str:
    return value.isoformat()


def _normalize_member_data(data: dict) -> dict:
    """Fill membership defaults for a registration payload."""
    normalized = {key: str(value).strip() for key, value in data.items() if value is not None}
    email = normalized.get("email", "")
    if email:
        normalized.setdefault("id", f"member_{email.split('@', 1)[0].lower()}")

    start_date = _parse_date(normalized.get("start_date", "")) or date.today()
    expiration_date = _parse_date(normalized.get("expiration_date", "")) or (start_date + timedelta(days=365))

    normalized["start_date"] = _format_date(start_date)
    normalized["expiration_date"] = _format_date(expiration_date)
    normalized["membership_status"] = "active" if expiration_date >= date.today() else "expired"
    return normalized


def _membership_status(member: dict, today: date | None = None) -> str:
    """Calculate membership status from expiration date."""
    today = today or date.today()
    expiration = _parse_date(member.get("expiration_date", ""))
    if expiration is None:
        return str(member.get("membership_status") or "unknown").lower()
    return "active" if expiration >= today else "expired"


def process_request(user_input: str) -> dict:
    """Process a user request using Tool Use and Reflection patterns.

    Args:
        user_input (str): Natural-language command from the interface layer.

    Returns:
        dict: Engine result with at least `status` and `message`. Status values
        are `"success"`, `"exists"`, `"incomplete"`, `"not_found"`,
        `"unknown"`, or `"error"`. Successful list/search calls include
        `data: list[dict]`, successful report calls include `data: dict`,
        incomplete calls include `missing: list[str]`, and other terminal
        statuses include `data: None`.
    """
    try:
        # ----------------------------------------------------------------
        # Step 1 — Tool Use + Reflection: extract intent, data, and completeness
        # ----------------------------------------------------------------
        model = genai.GenerativeModel(
            _MODEL,
            system_instruction=_ANALYSIS_PROMPT,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=256,
            )
        )
        
        analysis_response = model.generate_content(user_input)
        try:
            analysis = _parse_analysis(analysis_response.text)
        except (json.JSONDecodeError, ValueError):
            analysis = _local_analysis(user_input)
        intent = analysis["intent"]
        data = analysis["data"]
        missing_fields = sorted(set(analysis["missing"] + _missing_required_fields(intent, data)))
        is_complete = analysis["complete"] and not missing_fields

        if not is_complete:
            return _result("incomplete", "Missing required fields.", missing=missing_fields)

        if intent == "register" and not _is_valid_email(data.get("email", "")):
            return _result("validation_error", "Invalid email format.")

        # ----------------------------------------------------------------
        # Step 3 — Dispatch: call the correct storage function
        # ----------------------------------------------------------------
        if intent == "register":
            member_data = _normalize_member_data(data)
            result = save_member(member_data)
            if result == "success":
                return _result("success", "Member registered.", member_data)
            elif result == "exists":
                return _result("exists", "Member already registered.")
            else:
                return _result("error", "Storage error.")

        elif intent == "list":
            members = get_members()
            return _result("success", f"{len(members)} member(s) found.", members)

        elif intent in {"delete", "remove"}:
            result = delete_member(_lookup_value(data))
            if result == "success":
                return _result("success", "Member removed successfully.")
            elif result == "not_found":
                return _result("not_found", "Member not found.")
            else:
                return _result("error", "Storage error.")

        elif intent == "update":
            member_lookup = _lookup_value(data)
            updates = {
                key: value
                for key, value in data.items()
                if key in {"name", "student_id", "major", "year", "start_date", "expiration_date"}
                and str(value).strip()
            }
            if "expiration_date" in updates:
                expiration = _parse_date(updates["expiration_date"])
                if expiration is None:
                    return _result("validation_error", "Invalid expiration date.")
                updates["expiration_date"] = _format_date(expiration)
                updates["membership_status"] = "active" if expiration >= date.today() else "expired"
            result = update_member(member_lookup, updates)
            if result == "success":
                return _result("success", "Member updated.")
            elif result == "not_found":
                return _result("not_found", "Member not found.")
            else:
                return _result("error", "Storage error.")

        elif intent == "search":
            matches = search_members(data)
            return _result("success", f"{len(matches)} member(s) found.", matches)

        elif intent == "report":
            stats = get_stats_by_status() if "status" in str(data).lower() else get_stats_by_major()
            return _result("success", "Report generated.", stats)

        elif intent == "status":
            member = get_member_by_lookup(_lookup_value(data))
            if not member:
                return _result("not_found", "Member not found.")
            status = _membership_status(member)
            payload = dict(member)
            payload["membership_status"] = status
            if status == "expired":
                message = "Membership has expired and needs to be renewed."
            elif status == "active":
                message = "Membership is active."
            else:
                message = "Membership status is unknown."
            return _result(status if status in {"active", "expired"} else "success", message, payload)

        elif intent == "renew":
            member_lookup = _lookup_value(data)
            member = get_member_by_lookup(member_lookup)
            if not member:
                return _result("not_found", "Member not found.")

            current_expiration = _parse_date(member.get("expiration_date", ""))
            new_expiration = _parse_date(data.get("expiration_date", ""))
            if new_expiration is None:
                return _result("validation_error", "Invalid expiration date.")
            if new_expiration < date.today():
                return _result("validation_error", "New expiration date must not be in the past.")
            if current_expiration and new_expiration <= current_expiration:
                return _result("validation_error", "New expiration date must be after the current expiration date.")

            result = update_member(
                member_lookup,
                {
                    "expiration_date": _format_date(new_expiration),
                    "membership_status": "active",
                },
            )
            if result == "success":
                updated = dict(member)
                updated["expiration_date"] = _format_date(new_expiration)
                updated["membership_status"] = "active"
                return _result("success", "Membership renewed successfully.", updated)
            elif result == "not_found":
                return _result("not_found", "Member not found.")
            return _result("error", "Storage error.")

        else:  # unknown intent
            return _result(
                "unknown",
                "I can register, list, search, check status, renew, update, remove, or report on members.",
            )

    except NotImplementedError:
        raise
    except Exception as exc:
        return _result("error", str(exc))
