# Club Membership System

The Club Membership System is a command-line and web application for managing student club memberships through natural-language requests. It uses Gemini to extract intent and fields, local validation rules to protect write operations, and Google Sheets as the persistence layer.

## Rubric Paths

- Source code: `src/`
- Tests: `tests/`
- Requirement specification: `FUNCTIONALITY.md`
- Design and interface contract: `CONTRACT.md`
- Lab 4 worksheet-style design support: `LAB4_DESIGN.md`
- Setup and execution guide: `SETUP_GUIDE.md`
- Demo video: https://youtu.be/syREus83ufg?si=QwuxOx4CePY86Ptx

## Features

- Run from either a command-line interface or browser interface
- Register a member with `name`, `email`, `major`, `year`, and membership dates
- List all members
- Search members by supported fields
- Update member details
- Check whether a membership is active or expired
- Renew memberships by setting a new expiration date
- Remove members by email or member ID
- Generate membership reports
- Handle duplicate, incomplete, unknown, and storage-error paths with structured statuses

## Architecture

```text
interface -> engine -> storage -> Google Sheets
```

- `interface`: collects CLI input and formats responses
- `engine`: extracts intent, validates request completeness, and dispatches work
- `storage`: reads and writes Google Sheets records

## Setup

Install dependencies from this directory:

```bash
python3 -m pip install -r requirements.txt
```

Create local configuration:

```bash
cp .env.example .env
```

Fill in `.env` with a Gemini API key:

```bash
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash
SPREADSHEET_NAME=club-membership-system-members
```

Google Sheets setup:

1. Create a Google Sheet named `club-membership-system-members`.
2. Add row 1 headers: `id`, `name`, `email`, `major`, `year`, `start_date`, `expiration_date`, `membership_status`.
3. Place `service_account.json` in this project directory.
4. Share the sheet with the service account email as an editor.

## Run

Command-line interface:

```bash
python3 -m src.interface.cli
```

Web interface:

```bash
python3 -m flask --app src.interface.web run --debug --port 5050
```

Then open:

```text
http://127.0.0.1:5050
```

Example requests:

```text
Register Alice Chen, alice@example.com, Computer Science major, sophomore, start date 2026-06-01.
Show me all registered members.
Check membership status for alice@example.com.
Renew alice@example.com until 2027-06-01.
Remove alice@example.com.
```

## Test

Run the full suite:

```bash
python3 -m pytest tests/ -v
```

Run with coverage:

```bash
python3 -m pytest --cov=src --cov-report=term-missing tests/ -v
```

The test suite includes unit tests with mocked Gemini/storage calls and integration tests for the Google Sheets storage layer.
