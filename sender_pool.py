from gmail_service import GmailService
from pathlib import Path
import os
import random

class SenderPool:
    def __init__(self, use_simulated=False):
        self.senders = []
        self.use_simulated = use_simulated
        self._load_senders()

    def _load_senders(self):
        token_dir = Path("tokens")
        if not token_dir.exists():
            return

        for token_file in token_dir.glob("*.json"):
            if not token_file.is_file():
                continue
            
            try:
                # Assuming filename is email.json
                email = token_file.stem 
                # Create service (which loads creds)
                # But creating service is expensive (API call), let's defer?
                # Actually, creating GmailService with token path is fast unless expired
                service = GmailService(token_file=str(token_file), credentials_file="credentials.json")
                if service.service: # Make sure service init worked
                     self.senders.append(service)
                     print(f"✅ Loaded sender: {service.email_address}")
            except Exception as e:
                print(f"⚠️  Failed to load account {token_file}: {e}")

    def get_sender(self):
        """Returns a sender service (round robin / random)."""
        if not self.senders:
            return None
        
        # Simple random selection for load balancing
        return random.choice(self.senders)

    def count(self):
        return len(self.senders)
