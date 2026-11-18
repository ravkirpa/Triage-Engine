# Outbound SDR agent (TankhaPay)

Ingests a lead database (company, POC, POC email, BI, **bottlenecks**), groups leads into bottleneck-led campaigns (multi-entity, payroll/compliance, attendance, workforce mix, integration, performance/L&D, HR admin, general), and emails every lead on **day 1-3-5-7-9-11** until they reply. Intent never gates or ranks sends. Technology only: Global HRMS + payroll.

## Flow
1. `/lead` only activates the agent and asks for the database; the daily routine (`docs/DAILY_ROUTINE.md`) does the rest, on a schedule.
2. Each due email is created as a **Gmail draft** through the Gmail connector (the connector can draft and read, not send). Send the drafts, then `python -m sdr sent <email> <step>` records them and starts the cadence clock.
3. Replies are found via Gmail search and logged with `python -m sdr reply`, which stops that lead's cadence and triages the reply.
4. Leads self-book through the Calendly link in the signature (`CALENDLY_URL`).

Commands: `ingest <file>`, `due`, `sent <email> <step>`, `reply <email> <text>`, `report`. Tests: `python3 -m unittest discover -s tests`.

State is in `data/sdr.db` (git-ignored); cloud sessions are ephemeral, so keep it on persistent storage for scheduled runs.
