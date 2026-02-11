import time
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ============================================================
# CONFIG LOADER
# ============================================================
def load_config(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError("config.json not found.")
    return json.loads(path.read_text(encoding="utf-8"))


# ============================================================
# FILE LOADERS
# ============================================================
def load_senders(path: Path) -> List[Tuple[str, str]]:
    """
    Supports client's format:
    email <whitespace/tab> password <whitespace/tab> confirm_password(optional)

    Example:
    m-10828325@moe-dl.edu.my    pass123    pass123
    """
    if not path.exists():
        raise RuntimeError("senders.txt not found.")

    senders: List[Tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()  # splits on any whitespace (tabs or spaces)
        if len(parts) < 2:
            raise ValueError(f"Bad sender line (need at least email + password): {raw}")

        email = parts[0].strip()
        password = parts[1].strip()

        if len(parts) >= 3:
            confirm = parts[2].strip()
            if password != confirm:
                raise ValueError(f"Password mismatch for sender: {email}")

        senders.append((email, password))

    if not senders:
        raise ValueError("No senders loaded from senders.txt.")
    return senders


def load_recipients_txt(path: Path) -> List[str]:
    """
    recipients.txt: one email per line
    """
    if not path.exists():
        raise RuntimeError("recipients.txt not found.")

    recips: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        email = raw.strip()
        if email and not email.startswith("#"):
            recips.append(email)

    if not recips:
        raise ValueError("No recipients loaded from recipients.txt.")
    return recips


def load_template(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"Template file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def render(tpl: str, data: Dict[str, str]) -> str:
    """
    Simple placeholder rendering: "Hello {email}" -> fill from data.
    Missing keys become empty.
    """
    class SafeDict(dict):
        def __missing__(self, key):
            return ""
    return tpl.format_map(SafeDict(data))


# ============================================================
# SENDER ROTATION
# ============================================================
class RoundRobin:
    def __init__(self, items: List[Tuple[str, str]]):
        self.items = items
        self.i = 0

    def next(self) -> Tuple[str, str]:
        item = self.items[self.i]
        self.i = (self.i + 1) % len(self.items)
        return item


# ============================================================
# RETRY HELPER
# ============================================================
def with_retries(fn, retries: int, backoff_base: float):
    last = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            last = e
            sleep_s = (backoff_base ** (attempt - 1)) + random.random() * 0.25
            time.sleep(sleep_s)
    raise last


# ============================================================
# COMPANY MAIL ADAPTER (DRY RUN NOW, REAL API LATER)
# ============================================================
@dataclass
class TokenInfo:
    token: str
    expires_at: float


class CompanyMailAdapter:
    """
    Right now:
      - login() returns a fake token
      - send_mail() does nothing (dry run)
    Later:
      - replace login() and send_mail() with real company endpoints / SDK.
    """

    def __init__(self, token_refresh_skew_sec: int = 30):
        self._tokens: Dict[str, TokenInfo] = {}
        self._skew = token_refresh_skew_sec

    def login(self, sender_email: str, sender_password: str) -> Tuple[str, int]:
        """
        TODO: Replace with real company auth.
        Must return: (token, expires_in_seconds)
        """
        fake_token = f"FAKE_TOKEN_FOR_{sender_email}"
        return fake_token, 600  # 10 minutes

    def get_token(self, sender_email: str, sender_password: str) -> str:
        now = time.time()
        info = self._tokens.get(sender_email)
        if info and now < (info.expires_at - self._skew):
            return info.token

        token, expires_in = self.login(sender_email, sender_password)
        self._tokens[sender_email] = TokenInfo(token=token, expires_at=now + expires_in)
        return token

    def send_mail(self, token: str, from_email: str, to_email: str, subject: str, body_text: str) -> None:
        """
        TODO: Replace with real company send mail function.
        For now: pretend success.
        """
        return


# ============================================================
# MAIN
# ============================================================
def main():
    base = Path(".")
    cfg = load_config(base / "config.json")

    mode = str(cfg.get("mode", "dry_run")).lower()
    rate_per_sec = float(cfg.get("rate_per_sec", 3))
    retries = int(cfg.get("retries", 3))
    backoff_base = float(cfg.get("backoff_base", 1.5))
    token_skew = int(cfg.get("token_refresh_skew_sec", 30))

    delay = 1.0 / rate_per_sec if rate_per_sec > 0 else 0.0

    senders = load_senders(base / "senders.txt")
    recipients = load_recipients_txt(base / "recipients.txt")
    subject_tpl = load_template(base / "templates" / "subject.txt")
    body_tpl = load_template(base / "templates" / "body.txt")

    logs_dir = base / "logs"
    logs_dir.mkdir(exist_ok=True)
    send_log_path = logs_dir / "send.log"
    fail_log_path = logs_dir / "fail.log"

    rr = RoundRobin(senders)
    adapter = CompanyMailAdapter(token_refresh_skew_sec=token_skew)

    sent = 0
    failed = 0

    print(f"Mode: {mode}")
    print(f"Senders: {len(senders)} | Recipients: {len(recipients)} | Rate: {rate_per_sec}/sec")
    print("-" * 70)

    with send_log_path.open("a", encoding="utf-8") as slog, fail_log_path.open("a", encoding="utf-8") as flog:
        for idx, to_email in enumerate(recipients, start=1):
            sender_email, sender_pw = rr.next()

            data = {"email": to_email}
            subject = render(subject_tpl, data)
            body_text = render(body_tpl, data)

            def action():
                token = adapter.get_token(sender_email, sender_pw)
                if mode == "dry_run":
                    print(f"[{idx}] DRYRUN -> to={to_email} from={sender_email} token={token[:30]}...")
                    return
                adapter.send_mail(token, sender_email, to_email, subject, body_text)

            try:
                with_retries(action, retries=retries, backoff_base=backoff_base)
                sent += 1
                slog.write(json.dumps({"to": to_email, "from": sender_email, "ok": True}) + "\n")
                slog.flush()
                if mode != "dry_run":
                    print(f"[{idx}] SENT -> {to_email} (from {sender_email})")
            except Exception as e:
                failed += 1
                print(f"[{idx}] FAIL -> {to_email} (from {sender_email}) | {type(e).__name__}: {e}")
                flog.write(json.dumps({"to": to_email, "from": sender_email, "ok": False, "err": str(e)}) + "\n")
                flog.flush()

            if delay > 0:
                time.sleep(delay)

    print("-" * 70)
    if failed == 0:
        print(f"SUCCESS ✅ Sent={sent} Failed={failed}")
    else:
        print(f"DONE ⚠️ Sent={sent} Failed={failed}")


if __name__ == "__main__":
    main()
