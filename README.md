# Outbound SDR agent

Ingests a lead database (POC emails, BI, buyer signals), qualifies by signal, emails on **day 1-3-5-7-9-11**, stops the moment a lead replies, triages replies, and asks leads to self-book through your Calendly link.

## Use
1. `cp .env.example .env` and fill in `CALENDLY_URL`, sender details, SMTP/IMAP. Leave `SDR_SEND=0` for a dry run (logs, sends nothing).
2. In Claude Code run `/lead`. It asks for the database, imports it, shows the hottest leads, and sends Day 1.
3. Schedule `python -m sdr tick` (daily) for follow-ups and reply polling; `python -m sdr report` for the pipeline.

Commands: `ingest <file>`, `tick`, `report`, `reply <email> <text>`. Tests: `python3 -m unittest discover -s tests`.

## Notes
- Stdlib only; XLSX import needs `pip install openpyxl`.
- State lives in `data/sdr.db`. Cloud sessions are ephemeral, so a scheduled run needs this DB on persistent storage.
- Every email carries a "reply stop" opt-out; unsubscribes and bounces end the cadence. Respect CAN-SPAM/GDPR for your lead sources.
