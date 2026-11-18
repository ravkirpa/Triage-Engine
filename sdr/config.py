import os
from pathlib import Path

def load_env(path=".env"):
    p = Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def get(key, default=""):
    return os.environ.get(key, default)

DB_PATH = lambda: get("SDR_DB", "data/sdr.db")
CADENCE_DAYS = (1, 3, 5, 7, 9, 11)  # day numbers; day 1 = first email

# Fixed on purpose: never read from env or edited. Use exactly as given.
CALENDLY_LINK = "https://calendly.com/rav-singh-akalinfo/30min"

LOGO_PATH = "assets/tankhapay_logo.png"
SIGNATURE_TEXT = f"""Best Regards,
Rav Singh
Lead - International Business
Book a Meeting : {CALENDLY_LINK}
Best Payroll Outsourcing Services in India | 26+ years of payroll expertise
Akal Information Systems Ltd. (http://www.akalinfosys.com/)
103,Tower J,World Trade Centre
Nauroji Nagar,New Delhi 110029
+91 9871906440
rav.singh@akalinfo.com"""
