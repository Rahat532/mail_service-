import os.path
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class GmailService:

    def __init__(self, token_file=None, credentials_file='credentials.json'):
        self.token_file = token_file
        self.credentials_file = credentials_file
        self.service = None
        self.email_address = None
        if self.token_file:
             self.authenticate()

    def authenticate(self):
        """Authenticates the user and returns the Gmail service object."""
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logging.error(f"Error refreshing token: {e}")
                    creds = None # Force re-auth
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                     raise FileNotFoundError(f"Missing {self.credentials_file}. You must download OAuth 2.0 Credentials from Google Cloud Console.")
                
                print("🔑 Initiating OAuth flow... Please check your browser.")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                     raise RuntimeError(f"Failed to authenticate: {e}")

            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token saved to token.json")


        try:
            self.service = build('gmail', 'v1', credentials=creds)
            # Fetch user email for reference
            profile = self.service.users().getProfile(userId='me').execute()
            self.email_address = profile['emailAddress']
            print(f"✅ Authenticated as: {self.email_address}")
        except HttpError as error:
             logging.error(f'An error occurred: {error}')
             self.service = None

    def create_message(self, sender, to, subject, body_html=None, body_text=None):
        """Create a message for an email."""
        message = MIMEMultipart("alternative")
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        if body_text:
             part1 = MIMEText(body_text, 'plain')
             message.attach(part1)
        
        if body_html:
             part2 = MIMEText(body_html, 'html')
             message.attach(part2)

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_email(self, to_email, subject, body_html=None, body_text=None):
        """Send an email message."""
        if not self.service:
            raise RuntimeError("Gmail Service not initialized.")

        try:
            # We need the user's email address to set the 'from' field correctly
            # Usually 'me' works for the authenticated user
            profile = self.service.users().getProfile(userId='me').execute()
            sender_email = profile['emailAddress']

            message = self.create_message(sender_email, to_email, subject, body_html, body_text)
            sent_message = self.service.users().messages().send(userId="me", body=message).execute()
            logging.info(f'Message Id: {sent_message["id"]}')
            return sent_message
        except HttpError as error:
            logging.error(f'An error occurred: {error}')
            raise RuntimeError(f'Error sending email: {error}')
