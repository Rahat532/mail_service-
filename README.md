# 📧 Python Bulk Email Sender (Gmail API & Token System)

A powerful, automated bulk email tool with a **modern web interface** designed to send personalized emails safely using the **Gmail API (OAuth 2.0)**. This tool eliminates the need for insecure App Passwords and supports seamless switching between multiple sender accounts.

---

## 📖 How it Works

The app uses **OAuth 2.0 Tokens** to communicate with Google. Instead of storing your password, you authorize the app once via your browser. The app then receives a "Refresh Token" that allows it to send emails on your behalf indefinitely.

To prevent spam flags and bypass daily limits, the system can store multiple tokens and rotate between different sender accounts automatically.

---

## 🚀 Key Features

### 🎨 Modern Web Interface

- **Premium Glassmorphic UI**: Beautiful, modern design with dark mode aesthetics
- **Real-time Monitoring**: Live progress bar, success/fail counters, and timing statistics
- **Dual Modes**: Choose between Static (file-based) or Dynamic (text-based) email composition
- **Smart Management**: Built-in failure tracking, email retry, and log management

### 🔐 Security & Authentication

- **OAuth 2.0 Token System**: Secure authentication using official Gmail APIs
- **Single-Token Logic**: Keeps only the latest authorized account active for streamlined automation
- **Smart Rotation**: Automatically rotates through authorized accounts to distribute sending load

### ✉️ Email Features

- **Dynamic Personalization**: Use variables like `{name}` or `{company}` in templates, pulled from CSV
- **HTML & Plain Text**: Send rich HTML emails with automatic plain-text fallbacks
- **Timing Analytics**: Track total time and average time per email sent
- **Resilient Retry**: Automatically saves failures to CSV for easy retrying

---

## 🛠️ Setup Process

### 1. Prerequisites

- Python 3.8+ installed
- A Google Cloud Project with the **Gmail API** enabled

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Google Cloud Setup (One-Time)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create **OAuth 2.0 Client ID** (Desktop Application)
3. **Download** the JSON file, rename it to `credentials.json`, and place it in the project root
4. Enable the **Gmail API** in your Google Cloud project
5. Add test users in **OAuth Consent Screen** if your app is in "Testing" mode

---

## 🖥️ Web Interface (Recommended)

### Launch the UI

```bash
# Activate virtual environment and start server
source .venv/Scripts/activate && python gui_server.py
```

Then open your browser to: **http://localhost:8000**

### UI Features

- **Email Mode Toggle**: Switch between Static (file-based) and Dynamic (text-based) modes
- **Live Statistics**: Real-time success/fail counts, progress bar, and timing metrics
- **Log Management**: View, filter, and clear logs with one click
- **Failure Recovery**: See failed emails, copy them to clipboard, or retry automatically
- **Reset App**: Clear all stats and start fresh without restarting the server

### Static Mode (File-based)

Perfect for reusable campaigns:

- Point to your `leads.csv` file
- Point to `templates/subject.txt` and `templates/body.txt`
- Use `{variable}` syntax in files

### Dynamic Mode (Text-based)

Perfect for quick campaigns:

- Type your subject directly in the UI
- Write your email body in the textarea
- Still uses `{variable}` syntax for personalization
- Auto-detects HTML vs plain text

---

## 💻 Command Line Interface (CLI)

### Account Management

```bash
# Add a new Gmail account (opens browser for OAuth)
python account_manager.py --add your-email@gmail.com

# List all authorized accounts
python account_manager.py --list
```

> **Note:** Adding a new account automatically removes previous tokens (single-token mode).

### Sending Emails via CLI

```bash
# Send emails (live mode)
python main.py --live

# Send using a specific authorized account
python main.py --live --sender your-email@gmail.com

# Retry previously failed emails
python main.py --retry --live
```

---

## 📂 File Formats & Templates

### Leads File (`leads.csv`)

Requires an `email` column. Additional columns become variables:

```csv
email,name,company
john@example.com,John Smith,Acme Corp
jane@example.com,Jane Doe,Tech Inc
```

### Static Templates (Optional)

When using **Static Mode**, create files in the `templates/` folder:

**templates/subject.txt**:

```
Hello {name}!
```

**templates/body.txt** or **templates/body.html**:

```
Hi {name},

I noticed you work at {company}...
```

Use `{column_name}` to insert data from your CSV.

---

## ⏱️ Performance Metrics

The UI displays:

- **Total Time**: Complete process duration
- **Average Time Per Email**: Helps optimize rate limits
- **Individual Email Timing**: Each log entry shows how long it took

---

## ⚠️ Troubleshooting

### Common Issues

**Access Blocked (403 Error)**

- Your app is in "Testing" mode
- Solution: Add your email to "Test Users" in Google Cloud Console > OAuth Consent Screen

**API Not Enabled**

- Solution: Enable "Gmail API" in Google Cloud Console > APIs & Services

**Module Not Found (FastAPI)**

- Solution: Activate virtual environment first: `source .venv/Scripts/activate`

**Server Shows 0.0.0.0:8000**

- This is normal! Open `http://localhost:8000` in your browser

---

## 🧹 Managing Logs & Failures

### Via Web UI

- **Clear Logs**: Reset live logs display
- **Copy Emails**: Copy all failed email addresses to clipboard
- **Clear Failures**: Delete the `failed_emails.csv` file
- **Reset App**: Clear all stats and start fresh

### Via Files

- Live logs: `logs/app.log`
- Sent emails: `logs/sent.log`
- Failed emails: `failed_emails.csv`

---

## 🛡️ Security Best Practices

1. **Never commit secrets**: The `.gitignore` already excludes `tokens/`, `credentials.json`, and `.env`
2. **Token isolation**: Each email account has its own token file
3. **Testing mode**: Start with Google's "Testing" mode and add specific test users
4. **Rate limiting**: The system includes delays to respect Gmail's sending limits

---

## 📊 Account Limits

- **Testing Mode**: Up to 100 test users
- **Gmail Sending Limits**: ~500 emails per day per account (use rotation for more)
- **Token Refresh**: Automatic - tokens never expire as long as they're used regularly

---

## 🎯 Quick Start Guide

1. **Setup Google Cloud** (one-time, 5 minutes)
2. **Add your first account**: `python account_manager.py --add your-email@gmail.com`
3. **Launch the UI**: `source .venv/Scripts/activate && python gui_server.py`
4. **Open browser**: `http://localhost:8000`
5. **Choose Dynamic Mode** for quick testing
6. **Enter your CSV path** and write a test email
7. **Click "Send Emails"** and watch the magic happen! ✨
