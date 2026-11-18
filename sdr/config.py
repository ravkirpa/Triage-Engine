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
