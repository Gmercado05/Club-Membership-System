# Requirement Specification

## Project Purpose

The Club Membership System helps a student club register members, track whether memberships are active or expired, renew memberships, search member records, and remove members when needed.

## Users

- Primary user: a club officer who manages member records through a CLI or web GUI.
- External services: Gemini for intent extraction and Google Sheets for membership storage.

## Data Model

Each member record contains:

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

Email is treated as the unique identifier for duplicate prevention. The generated `id` or email can be used for lookup/removal.

## Functional Requirements

### Register New Member

- Input: natural-language text containing at least `name` and `email`; optional fields include `major`, `year`, `start_date`, and `expiration_date`.
- Example: `Register Alex Rivera, alex@example.com, Computer Science major, sophomore, start date 2026-06-01.`
- Success: save one member record and return `success` with the created record.
- Failure cases:
  - Missing name or email returns `incomplete`.
  - Invalid email format returns `validation_error`.
  - Duplicate email returns `exists`.
  - Google Sheets or credential failure returns `error`.

### Check Membership Status

- Input: natural-language text containing a member email or ID.
- Example: `Check membership status for alex@example.com.`
- Success:
  - Expiration date today or later returns `active`.
  - Expiration date before today returns `expired`.
- Failure cases:
  - Missing lookup value returns `incomplete`.
  - Missing member returns `not_found`.
  - Invalid or missing expiration date returns an unknown status message.

### Renew Membership

- Input: natural-language text containing a member email or ID and a new expiration date.
- Example: `Renew alex@example.com until 2027-06-01.`
- Success: update the member expiration date and return `success`.
- Failure cases:
  - Missing lookup or date returns `incomplete`.
  - Member not found returns `not_found`.
  - New expiration date in the past returns `validation_error`.
  - New expiration date not later than the current expiration date returns `validation_error`.
  - Google Sheets or credential failure returns `error`.

### Remove Member

- Input: natural-language text containing a member email or ID.
- Example: `Remove alex@example.com.`
- Success: delete the matching member row and return `success`.
- Failure cases:
  - Missing lookup value returns `incomplete`.
  - Missing member returns `not_found`.
  - Google Sheets or credential failure returns `error`.

### Search And List Members

- Input: natural-language list or search request.
- Examples: `Show all members.`, `Show me Computer Science majors.`
- Success: return `success` with matching member records.
- Failure case: storage failure returns an empty result set.

### Reports

- Input: natural-language report request.
- Examples: `Give me a report by membership status.`, `Give me a report by major.`
- Success: return `success` with a count mapping.
- Failure case: storage failure returns an empty report.

### Unknown Or Empty Input

- Input: off-topic text, unsupported requests, or blank terminal input.
- Success:
  - Unknown requests return `unknown` with supported actions.
  - Blank CLI input is ignored without calling the engine.
  - Blank web input returns `incomplete`.

## Nonfunctional Requirements

- Maintain a three-layer architecture with separate interface, engine, and storage responsibilities.
- Return structured dictionaries from the engine so interface layers do not parse free-form text.
- Prevent incomplete write operations before storage is called.
- Keep credentials out of committed source files.
- Include automated tests for core behavior, edge cases, and storage integration.
