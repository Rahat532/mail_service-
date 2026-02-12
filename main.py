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

from smtp_service import SMTPService
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
                failures.append(lead)
            except json.JSONDecodeError:
                continue
    return failures

def load_template_file(path: Path) -> str:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()

def main():
    parser = argparse.ArgumentParser(description="Gmail Bulk Sender (SMTP)")
    parser.add_argument("--leads", default="leads.csv", help="Path to leads file (csv/txt)")
    parser.add_argument("--templates-dir", default="templates", help="Directory containing subject.txt, body.txt, body.html")
    parser.add_argument("--limit", type=int, default=0, help="Max emails to send (0 for all)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate sending without SMTP connection")
    parser.add_argument("--retry", action="store_true", help="Retry failed emails from failed_emails.csv")
    parser.add_argument("--live", action="store_true", help="Actually send emails (override default dry-run mode)")
    parser.add_argument("--sender", help="Use a specific sender email address (must be authorized in tokens/)")

    args = parser.parse_args()
    
    # Mode Logic
    dry_run = args.dry_run or (os.getenv("DEFAULT_MODE", "dry-run") == "dry-run" and not args.live)

    # 1. Start & Check Retry
    leads = []
    if args.retry:
        print("🔄 Loading failed emails for retry...")
        leads = load_failures()
        if not leads:
            print("No failed emails found to retry.")
            return
        FAILED_CSV.rename(FAILED_CSV.with_suffix(f".bak.{int(time.time())}"))
    else:
        recipients_path = Path(args.leads)
        if not recipients_path.exists():
            print(f"❌ Leads file not found: {recipients_path}")
            return
        
        print(f"📂 Loading leads from {recipients_path}...")
        leads = Reader.load_leads(recipients_path)

    if not leads:
        print("⚠️ No leads found.")
        return

    if args.limit > 0:
        leads = leads[:args.limit]

    print(f"✅ Loaded {len(leads)} leads.")

    # 2. Load Templates
    tpl_dir = Path(args.templates_dir)
    if not tpl_dir.exists():
        print(f"❌ Templates directory not found: {tpl_dir}")
        return

    subj_tpl = load_template_file(tpl_dir / "subject.txt")
    body_txt_tpl = load_template_file(tpl_dir / "body.txt")
    body_html_tpl = load_template_file(tpl_dir / "body.html")

    if not subj_tpl:
        print(f"❌ Missing {tpl_dir}/subject.txt")
        return
    if not body_txt_tpl and not body_html_tpl:
        print(f"❌ Must provide at least body.txt or body.html in {tpl_dir}")
        return
    
    print(f"📄 Loaded templates from: {tpl_dir}")



    # 3. Authenticate (Skip if Dry Run)
    senders = []
    
    if not dry_run:
        # Check for multiple tokens
        token_dir = Path("tokens")
        if token_dir.exists() and list(token_dir.glob("*.json")):
            print("🔐 Loading multiple sender accounts from 'tokens/'...")
            try:
                # Load all available tokens
                senders = []
                for t_file in token_dir.glob("*.json"):
                    svc = GmailService(token_file=str(t_file))
                    if svc.service:
                        senders.append(svc)
                        print(f"   ✓ Authenticated: {svc.email_address}")
            except Exception as e:
                print(f"❌ Error loading accounts: {e}")
        
        # Fallback to single token.json if no 'tokens/' dir or empty
        elif os.path.exists("token.json"):
            print("🔐 Loading single account (token.json)...")
            svc = GmailService(token_file="token.json")
            if svc.service:
                senders.append(svc)

        # Fallback to SMTP
        if not senders:
            smtp_email = os.getenv("SMTP_EMAIL")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            if smtp_email and smtp_password:
                print(f"🔐 Initializing SMTP for {smtp_email}...")
                senders.append(SMTPService(smtp_email, smtp_password))
            else:
                print("❌ No valid authentication found (No 'tokens/' directory, no 'token.json', no SMTP credentials).")
                print("   Run 'python account_manager.py --add <email>' to add accounts.")
                return

    # Filter by specific sender if requested
    if args.sender:
        filtered_senders = []
        for s in senders:
            sender_email = getattr(s, 'email_address', None) or getattr(s, 'email', None)
            if sender_email == args.sender:
                filtered_senders.append(s)
        
        if not filtered_senders:
            print(f"❌ Error: Sender '{args.sender}' not found in authorized accounts.")
            print("   Available accounts:")
            for s in senders:
                print(f"   - {getattr(s, 'email_address', None) or getattr(s, 'email', None)}")
            return
        senders = filtered_senders

    print(f"✅ Active Senders: {len(senders)}")
    for s in senders:
        print(f"   - {getattr(s, 'email_address', None) or getattr(s, 'email', None)}")

    # 4. Processing Loop
    print(f"🚀 Starting {'DRY RUN ' if dry_run else ''}process...")
    
    delay = float(os.getenv("RATE_LIMIT_DELAY", 2))
    success_count = 0
    fail_count = 0
    
    pbar = tqdm(leads, unit="email")
    
    for lead in pbar:
        email = lead.get("email")
        pbar.set_description(f"Processing {email}")
        
        footer = "\n\nTo unsubscribe, reply with 'UNSUBSCRIBE'"
        
        try:
            subject = render_template(subj_tpl, lead)
            
            body_html = None
            if body_html_tpl:
                html_footer = "<br><br><small>To unsubscribe, reply with 'UNSUBSCRIBE'</small>"
                body_html = render_template(body_html_tpl, lead) + html_footer
            
            body_text = None
            if body_txt_tpl:
                body_text = render_template(body_txt_tpl, lead) + footer
                
            if dry_run:
                # time.sleep(0.1)
                success_count += 1
                continue

            # Load Balance: Round Robin rotation
            sender_index = success_count % len(senders)
            current_service = senders[sender_index]
            
            # Send via proper service
            if isinstance(current_service, GmailService):
                # Gmail API
                current_service.send_email(to_email=email, subject=subject, body_html=body_html, body_text=body_text)
            else:
                # SMTP Service
                current_service.send_email(to_email=email, subject=subject, body_html=body_html, body_text=body_text)
                
            log_success(email)
            success_count += 1
            
            time.sleep(delay + random.random())

        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to send to {email}: {e}")
            log_failure(lead, e)
    
    print("\n" + "="*30)
    print(f"🎉 Completed.")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    
    if fail_count > 0:
        print(f"⚠️  Failures saved to {FAILED_CSV}. Run with --retry to retry.")

if __name__ == "__main__":
    main()
