# Project: Python Bulk Email Sender (Gmail API)

---

# 📝 Prompt / Requirements Specifications

## Objective

Build a Python-based bulk email automation tool that sends personalized emails to a list of leads using the **Gmail API** (OAuth2). The system must be robust, supporting retries, detailed logging, and failure management.

## System Architecture

### 1. Input Sources

- **Leads**: Support both `leads.txt` (one email per line) and `leads.csv` (must contain an `email` column). Validate emails using Regex and skip invalid entries.
- **Content**: Read subject and body from `content.txt`. The file format should be parsed to extract the "Subject:" line and the subsequent "Body:" content.

### 2. Email Sending Service (Gmail API)

- **Authentication**: Use `OAuth 2.0` with `credentials.json`.
- **Token Management**: Store and reuse access tokens (`token.json` or `token.pickle`) to avoid re-authentication on every run.
- **Sending**: Construct MIME messages (text/html) and send via the Gmail API `users().messages().send()` endpoint.
- **Wait Mechanism**: Implement a configurable delay (e.g., 2-5 seconds) between emails to respect API rate limits.

### 3. Failure Handling & Retry Logic

- **Failure Storage**: If an email fails to send, log the details (Email, Subject, Error Message, Timestamp) into a `failed_emails.csv` (or `.json`) file.
- **Retry Mode**: On startup, check if a failure file exists.
  - Prompt the user: _"Retry failed emails? (y/n)"_
  - If **Yes**: Load failed emails and attempt to resend.
  - If successful: Remove from the failure list.
  - If failed again: Update the failure record (optionally track retry counts).

### 4. Logging

- Maintain a `logs.txt` file.
- Log formats:
  - `[SUCCESS] <email> - <timestamp>`
  - `[FAILED] <email> - <error>`
  - `[RETRY SUCCESS] <email>`

### 5. Advanced Features (Optional but Recommended)

- **Exponential Backoff**: If a send fails, wait 2s -> 4s -> 8s before giving up or ensuring the next retry respects limits.
- **CLI Arguments**: Allow running via command line, e.g., `python main.py --retry`.
- **Modular Code**: Separate concerns into `mailer.py`, `reader.py`, `logger.py`, and `main.py`.

---

# 🗺️ Implementation Roadmap

## Phase 1: Setup & Configuration

- [ ] **Environment Setup**:
  - Install Python dependencies: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `pandas` (optional, for CSV).
- [ ] **Google Cloud Project**:
  - Create project in Google Cloud Console.
  - Enable **Gmail API**.
  - Create OAuth 2.0 Desktop Client credentials.
  - Download `credentials.json` and place it in the project root.

## Phase 2: Core Modules Development

- [ ] **Module: `gmail_service.py`**:
  - Implement `get_gmail_service()` to handle OAuth flow (load/save tokens).
  - Implement `create_message()` for MIME construction.
  - Implement `send_email()` to interact with the API.
- [ ] **Module: `reader.py`**:
  - Implement `load_leads(filepath)`: Detect CSV vs TXT, validate emails.
  - Implement `load_content(filepath)`: Parse Subject and Body.

## Phase 3: Main Logic & State Management

- [ ] **Module: `logger.py`**:
  - Set up simple file logging to `logs.txt`.
- [ ] **Module: `main.py` (Base Flow)**:
  - Orchestrate loading leads and content.
  - Initialize Gmail Service.
  - Loop through leads and send emails with `time.sleep()`.
- [ ] **Failure Handling**:
  - Wrap sending logic in `try/except`.
  - On exception: Append record to `failed_emails.csv`.

## Phase 4: Retry Mechanism & Refinement

- [ ] **Retry Logic**:
  - Add startup check for `failed_emails.csv`.
  - Implement logic to read failures and re-queue them if user approves.
- [ ] **CLI & Polish**:
  - Add `argparse` for flags like `--retry` or `--dry-run`.
  - Final code cleanup and comments.

## Phase 5: Testing

- [ ] **Dry Run**: Test with a small list of your own emails.
- [ ] **Failure Test**: Intentionally disconnect internet or invalidate token to verify `failed_emails.csv` creation.
- [ ] **Retry Test**: Run script again to verify retry prompt and successful clearing of the failure list.
