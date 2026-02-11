import argparse
import os
import time
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

from gmail_service import GmailService
from reader import Reader
from utils import render_template

# Load environment variables
load_dotenv()

# Setup Logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# console.setFormatter(logging.Formatter("%(message)s"))
# logging.getLogger('').addHandler(console) # Don't add to root to avoid tqdm interference

FAILED_CSV = Path("failed_emails.csv")
LOG_FILE = LOG_DIR / "sent.log"

def log_success(email):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[SUCCESS] {email} - {datetime.now()}\n")

def log_failure(lead, error):
    file_exists = FAILED_CSV.exists()
    row = {
        "email": lead.get("email"),
        "attributes": json.dumps(lead),
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    }
    with open(FAILED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "attributes", "error", "timestamp"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def load_failures():
    if not FAILED_CSV.exists():
        return []
    
    failures = []
    with open(FAILED_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lead = json.loads(row["attributes"])
                # Preserve the original attributes
                failures.append(lead)
            except json.JSONDecodeError:
                continue
    return failures

def main():
    parser = argparse.ArgumentParser(description="Gmail Bulk Sender")
    parser.add_argument("--leads", default="leads.csv", help="Path to leads file (csv/txt)")
    parser.add_argument("--content", default="content.txt", help="Path to content file (html/txt)")
    parser.add_argument("--limit", type=int, default=0, help="Max emails to send (0 for all)")
    parser.add_argument("--draft", action="store_true", help="Create drafts instead of sending")
    parser.add_argument("--dry-run", action="store_true", help="Simulate sending without API calls")
    parser.add_argument("--retry", action="store_true", help="Retry failed emails from failed_emails.csv")
    
    args = parser.parse_args()
    
    # 1. Start & Check Retry
    leads = []
    
    if args.retry:
        print("🔄 Loading failed emails for retry...")
        leads = load_failures()
        if not leads:
            print("No failed emails found to retry.")
            return
        # If retrying, we might want to clear the old failure file or append to a new one
        # For simplicity, we'll rename the old one to .bak
        FAILED_CSV.rename(FAILED_CSV.with_suffix(f".bak.{int(time.time())}"))
    else:
        # Normal Load
        recipients_path = Path(args.leads)
        if not recipients_path.exists():
            print(f"❌ Leads file not found: {recipients_path}")
            return
        
        print(f"📂 Loading leads from {recipients_path}...")
        leads = Reader.load_leads(recipients_path)

    if not leads:
        print("⚠️ No leads found.")
        return

    # Apply Limit
    if args.limit > 0:
        leads = leads[:args.limit]

    print(f"✅ Loaded {len(leads)} leads.")

    # 2. Load Content
    content_path = Path(args.content)
    if not content_path.exists():
        print(f"❌ Content file not found: {content_path}")
        return
    
    subj_tpl, body_html_tpl, body_txt_tpl = Reader.load_content(content_path)
    print(f"📄 Loaded content: '{subj_tpl}'")

    # 3. Authenticate
    service = None
    if not args.dry_run:
        print("🔐 Authenticating with Gmail...")
        try:
            gmail = GmailService()
            service = gmail.authenticate()
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return

    # 4. Processing Loop
    print(f"🚀 Starting {'DRY RUN ' if args.dry_run else ''}{'DRAFT ' if args.draft else 'SENDING '} process...")
    
    delay = float(os.getenv("RATE_LIMIT_DELAY", 2))
    
    success_count = 0
    fail_count = 0
    
    pbar = tqdm(leads, unit="email")
    
    for lead in pbar:
        email = lead.get("email")
        pbar.set_description(f"Processing {email}")
        
        # Render
        footer = "\n\nTo unsubscribe, reply with 'UNSUBSCRIBE'"
        
        # Prepare content variables
        # Ensure common keys are available even if not in CSV
        # lead already has the keys from CSV
        
        try:
            subject = render_template(subj_tpl, lead)
            
            body_html = None
            if body_html_tpl:
                # Naive HTML footer append - rigorous way is parsing HTML </body>
                # For now simple string append if plain text, or just appending to HTML string
                # We can wrap the footer in a div
                html_footer = "<br><br><small>To unsubscribe, reply with 'UNSUBSCRIBE'</small>"
                body_html = render_template(body_html_tpl, lead) + html_footer
            
            body_text = None
            if body_txt_tpl:
                body_text = render_template(body_txt_tpl, lead) + footer
            elif body_html: 
                # If only HTML provided, we should probably generate a basic text version or leave it None
                # Gmail API handles strictly HTML fine usually, but nice to have alt text.
                # For this implementation, we rely on what reader returns.
                pass
                
            if args.dry_run:
                # Simulate
                time.sleep(0.1)
                # logging.info(f"[DRY RUN] To: {email} | Subj: {subject}")
                success_count += 1
                continue

            # API Call
            message_body = gmail.create_message(email, subject, body_html, body_text)
            
            if args.draft:
                gmail.create_draft(message_body)
            else:
                gmail.send_message(message_body)
                
            log_success(email)
            success_count += 1
            
            # Rate Limit
            time.sleep(delay + random.random()) # Add jitter

        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to send to {email}: {e}")
            log_failure(lead, e)
            # Optional: Backoff here if it's a rate limit error (429)
            # For simplest MVC, we just log and continue, managing retries later.
    
    print("\n" + "="*30)
    print(f"🎉 Completed.")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📝 Logs: {LOG_DIR}")
    if fail_count > 0:
        print(f"⚠️  Failures saved to {FAILED_CSV}. Run with --retry to retry.")

if __name__ == "__main__":
    main()
