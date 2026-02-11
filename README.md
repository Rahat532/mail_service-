# Gmail Bulk Mailer (SMTP Version)

A Python-based bulk email tool using **Gmail SMTP** and **App Passwords**.
Supports **HTML templates**, **Resilient Retry Logic**, and **Rate Limiting**.

---

## 🚀 Features

- **SMTP Integration**: Uses secure SMTP with App Passwords (no OAuth required).
- **HTML & Plain Text**: Support for rich HTML emails with fallback text.
- **Personalization**: Substitute variables like `{name}`, `{company}` from your CSV.
- **Resiliency**: Automatically logs failures and supports resuming/retrying.
- **Rate Limiting**: Configurable delays to respect Gmail limits.

## 🛠️ Setup

### 1. Prerequisites

- Python 3.8+
- A Google Account with **2-Step Verification** enabled.
- An **App Password** generated from [Google Account Security](https://myaccount.google.com/security).

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your details:

```ini
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Your 16-char App Password
RATE_LIMIT_DELAY=2
```

## 🏃 Usage

### Basic Sending

Sends emails from `leads.csv` using `content.txt`:

```bash
python main.py
python main.py --live
```

### Custom Files

Specify different lead or content files:

```bash
python main.py --leads my_list.csv --content my_offer.html
```

### Dry Run

Simulates the process without connecting to SMTP:

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

Must have headers. `email` column is required.

```csv
email,name,company
alice@example.com,Alice,Wonderland Inc
```

### Content (HTML or TXT)

First line must be `Subject: <Your Subject>`.

**example.html**:

```html
Subject: Hello {name}!
<html>
  <body>
    <p>Hi {name},</p>
  </body>
</html>
```

## ⚠️ Troubleshooting

- **SMTP AuthenticationError**: Check your App Password in `.env`. Ensure 2FA is on.
- **Quota Exceeded**: Gmail sends are limited to ~500/day.
