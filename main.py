#!/usr/bin/env python3
"""
Gmail Bulk Mailer - Main Entry Point
Sends bulk emails via SMTP using App Passwords.
"""

import argparse
import os
import sys
import time
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from smtp_service import SMTPService
from reader import Reader
from utils import render_template

# Load environment variables
load_dotenv()

# Configuration from environment
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "2"))
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "dry-run")

# File paths
LOGS_DIR = Path("logs")
FAILED_EMAILS_FILE = LOGS_DIR / "failed_emails.csv"


def setup_logging():
    """Ensure logs directory exists."""
    LOGS_DIR.mkdir(exist_ok=True)


def log_failure(email: str, error: str):
    """Log a failed email to CSV."""
    file_exists = FAILED_EMAILS_FILE.exists()
    with open(FAILED_EMAILS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['email', 'error', 'timestamp'])
        writer.writerow([email, error, datetime.now().isoformat()])


def log_success(email: str, log_file: Path):
    """Log a successful email send."""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - SENT - {email}\n")


def send_with_retry(smtp_service: SMTPService, to_email: str, subject: str, 
                    body_html: str, body_text: str, dry_run: bool = False) -> bool:
    """
    Send email with retry logic.
    Returns True if successful, False otherwise.
    """
    if dry_run:
        print(f"  [DRY-RUN] Would send to: {to_email}")
        print(f"            Subject: {subject[:50]}...")
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            smtp_service.send_email(to_email, subject, body_html, body_text)
            return True
        except Exception as e:
            wait_time = BACKOFF_FACTOR ** attempt
            if attempt < MAX_RETRIES:
                print(f"  [RETRY {attempt}/{MAX_RETRIES}] Failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  [FAILED] {to_email}: {e}")
                log_failure(to_email, str(e))
                return False
    return False


def main():
    parser = argparse.ArgumentParser(description="Gmail Bulk Mailer (SMTP)")
    parser.add_argument("--leads", default="leads.csv", 
                        help="Path to leads file (CSV or TXT)")
    parser.add_argument("--content", default="content.txt",
                        help="Path to content file (HTML or TXT)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate sending without actually sending emails")
    parser.add_argument("--retry", action="store_true",
                        help="Retry failed emails from previous run")
    parser.add_argument("--live", action="store_true",
                        help="Actually send emails (override default dry-run mode)")
    args = parser.parse_args()

    # Determine if this is a dry run
    dry_run = args.dry_run or (DEFAULT_MODE == "dry-run" and not args.live)
    
    if dry_run:
        print("=" * 50)
        print("🔍 DRY-RUN MODE - No emails will be sent")
        print("   Use --live to actually send emails")
        print("=" * 50)
    
    # Validate configuration
    if not dry_run:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("ERROR: SMTP_EMAIL and SMTP_PASSWORD must be set in .env file")
            sys.exit(1)

    setup_logging()

    # Determine leads file
    if args.retry:
        if not FAILED_EMAILS_FILE.exists():
            print("No failed emails to retry.")
            sys.exit(0)
        leads_file = FAILED_EMAILS_FILE
        print(f"Retrying failed emails from: {leads_file}")
    else:
        leads_file = Path(args.leads)
    
    # Load leads
    try:
        leads = Reader.load_leads(leads_file)
        print(f"Loaded {len(leads)} leads from {leads_file}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not leads:
        print("No valid leads found. Exiting.")
        sys.exit(0)

    # Load content
    content_file = Path(args.content)
    try:
        subject_template, body_html_template, body_text_template = Reader.load_content(content_file)
        print(f"Loaded content from {content_file}")
        print(f"Subject: {subject_template}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Initialize SMTP service (only if not dry-run)
    smtp_service = None
    if not dry_run:
        smtp_service = SMTPService(SMTP_EMAIL, SMTP_PASSWORD)
        print(f"SMTP configured for: {SMTP_EMAIL}")

    # Create log file for this run
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    success_log = LOGS_DIR / f"sent_{run_timestamp}.log"

    # Send emails
    print(f"\nStarting email campaign...")
    print(f"Rate limit delay: {RATE_LIMIT_DELAY}s between emails")
    print("-" * 50)

    sent_count = 0
    failed_count = 0

    for i, lead in enumerate(leads, 1):
        email = lead.get('email')
        if not email:
            continue

        # Render templates with lead data
        subject = render_template(subject_template, lead)
        body_html = render_template(body_html_template, lead) if body_html_template else None
        body_text = render_template(body_text_template, lead) if body_text_template else None

        print(f"[{i}/{len(leads)}] Sending to: {email}")

        success = send_with_retry(
            smtp_service, email, subject, body_html, body_text, dry_run
        )

        if success:
            sent_count += 1
            if not dry_run:
                log_success(email, success_log)
        else:
            failed_count += 1

        # Rate limiting (skip delay on last email)
        if i < len(leads):
            time.sleep(RATE_LIMIT_DELAY)

    # Summary
    print("-" * 50)
    print(f"Campaign complete!")
    print(f"  Sent: {sent_count}")
    print(f"  Failed: {failed_count}")
    if not dry_run and sent_count > 0:
        print(f"  Success log: {success_log}")
    if failed_count > 0:
        print(f"  Failed emails logged to: {FAILED_EMAILS_FILE}")
        print(f"  Run with --retry to attempt failed emails again")


if __name__ == "__main__":
    main()
