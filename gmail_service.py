import os
import pickle
import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GmailService:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception:
                # If token is invalid/corrupt, proceed to re-auth
                creds = None

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    # If refresh fails, delete token and flow again
                    if os.path.exists(self.token_path):
                        os.remove(self.token_path)
                    creds = self._run_flow()
            else:
                creds = self._run_flow()
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    def _run_flow(self):
        """Run the OAuth flow."""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
            
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, SCOPES)
        return flow.run_local_server(port=0)

    def create_message(self, to, subject, body_html, body_text=None):
        """Create a message for an email."""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['subject'] = subject

        # Attach parts
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            message.attach(part1)
        
        # HTML part (last part is preferred by clients)
        if body_html:
            part2 = MIMEText(body_html, 'html')
            message.attach(part2)
        elif not body_text:
            raise ValueError("Must provide at least body_html or body_text")

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, message):
        """Send an email message."""
        if not self.service:
            raise RuntimeError("Service not authenticated. Call authenticate() first.")

        try:
            message = (self.service.users().messages().send(userId="me", body=message)
                       .execute())
            return message
        except Exception as error:
            raise error

    def create_draft(self, message):
        """Create a draft email."""
        if not self.service:
            raise RuntimeError("Service not authenticated. Call authenticate() first.")

        try:
            draft = {'message': message}
            draft = (self.service.users().drafts().create(userId="me", body=draft)
                     .execute())
            return draft
        except Exception as error:
            raise error
