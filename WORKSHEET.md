# Final Project Worksheet

Student Name: Gonzalo Mercado

Project Name: Club Membership System

## Project Summary

This project implements a three-layer agentic application for club membership management. A command-line interface and web interface accept natural-language requests, the engine interprets and validates those requests, and the storage layer persists member records in Google Sheets.

## Tool Use Design

The engine uses Gemini to convert flexible user text into structured intent data. This is more maintainable than keyword matching because users can phrase the same action in different ways, such as `register Alice`, `sign Alice up`, `check Alice's membership`, or `renew Alice until next year`.

The model returns:

```python
{"intent": str, "data": dict, "complete": bool, "missing": list}
```

Supported intents are `register`, `list`, `search`, `status`, `renew`, `update`, `delete/remove`, `report`, and `unknown`.

## Reflection And Validation Design

The engine treats the Gemini response as an interpretation, then applies deterministic validation before write operations. This keeps the reflection pattern useful while preventing the model from being the only safety gate.

Examples:

- `register` requires `name` and `email`, then fills membership defaults when dates are not provided.
- `status` requires a member email or ID.
- `renew` requires a member email or ID plus a new expiration date.
- `delete/remove` requires a member email or ID.
- `update` requires a member email or ID plus at least one changed field.

Incomplete write requests return `incomplete` before storage is called.

## Testing Strategy

Engine and interface tests use mocks so they run quickly and do not require API quota or Google Sheets credentials. Storage integration tests use the real Google Sheets API because authentication, row updates, duplicate checking, and deletion are the behavior that storage is responsible for proving.

The full test suite covers:

- Successful registration, listing, searching, status checks, renewal, updating, removal, and reporting
- Duplicate registration
- Incomplete write requests
- Unknown requests
- Storage errors
- CLI response formatting and session behavior
- Google Sheets integration paths

## Engineering Principles

- Separation of concerns: interface, engine, and storage layers are isolated.
- Single responsibility: each module owns a focused part of the workflow.
- Dependency injection: the CLI can receive a mock engine function for tests.
- Stable contracts: engine and storage functions return predictable statuses.
- Credential safety: `.env` and `service_account.json` are ignored by Git.
