import os
import asyncio
import json
import csv
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from smtp_service import SMTPService
from gmail_service import GmailService
from reader import Reader
from utils import render_template

load_dotenv()

app = FastAPI(title="Mail Service UI")

# State management (simplified for local use)
class AppState:
    is_running = False
    stop_requested = False
    progress = 0
    total = 0
    success_count = 0
    fail_count = 0
    current_logs = []
    
state = AppState()

# Ensure directories exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
FAILED_CSV = Path("failed_emails.csv")

class MailRequest(BaseModel):
    leads_path: str
    subject_path: Optional[str] = None
    body_path: Optional[str] = None
    is_retry: bool = False
    is_dry_run: bool = False
    is_dynamic: bool = False
    subject_content: Optional[str] = None
    body_content: Optional[str] = None

def load_template_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()

def get_failures():
    if not FAILED_CSV.exists():
        return []
    failures = []
    try:
        with open(FAILED_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                failures.append(row)
    except Exception as e:
        print(f"Error reading failures: {e}")
    return failures

async def run_mailer(req: MailRequest):
    state.is_running = True
    state.stop_requested = False
    state.progress = 0
    state.success_count = 0
    state.fail_count = 0
    state.current_logs = []

    try:
        # Load leads
        if req.is_retry:
            raw_failures = get_failures()
            leads = []
            for row in raw_failures:
                try:
                    leads.append(json.loads(row["attributes"]))
                except:
                    continue
            if FAILED_CSV.exists():
                FAILED_CSV.rename(FAILED_CSV.with_suffix(f".bak.{int(datetime.now().timestamp())}"))
        else:
            leads = Reader.load_leads(Path(req.leads_path))

        if not leads:
            state.current_logs.append("No leads found.")
            state.is_running = False
            return

        state.total = len(leads)
        
        # Load templates
        if req.is_dynamic:
            # Dynamic mode: use content from request
            subj_tpl = req.subject_content
            body_content = req.body_content
            
            # Check if body looks like HTML
            if body_content and ('<' in body_content and '>' in body_content):
                body_html_tpl = body_content
                body_txt_tpl = None
            else:
                body_txt_tpl = body_content
                body_html_tpl = None
        else:
            # Static mode: load from files
            subj_tpl = load_template_file(req.subject_path)
            body_html_tpl = None
            body_txt_tpl = None
            
            body_content = load_template_file(req.body_path)
            if req.body_path.endswith(".html"):
                body_html_tpl = body_content
            else:
                body_txt_tpl = body_content

        if not subj_tpl:
            state.current_logs.append(f"Subject file not found: {req.subject_path}")
            state.is_running = False
            return

        # Authenticate
        senders = []
        token_dir = Path("tokens")
        if token_dir.exists() and list(token_dir.glob("*.json")):
            for t_file in token_dir.glob("*.json"):
                svc = GmailService(token_file=str(t_file))
                if svc.service:
                    senders.append(svc)
        
        if not senders and os.getenv("SMTP_EMAIL") and os.getenv("SMTP_PASSWORD"):
            senders.append(SMTPService(os.getenv("SMTP_EMAIL"), os.getenv("SMTP_PASSWORD")))

        if not senders:
            state.current_logs.append("No authorized accounts found.")
            state.is_running = False
            return

        delay = float(os.getenv("RATE_LIMIT_DELAY", 2))

        for i, lead in enumerate(leads):
            if state.stop_requested:
                state.current_logs.append("Process cancelled by user.")
                break

            email = lead.get("email")
            state.current_logs.append(f"Sending to {email}...")
            
            try:
                subject = render_template(subj_tpl, lead)
                body_html = render_template(body_html_tpl, lead) if body_html_tpl else None
                body_text = render_template(body_txt_tpl, lead) if body_txt_tpl else None
                
                # Round Robin
                if req.is_dry_run:
                    state.current_logs.append(f"[DRY RUN] Would send to {email}")
                    state.success_count += 1
                    await asyncio.sleep(0.1) # Fast simulation
                    continue

                service = senders[state.success_count % len(senders)]
                service.send_email(to_email=email, subject=subject, body_html=body_html, body_text=body_text)
                
                state.success_count += 1
                state.current_logs.append(f"Successfully sent to {email}")
                
                # Mock sleep for UI visibility (actually should be the delay)
                await asyncio.sleep(delay + random.uniform(0.1, 0.5))

            except Exception as e:
                state.fail_count += 1
                state.current_logs.append(f"Failed to send to {email}: {str(e)}")
                # Log failure to CSV (using existing logic or re-impl)
                from main import log_failure
                log_failure(lead, e)

            state.progress = int(((i + 1) / state.total) * 100)

    except Exception as e:
        state.current_logs.append(f"Fatal Error: {str(e)}")
    
    state.is_running = False
    state.current_logs.append("Process completed.")

@app.get("/status")
async def get_status():
    return {
        "is_running": state.is_running,
        "progress": state.progress,
        "success": state.success_count,
        "fail": state.fail_count,
        "total": state.total,
        "logs": state.current_logs[-50:] # Only late logs
    }

@app.post("/send")
async def start_mailing(req: MailRequest, background_tasks: BackgroundTasks):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Process already running")
    background_tasks.add_task(run_mailer, req)
    return {"message": "Process started"}

@app.post("/cancel")
async def stop_mailing():
    state.stop_requested = True
    return {"message": "Cancellation requested"}

@app.get("/failures")
async def fetch_failures():
    return get_failures()

@app.post("/clear-logs")
async def clear_logs():
    state.current_logs = []
    return {"message": "Logs cleared"}

@app.post("/clear-failures")
async def clear_failures():
    if FAILED_CSV.exists():
        try:
            FAILED_CSV.unlink()
            return {"message": "Failures cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clear: {str(e)}")
    return {"message": "No failures to clear"}

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
