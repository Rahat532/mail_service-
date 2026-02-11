# Bulk Mailer

A Python-based bulk email sending tool with sender rotation, token caching, retry logic, and rate limiting.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [File Formats](#file-formats)
- [Templates](#templates)
- [Usage](#usage)
- [API Integration](#api-integration)
- [Logging](#logging)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Round-Robin Sender Rotation** – Distributes emails across multiple sender accounts
- **Token Caching** – Caches authentication tokens to minimize API calls
- **Automatic Retry** – Configurable retry with exponential backoff
- **Rate Limiting** – Control emails per second to avoid throttling
- **Template Support** – Dynamic subject and body templates with variable substitution
- **Logging** – Separate logs for successful sends and failures

---

## Project Structure

```
bulk_mailer/
├── main.py              # Main application script
├── config.json          # Configuration file (API URLs, settings)
├── senders.txt          # List of sender accounts (email|password)
├── recipients.txt       # List of recipient email addresses
├── templates/
│   ├── subject.txt      # Email subject template
│   └── body.txt         # Email body template
├── logs/                # Generated logs (auto-created)
│   ├── send.log         # Successful sends
│   └── fail.log         # Failed sends
├── venv/                # Python virtual environment
├── .gitignore           # Git ignore rules
└── README.md            # This documentation
```

---

## Requirements

- Python 3.8+
- `requests` – HTTP library for API calls
- `python-dotenv` – Load environment variables from `.env` file (optional)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/bulk_mailer.git
cd bulk_mailer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` – For HTTP API calls
- `python-dotenv` – For loading environment variables

Or create a `requirements.txt` and install:
```bash
pip install -r requirements.txt
```

---

## Configuration

Edit `config.json` with your API settings:

```json
{
  "auth_url": "https://your-auth-server.com/login",
  "send_url": "https://your-email-server.com/send",
  "rate_per_sec": 3,
  "retries": 3,
  "backoff_base": 1.5
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auth_url` | string | required | Authentication API endpoint |
| `send_url` | string | required | Email sending API endpoint |
| `rate_per_sec` | float | 3 | Maximum emails per second |
| `retries` | int | 3 | Number of retry attempts on failure |
| `backoff_base` | float | 1.5 | Exponential backoff multiplier |

### Rate Limiting Examples

| `rate_per_sec` | Delay Between Emails |
|----------------|---------------------|
| 1 | 1000ms |
| 3 | 333ms |
| 10 | 100ms |
| 0 | No delay |

---

## File Formats

### senders.txt

Contains sender account credentials, one per line in format: `email|password`

```
sender1@example.com|password123
sender2@example.com|password456
sender3@example.com|password789
```

**Notes:**
- Lines starting with `#` are comments
- Empty lines are ignored
- Each sender must have a `|` separator

### recipients.txt

Contains recipient email addresses, one per line:

```
alice@example.com
bob@example.com
charlie@example.com
```

**Notes:**
- Lines starting with `#` are comments
- Empty lines are ignored

---

## Templates

Templates support variable substitution using `{variable}` syntax.

### Available Variables

| Variable | Description |
|----------|-------------|
| `{email}` | Recipient's email address |

### templates/subject.txt

```
Important Update for {email}
```

### templates/body.txt

```
Hi,

We're reaching out about our application marketing service.
If you're not interested, reply STOP.

Thanks
```

### Adding Custom Variables

To add more variables, modify the `render()` calls in `main.py`:

```python
subject = render(subject_tpl, {"email": to_email, "name": "John"})
body = render(body_tpl, {"email": to_email, "name": "John"})
```

Then use `{name}` in your templates.

---

## Usage

### Run the Mailer

```bash
python main.py
```

### Expected Output

```
Senders: 3 | Recipients: 100
------------------------------------------------------------
[1] SENT  alice@example.com  (from sender1@example.com)
[2] SENT  bob@example.com  (from sender2@example.com)
[3] FAIL  charlie@example.com -> Connection timeout
...
------------------------------------------------------------
SUCCESS ✅ Sent=97 Failed=3
```

---

## API Integration

The application expects specific API request/response formats. Modify these functions in `main.py` to match your backend.

### Authentication API

**Function:** `api_login()`

**Request:**
```http
POST {auth_url}
Content-Type: application/json

{
  "email": "sender@example.com",
  "password": "password123"
}
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

### Send Email API

**Function:** `api_send()`

**Request:**
```http
POST {send_url}
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "from": "sender@example.com",
  "to": "recipient@example.com",
  "subject": "Hello",
  "text": "Email body content"
}
```

### Adapting to Your API

If your API uses different field names, update the functions:

```python
def api_login(auth_url: str, email: str, password: str) -> Tuple[str, int]:
    r = requests.post(auth_url, json={
        "username": email,      # Change field name
        "pass": password        # Change field name
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["token"], int(data.get("ttl", 3600))  # Change response keys
```

---

## Logging

Logs are stored in the `logs/` directory (auto-created on first run).

### send.log

Records successful sends in JSON format:

```json
{"to": "alice@example.com", "from": "sender1@example.com"}
{"to": "bob@example.com", "from": "sender2@example.com"}
```

### fail.log

Records failed sends with error details:

```json
{"to": "charlie@example.com", "from": "sender1@example.com", "error": "Connection timeout"}
```

---

## Customization

### Change Token Refresh Buffer

Tokens are refreshed 30 seconds before expiry. Modify in `TokenManager.get_token()`:

```python
if info and now < (info.expires_at - 30):  # Change 30 to desired buffer
```

### Add HTML Email Support

Modify `api_send()` payload:

```python
payload = {
    "from": from_email,
    "to": to_email,
    "subject": subject,
    "text": body_text,
    "html": body_html  # Add HTML version
}
```

### Add Attachments

Extend the `api_send()` function based on your API's attachment handling.

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `config.json not found` | Missing config file | Create `config.json` in project root |
| `Bad sender format` | Missing `\|` in senders.txt | Use format: `email\|password` |
| `NameResolutionError` | Invalid API URL | Check `auth_url` and `send_url` in config |
| `401 Unauthorized` | Bad credentials | Verify sender credentials |
| `429 Too Many Requests` | Rate limited | Reduce `rate_per_sec` in config |

### PowerShell Execution Policy Error

If you get an error activating venv:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Check Installed Packages

```bash
pip list
```

### Reinstall Dependencies

```bash
pip install --force-reinstall requests
```

---

## Security Notes

⚠️ **Important:** Never commit sensitive files to version control!

The `.gitignore` file excludes:
- `config.json` – Contains API URLs
- `senders.txt` – Contains sender credentials
- `logs/` – May contain email addresses

For team sharing, create template files:
- `config.example.json`
- `senders.example.txt`

---

## License

MIT License - Feel free to modify and distribute.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
