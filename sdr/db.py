import sqlite3
from pathlib import Path
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads(
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT, company TEXT, title TEXT,
  signal TEXT, signal_score INTEGER DEFAULT 0, extra TEXT,
  status TEXT NOT NULL DEFAULT 'active',  -- active|replied|meeting_booked|unsubscribed|bounced|completed|disqualified
  started_at TEXT, replied_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS touches(
  id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id), step INTEGER NOT NULL,
  subject TEXT, body TEXT, message_id TEXT, sent_at TEXT, dry_run INTEGER DEFAULT 0,
  UNIQUE(lead_id, step));
CREATE TABLE IF NOT EXISTS replies(
  id INTEGER PRIMARY KEY, lead_id INTEGER REFERENCES leads(id), from_email TEXT, subject TEXT,
  snippet TEXT, category TEXT, received_at TEXT, message_id TEXT UNIQUE);
"""

def connect(path=None):
    path = path or config.DB_PATH()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
