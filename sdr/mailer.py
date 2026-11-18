import smtplib, ssl, time
from email.message import EmailMessage
from email.utils import make_msgid
from . import config

def send(to, subject, body, in_reply_to=None):
    """Returns (message_id, dry_run). Dry run unless SDR_SEND=1."""
    msg = EmailMessage()
    msg["From"] = f"{config.get('SENDER_NAME')} <{config.get('FROM_EMAIL')}>"
    msg["To"] = to; msg["Subject"] = subject
    msg["Message-ID"] = mid = make_msgid(domain=(config.get("FROM_EMAIL").split("@")[-1] or "localhost"))
    if in_reply_to: msg["In-Reply-To"] = msg["References"] = in_reply_to
    msg.set_content(body)
    if config.get("SDR_SEND") != "1":
        print(f"[dry-run] to={to} subject={subject!r}"); return mid, True
    with smtplib.SMTP(config.get("SMTP_HOST"), int(config.get("SMTP_PORT", "587"))) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(config.get("SMTP_USER"), config.get("SMTP_PASSWORD")); s.send_message(msg)
    time.sleep(2)  # gentle pacing
    return mid, False
