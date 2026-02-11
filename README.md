# Gmail Bulk Mailer

A Python-based bulk email tool using the **Gmail API** (OAuth 2.0).  
Supports **HTML templates**, **Draft Mode**, **Resilient Retry Logic**, and **Rate Limiting**.

---

## 🚀 Features

- **Gmail API Integration**: Uses OAuth 2.0 for secure, token-based authentication.
- **Draft Mode**: Create drafts for review instead of sending immediately.
- **HTML & Plain Text**: Support for rich HTML emails with fallback text.
- **Personalization**: Substitute variables like `{name}`, `{company}` from your CSV.
- **Resiliency**: Automatically logs failures and supports resuming/retrying.
- **Rate Limiting**: Configurable delays to respect Gmail API limits.

## 🛠️ Setup

### 1. Prerequisites
- Python 3.8+
- A Google Cloud Project with **Gmail API** enabled.
- `credentials.json` (OAuth 2.0 Client ID) placed in the project root.

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` (optional, defaults provided):

```ini
RATE_LIMIT_DELAY=2  # Seconds between emails
```

## 🏃 Usage

### Basic Sending
Sends emails from `leads.csv` using `content.txt`:

```bash
python main.py
```

### Draft Mode (Safe Testing)
Creates drafts in your Gmail Drafts folder instead of sending:

```bash
python main.py --draft
```

### Custom Files
Specify different lead or content files:

```bash
python main.py --leads my_list.csv --content my_offer.html
```

### Dry Run
Simulates the process without hitting the Gmail API:

```bash
python main.py --dry-run
```

### Retrying Failures
If a run has failures, they are logged to `failed_emails.csv`. To retry them:

```bash
python main.py --retry
```

## 📂 File Formats

### Leads (CSV)
Must have headers. `email` column is required. Other columns are available as variables.

```csv
email,name,company
alice@example.com,Alice,Wonderland Inc
```

### Content (HTML or TXT)
First line must be `Subject: <Your Subject>`. The rest is the body.

**example.html**:
```html
Subject: Hello {name}!
<html>
<body>
  <p>Hi {name},</p>
  <p>Check out our offer for {company}!</p>
</body>
</html>
```

## 🛡️ Rate Limits & Quotas
- **Free Gmail**: ~500 emails/day.
- **Google Workspace**: ~2,000 emails/day.
- The tool adds a delay (default 2s) to avoid 429 Too Many Requests errors.

## ⚠️ Troubleshooting
- **Authentication Failed**: Delete `token.json` and run again to re-login.
- **Quota Exceeded**: Wait 24 hours.
