import os
from pathlib import Path
from gmail_service import GmailService, SCOPES
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN_DIR = Path("tokens")
CREDENTIALS_FILE = "credentials.json"


def add_account(alias):
    """Adds a new Gmail token for a specific alias/account."""
    
    flow_config = None
    
    # Check env vars first
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if client_id and client_secret:
        flow_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "project_id": "generic-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }

    elif not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: '{CREDENTIALS_FILE}' not found.")
        print("You verify the app using 'credentials.json' OR 'GOOGLE_CLIENT_ID' in .env")
        
        print("\n💡 Easy Setup: Checking for Client ID/Secret...")
        c_id = input("   Paste your GOOGLE_CLIENT_ID (or press Enter to skip): ").strip()
        if c_id:
            c_secret = input("   Paste your GOOGLE_CLIENT_SECRET: ").strip()
            if c_secret:
                # Update .env file
                try:
                    with open(".env", "a") as f:
                        f.write(f"\nGOOGLE_CLIENT_ID={c_id}\n")
                        f.write(f"GOOGLE_CLIENT_SECRET={c_secret}\n")
                    print("✅ Saved to .env! Retrying...")
                    
                    # Reload env vars
                    client_id = c_id
                    client_secret = c_secret
                     # Re-create config
                    flow_config = {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "project_id": "generic-project",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                except Exception as e:
                    print(f"❌ Failed to write to .env: {e}")
                    return

        if not flow_config:
             print("❌ Setup aborted. Please configure credentials.")
             return



    TOKEN_DIR.mkdir(exist_ok=True)
    # 🧹 DELETE ALL PREVIOUS TOKENS (Keep only latest)
    print("🧹 Cleaning up old tokens...")
    for old_token in TOKEN_DIR.glob("*.json"):
        try:
            os.remove(old_token)
            print(f"   - Removed {old_token.name}")
        except Exception as e:
            print(f"   ⚠️ Could not remove {old_token.name}: {e}")

    token_path = TOKEN_DIR / f"{alias}.json"
    
    # We want to force re-auth to select the account
    if flow_config:
        flow = InstalledAppFlow.from_client_config(flow_config, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    
    # Run server
    creds = flow.run_local_server(port=0)
    
    # Save the credentials
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print(f"✅ Authenticated and saved token for: {alias}")
    
    # Verify by getting profile
    try:
        service = GmailService(token_file=str(token_path))
        print(f"   Confirmed Account: {service.email_address}")
        if service.email_address != alias:
            print(f"⚠️  Warning: Token email ({service.email_address}) does not match alias ({alias}).")
            # Rename file to match actual email?
            new_path = TOKEN_DIR / f"{service.email_address}.json"
            if str(new_path) != str(token_path):
                 os.rename(token_path, new_path)
                 print(f"   Renamed token file to {new_path}")

    except Exception as e:
        print(f"❌ Verification failed: {e}")

def list_accounts():
    """Lists all available token files."""
    if not TOKEN_DIR.exists():
        print("No accounts added yet.")
        return []
    
    accounts = []
    print("\n📧 Configured Accounts:")
    for token_file in TOKEN_DIR.glob("*.json"):
        # We assume the filename is the email, but really we should check inside or just trust filename
        email = token_file.stem
        # Optional: Load to verify validity? expensive.
        print(f" - {email}")
        accounts.append(str(token_file))
    print(f"Total: {len(accounts)}\n")
    return accounts

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Manage Gmail Accounts for Bulk Sender")
    parser.add_argument("--add", help="Add a new account (provide email address as alias)")
    parser.add_argument("--list", action="store_true", help="List configured accounts")
    
    args = parser.parse_args()
    
    if args.add:
        add_account(args.add)
    elif args.list:
        list_accounts()
    else:
        parser.print_help()
