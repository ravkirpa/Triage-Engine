"""The cadence engine: day 1-3-5-7-9-11, only until the lead replies."""
from datetime import datetime, timedelta, timezone
from . import config, mailer, templates, triage

def now(): return datetime.now(timezone.utc)

def due_step(lead, sent_steps, today=None):
    """Next step number due for this lead, or None. Day N is (N-1) days after the first email."""
    today = today or now()
    if lead["status"] != "active": return None
    nxt = len(sent_steps) + 1
    if nxt > len(config.CADENCE_DAYS): return None
    if not lead["started_at"]: return 1
    start = datetime.fromisoformat(lead["started_at"])
    return nxt if today >= start + timedelta(days=config.CADENCE_DAYS[nxt - 1] - 1) else None

def tick(con, today=None, cap=None):
    """One scheduled run: poll replies first (so we never email someone who answered), then send what's due."""
    today = today or now(); cap = cap or int(config.get("DAILY_SEND_CAP", "40"))
    replies = triage.poll_inbox(con)
    sent_today = con.execute("select count(*) from touches where date(sent_at)=date(?)", (today.isoformat(),)).fetchone()[0]
    sent = 0
    # hottest signals first
    for lead in con.execute("select * from leads where status='active' order by signal_score desc, id").fetchall():
        if sent_today + sent >= cap: print(f"[engine] daily cap {cap} reached"); break
        steps = [r["step"] for r in con.execute("select step from touches where lead_id=?", (lead["id"],))]
        step = due_step(lead, steps, today)
        if not step: continue
        subj, body = templates.render(step, lead)
        prev = con.execute("select message_id from touches where lead_id=? order by step desc limit 1", (lead["id"],)).fetchone()
        mid, dry = mailer.send(lead["email"], subj, body, in_reply_to=prev["message_id"] if prev else None)
        con.execute("insert into touches(lead_id,step,subject,body,message_id,sent_at,dry_run) values(?,?,?,?,?,?,?)",
                    (lead["id"], step, subj, body, mid, today.isoformat(), int(dry)))
        if step == 1: con.execute("update leads set started_at=? where id=?", (today.isoformat(), lead["id"]))
        if step == len(config.CADENCE_DAYS): con.execute("update leads set status='completed' where id=?", (lead["id"],))
        con.commit(); sent += 1
    return {"replies_processed": len(replies), "emails_sent": sent}

def report(con):
    q = lambda s: con.execute(s).fetchall()
    return {"leads_by_status": {r[0]: r[1] for r in q("select status,count(*) from leads group by 1")},
            "replies_by_category": {r[0]: r[1] for r in q("select category,count(*) from replies group by 1")},
            "hot_replies": [dict(r) for r in q("select l.name,l.company,r.category,r.snippet from replies r join leads l on l.id=r.lead_id where r.category in ('interested','question','referral','meeting_booked') order by r.id desc limit 10")]}
