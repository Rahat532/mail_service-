import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SMTPService:
    def __init__(self, email_address: str, app_password: str, host: str = "smtp.gmail.com", port: int = 587):
        self.email_address = email_address
        self.app_password = app_password
        self.host = host
        self.port = port

    def send_email(self, to_email: str, subject: str, body_html: str = None, body_text: str = None):
        """
        Send an email via SMTP.
        """
        if not body_html and not body_text:
            raise ValueError("Must provide at least body_html or body_text")

        # Create message container
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.email_address
        message["To"] = to_email

        # Attach text part first (fallback)
        if body_text:
            part1 = MIMEText(body_text, "plain")
            message.attach(part1)

        # Attach HTML part last (preferred)
        if body_html:
            part2 = MIMEText(body_html, "html")
            message.attach(part2)

        # Create secure connection and send
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.email_address, self.app_password)
                server.sendmail(self.email_address, to_email, message.as_string())
        except Exception as e:
            # Re-raise to be caught by the main loop's failure handler
            raise RuntimeError(f"SMTP Error: {e}") from e
