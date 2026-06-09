# Lab 4 Requirement And Design Worksheet

## Part A: Functionality

### Functionality 1: Register New Member

- Input: name, email, major, year, and membership start date.
- Output: registration result and saved member record.
- Success: required fields are present, email is valid, email is unique, and the record is saved.
- Failure/edge cases: missing fields, invalid email, duplicate email, storage save error.

### Functionality 2: Check Membership Status

- Input: member email or member ID.
- Output: active, expired, or not found status.
- Success: member exists and the engine compares expiration date to the current date.
- Failure/edge cases: member not found, invalid lookup, storage read error.

### Functionality 3: Renew Membership

- Input: member email or ID and a new expiration date.
- Output: renewal confirmation and updated membership record.
- Success: member exists, date is valid, and expiration date is extended.
- Failure/edge cases: member not found, date in the past, date not later than current expiration, storage update error.

### Functionality 4: Remove Member

- Input: member email or ID.
- Output: removal result.
- Success: member exists and the record is deleted.
- Failure/edge cases: member not found, storage delete error.

## Part B: Architecture Mapping

### Register New Member Mapping

- `interface` responsibilities: collect the natural-language registration request and display the registration result.
- `engine` responsibilities: extract fields, validate required fields/email format, create membership defaults, and call storage.
- `storage` responsibilities: check duplicate email and save the member record.

### Check Membership Status Mapping

- `interface` responsibilities: collect lookup text and display active/expired/not-found status.
- `engine` responsibilities: validate lookup, retrieve the member, compare expiration date to today's date.
- `storage` responsibilities: retrieve a member by email, member ID, or student ID.

### Renew Membership Mapping

- `interface` responsibilities: collect lookup and new expiration date, then display the renewal result.
- `engine` responsibilities: validate date rules and call storage update.
- `storage` responsibilities: update the member expiration date and status fields.

### Remove Member Mapping

- `interface` responsibilities: collect removal request and display the result.
- `engine` responsibilities: validate lookup and dispatch deletion.
- `storage` responsibilities: delete the matching member record.

## Part C: Interface Contracts

### Interface To Engine

- Function: `process_request(user_input: str) -> dict`
- Input payload: natural-language request string.
- Return payload/status: structured dictionary with `status`, `message`, and optional `data` or `missing`.
- Failure statuses: `incomplete`, `validation_error`, `exists`, `not_found`, `unknown`, `error`.

### Engine To Storage

- Functions: `save_member`, `get_member_by_lookup`, `update_member`, `delete_member`, `get_members`, `search_members`, `get_stats_by_major`, `get_stats_by_status`.
- Input payload: member dictionaries, lookup strings, or update dictionaries.
- Return payload/status: storage status strings, member records, member lists, or report dictionaries.
- Failure statuses: storage functions return `error`, `not_found`, `[]`, `{}`, or `None` according to their contracts.
