# Setup And Execution Guide

## Requirements

- Python 3.10 or newer recommended
- Google Sheet for membership records storage
- Google service account JSON file
- Gemini API key

## Install Dependencies

From the project directory:

```bash
python3 -m pip install -r requirements.txt
```

## Configure Environment

Create a local `.env` file:

```bash
cp .env.example .env
```

Set these values:

```bash
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash
SPREADSHEET_NAME=club-membership-system-members
```

`GEMINI_API_KEY` may be used instead of `GOOGLE_API_KEY`.

## Configure Google Sheets

1. Create a Google Sheet named `club-membership-system-members`.
2. Add this header row exactly:

```text
id,name,email,major,year,start_date,expiration_date,membership_status
```

3. Place `service_account.json` in the project directory.
4. Share the sheet with the service account email listed in `service_account.json`.
5. Give the service account editor access.

`service_account.json` and `.env` are ignored by Git because they contain local credentials.

## Run The Application

Command-line version:

```bash
python3 -m src.interface.cli
```

Web version:

```bash
python3 -m flask --app src.interface.web run --debug --port 5050
```

Open `http://127.0.0.1:5050` in a browser.

In the command-line version, exit with `quit`, `exit`, or `Ctrl-D`.

## Example Session

```text
You: Register Alice Chen, alice@example.com, Computer Science major, sophomore, start date 2026-06-01.
Assistant: Member registered.

You: Check membership status for alice@example.com.
Assistant: Membership is active.

You: Renew alice@example.com until 2027-06-01.
Assistant: Membership renewed successfully.

You: Show me Computer Science majors.
Assistant: 1 member(s) found.
  - Alice Chen (alice@example.com)

You: Give me a report by membership status.
Assistant: Report generated.
  - active: 1
```

## Run Tests

Fast unit tests and mocked storage tests:

```bash
python3 -m pytest tests/engine tests/interface tests/storage/test_storage_unit_paths.py -v
```

Full suite, including live Google Sheets integration tests:

```bash
python3 -m pytest tests/ -v
```

Coverage report:

```bash
python3 -m pytest --cov=src --cov-report=term-missing tests/ -v
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
| `error` from engine calls | Missing or invalid API key | Check `.env` and the Gemini key |
| Empty member list when sheet has data | Sheet not shared with service account | Share the sheet with editor access |
| Storage integration tests fail | Sheet name or headers differ | Verify `SPREADSHEET_NAME` and row 1 headers |
| Import errors | Dependencies missing | Re-run `python3 -m pip install -r requirements.txt` |
