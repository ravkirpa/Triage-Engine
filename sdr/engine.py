"""Cadence engine: day 1-3-5-7-9-11, only until the lead replies. Emails are queued for Gmail drafting;
nothing here sends mail. Every active lead is emailed regardless of intent (FIFO order)."""
from datetime import datetime, timedelta, timezone
from . import config, templates

def now(): return datetime.now(timezone.utc)

def due_step(lead, sent_steps, today=None):
    today = today or now()
    if lead["status"] != "active": return None
    nxt = len(sent_steps) + 1
    if nxt > len(config.CADENCE_DAYS): return None
    if not lead["started_at"]: return 1
    start = datetime.fromisoformat(lead["started_at"])
    return nxt if today >= start + timedelta(days=config.CADENCE_DAYS[nxt - 1] - 1) else None

def due(con, today=None, cap=None):
    """Emails that should go out now (not yet drafted/sent). Skips anyone who has replied."""
    today = today or now(); cap = cap or int(config.get("DAILY_SEND_CAP", "40")); out = []
    for lead in con.execute("select * from leads where status='active' order by id").fetchall():
        if len(out) >= cap: break
        steps = [r["step"] for r in con.execute("select step from touches where lead_id=?", (lead["id"],))]
        step = due_step(lead, steps, today)
        if step:
            campaign, subj, body = templates.render(step, lead)
            out.append(dict(email=lead["email"], lead_id=lead["id"], step=step, day=config.CADENCE_DAYS[step-1],
                            campaign=campaign, subject=subj, body=body, calendly_link=config.CALENDLY_LINK,
                            attachment=config.LOGO_PATH))
    return out

def mark_sent(con, email, step, ref="", today=None):
    """Record that step N went out (draft sent from Gmail). Starts the day-1 clock on step 1."""
    today = today or now(); lead = con.execute("select * from leads where email=?", (email.lower(),)).fetchone()
    if not lead: raise SystemExit(f"unknown lead {email}")
    _, subj, body = templates.render(step, lead)
    con.execute("insert or ignore into touches(lead_id,step,subject,body,message_id,sent_at) values(?,?,?,?,?,?)",
                (lead["id"], step, subj, body, ref, today.isoformat()))
    if step == 1: con.execute("update leads set started_at=? where id=?", (today.isoformat(), lead["id"]))
    if step == len(config.CADENCE_DAYS): con.execute("update leads set status='completed' where id=? and status='active'", (lead["id"],))
    con.commit()

def report(con):
    q = lambda s: con.execute(s).fetchall()
    return {"leads_by_status": {r[0]: r[1] for r in q("select status,count(*) from leads group by 1")},
            "replies_by_category": {r[0]: r[1] for r in q("select category,count(*) from replies group by 1")},
            "needs_your_attention": [dict(r) for r in q("select l.name,l.company,l.email,r.category,r.snippet from replies r join leads l on l.id=r.lead_id where r.category in ('interested','question','referral','meeting_booked') order by r.id desc limit 20")]}
