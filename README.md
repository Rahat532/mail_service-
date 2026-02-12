# 📧 Python Bulk Email Sender (Gmail API & Token System)

A powerful, automated bulk email tool designed to send personalized emails safely using the **Gmail API (OAuth 2.0)**. This tool eliminates the need for insecure App Passwords and supports seamless switching between multiple sender accounts.

---

## 📖 How it Works

The app uses **OAuth 2.0 Tokens** to communicate with Google. Instead of storing your password, you authorize the app once via your browser. The app then receives a "Refresh Token" that allows it to send emails on your behalf indefinitely.

To prevent spam flags and bypass daily limits, the system can store multiple tokens and rotate between different sender accounts automatically.

---

## 🚀 Key Features

- **Token System (OAuth 2.0)**: Secure, modern authentication using official Gmail APIs.
- **Single-Token Logic**: Configured to keep only the latest authorized account active for streamlined automation.
- **Smart Rotation**: Automatically rotates through authorized accounts in the `tokens/` folder to distribute sending load.
- **Dynamic Personalization**: Use variables like `{name}` or `{company}` in your templates, pulled directly from your CSV.
- **HTML & Plain Text Support**: Send rich HTML emails with automatic plain-text fallbacks.
- **Resilient Retry Mechanism**: Automatically catches failures and saves them to `failed_emails.csv` for easy retrying.

---

## 🛠️ Setup Process

### 1. Prerequisites

- Python 3.8+ installed.
- A Google Cloud Project with the **Gmail API** enabled.

### 2. Installation

```bash
# Clone the repository and enter the directory
pip install -r requirements.txt
```

### 3. Google Cloud Setup (The "One-Time" Step)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create **OAuth 2.0 Client ID** (Desktop Application).
3. **Option A (Recommended):** Download the JSON file, rename it to `credentials.json`, and place it in the project root.
4. **Option B:** Copy the **Client ID** and **Client Secret** and paste them into your `.env` file when prompted by the script.

---

## 🏃 Usage & Commands

### 🔐 Multi-Account Management

Use the `account_manager.py` script to authorize your sender accounts.

> **Note:** Whenever you add a new account, the script will automatically delete previous tokens to ensure only the latest one is active (per your configuration).

```bash
# Authorize a new Gmail account (opens browser)
python account_manager.py --add your-email@gmail.com

# List currently authorized accounts
python account_manager.py --list
```

### ✉️ Sending Emails

The `main.py` script handles the actual email delivery.

```bash
# Dry Run (Simulation - No emails sent)
python main.py

# Live Run (Actually send emails)
python main.py --live

# Send using a SPECIFIC authorized account
python main.py --live --sender your-email@gmail.com

# Retry previously failed emails
python main.py --retry --live
```

---

## 📂 File Formats & Templates

### Leads (`leads.csv`)

Requires an `email` column. Any other columns can be used as placeholders in templates.

```csv
email,name,company
client@example.com,John,Acme Corp
```

### Templates (`templates/` folder)

The app reads from the `templates/` directory by default:

- `subject.txt`: Subject line of the email.
- `body.html`: Rich HTML content.
- `body.txt`: Plain text fallback.

Use `{column_name}` to insert data from your CSV (e.g., `Hi {name},`).

---

## ⚠️ Troubleshooting

- **Access Blocked (403 Data Error):** Your app is in "Testing" mode. You **must** add your email address to the "Test Users" list in Google Cloud Console > OAuth Consent Screen.
- **API Not Enabled:** Ensure the "Gmail API" is enabled in the Google Library for your project.
- **Scopes Error:** If the app asks for new permissions, the script will force a re-login to update your token.

---

## 🛡️ Security Note

Your `tokens/` directory contains sensitive access keys. **Never** commit your `tokens/` folder or `credentials.json` to public version control (like GitHub). They are included in the `.gitignore` by default.
