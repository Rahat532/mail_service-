import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class Reader:
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(Reader.EMAIL_REGEX.match(email))

    @staticmethod
    def load_leads(filepath: Path) -> List[Dict[str, str]]:
        """
        Load leads from CSV or TXT file.
        Returns a list of dictionaries. For TXT, only 'email' key exists.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Leads file not found: {filepath}")

        leads = []
        seen_emails = set()

        if filepath.suffix.lower() == '.csv':
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # Normalize headers: strip whitespace
                if reader.fieldnames:
                    reader.fieldnames = [name.strip() for name in reader.fieldnames]
                
                for row in reader:
                    # Find email column (case-insensitive)
                    email_col = next((k for k in row.keys() if k.lower() == 'email'), None)
                    if email_col and row[email_col]:
                        email = row[email_col].strip()
                        if Reader.validate_email(email) and email not in seen_emails:
                            row['email'] = email  # Ensure standardized key
                            leads.append(row)
                            seen_emails.add(email)

        else:  # Assume TXT (one email per line)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    email = line.strip()
                    if Reader.validate_email(email) and email not in seen_emails:
                        leads.append({'email': email})
                        seen_emails.add(email)

        return leads

    @staticmethod
    def load_content(filepath: Path) -> Tuple[str, str, str]:
        """
        Load content from a file.
        Expected format for TXT/HTML files generally contains:
        Subject: <Subject Line>
        
        Body content starts after the Subject line (and optional blank lines).
        
        Returns: (Subject, Body_HTML, Body_Text)
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Content file not found: {filepath}")

        raw_content = filepath.read_text(encoding='utf-8')
        lines = raw_content.splitlines()

        subject = "No Subject"
        body_start_idx = 0

        # Parse Subject
        if lines and lines[0].lower().startswith("subject:"):
            subject = lines[0].split(":", 1)[1].strip()
            body_start_idx = 1
            # Skip empty lines after subject
            while body_start_idx < len(lines) and not lines[body_start_idx].strip():
                body_start_idx += 1

        body_content = "\n".join(lines[body_start_idx:])
        
        # If HTML file, Body is HTML. If TXT, Body is Plain Text.
        if filepath.suffix.lower() == '.html':
            return subject, body_content, None
        else:
            return subject, None, body_content
