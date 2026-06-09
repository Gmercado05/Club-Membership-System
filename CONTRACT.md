# Design And Interface Contract

## Layered Architecture

```text
src/interface/cli.py or src/interface/web.py
    -> src/engine/engine.py
        -> src/storage/storage_handler.py
        -> src/storage/storage_handler_extended.py
            -> src/storage/sheet_client.py
                -> Google Sheets
```

## Component Responsibilities

### Interface Layer

- Owns terminal input and output.
- Owns browser input and output for the web UI.
- Calls the engine through `process_request(user_input)`.
- Formats structured engine results for display.
- Does not call Gemini or Google Sheets directly.

### Engine Layer

- Owns application orchestration.
- Uses Gemini to interpret natural-language intent and fields.
- Applies deterministic completeness checks before mutating storage.
- Dispatches valid requests to storage functions.
- Returns a structured result for every handled path.

### Storage Layer

- Owns Google Sheets authentication and data access.
- Validates required member fields before writes.
- Enforces duplicate-email prevention.
- Converts storage exceptions into contract status values.

## Shared Data Shapes

`member_record`:

```python
{
    "id": str,
    "name": str,
    "email": str,
    "major": str,
    "year": str,
    "start_date": str,
    "expiration_date": str,
    "membership_status": str,
}
```

`engine_result` always contains:

```python
{"status": str, "message": str}
```

Optional keys:

- `data`: list, dict, or `None`
- `missing`: list of required fields for incomplete requests

## Interface To Engine Contract

`process_request(user_input: str) -> dict`

Return statuses:

| Status | Meaning |
| --- | --- |
| `success` | Operation completed |
| `exists` | Registration email already exists |
| `incomplete` | Required fields are missing |
| `validation_error` | Email or date validation failed |
| `active` | Membership exists and has not expired |
| `expired` | Membership exists and has expired |
| `not_found` | Requested member row was not found |
| `unknown` | Request is unsupported or off-topic |
| `error` | AI, parsing, credential, or storage failure |

`format_response(result: dict) -> str`

- Converts engine results into terminal text.
- Displays list and report payloads.
- Displays missing fields for incomplete requests.

`run_session(process_fn: callable | None = None) -> None`

- Runs the CLI loop until `quit`, `exit`, or EOF.
- Accepts an injected engine function for testing.

`create_app(process_fn: callable | None = None) -> Flask`

- Creates the web application.
- Serves the HTML interface at `/`.
- Accepts JSON requests at `/api/request`.
- Uses an injected engine function for tests.

## Engine To Storage Contract

`save_member(member_data: dict) -> str`

- `success`: row appended.
- `exists`: duplicate email found.
- `error`: missing required data or storage failure.

`get_members() -> list[dict]`

- Returns all records.
- Returns `[]` for empty sheet or storage failure.

`search_members(filters: dict) -> list[dict]`

- Returns records matching all non-empty supported filters.
- Empty filters return all records.
- Storage failure returns `[]`.

`get_member_by_lookup(member_lookup: str) -> dict | None`

- Returns one member matched by email, member ID, or student ID.
- Returns `None` when no member matches or storage fails.

`update_member(member_lookup: str, updates: dict) -> str`

- `success`: row updated.
- `not_found`: no matching member email or ID.
- `error`: invalid update payload or storage failure.

`delete_member(member_lookup: str) -> str`

- `success`: row deleted.
- `not_found`: no matching member email or ID.
- `error`: storage failure.

`get_stats_by_major() -> dict`

- Returns `major -> count`.
- Blank majors are grouped under `"(Unknown)"`.
- Storage failure returns `{}`.

`get_stats_by_status() -> dict`

- Returns `membership_status -> count`.
- Blank statuses are grouped under `"(Unknown)"`.
- Storage failure returns `{}`.

## Design Principles

- Single Responsibility: each layer owns one concern.
- Open/Closed: new intents can be added by extending prompt rules and dispatch branches without changing interface/storage contracts.
- Liskov Substitution: engine tests replace storage functions with mocks that obey the same contracts.
- Interface Segregation: the CLI depends only on `process_request`, not individual storage functions.
- Dependency Inversion: higher layers depend on function contracts, while concrete Google Sheets access is isolated in the storage layer.
