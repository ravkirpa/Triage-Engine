"""Cadence engine: day 1-3-5-7-9-11, only until the lead replies. Emails are queued for Gmail drafting;
nothing here sends mail. Every active lead is emailed regardless of intent (FIFO order)."""
from datetime import datetime, timedelta, timezone
from . import config, templates

def now(): return datetime.now(timezone.utc)

def day_offset(step):
    """Step 1 on day 1; every later step 2 days after the previous one (day 3, 5, 7, 9, 11, 13, ...)."""
    return 2 * (step - 1)

def due_step(lead, sent_steps, today=None):
    today = today or now()
    if lead["status"] != "active": return None
    nxt = len(sent_steps) + 1
    if not lead["started_at"]: return None if sent_steps else 1   # step 1 drafted, awaiting approval
    start = datetime.fromisoformat(lead["started_at"])
    return nxt if today >= start + timedelta(days=day_offset(nxt)) else None

def due(con, today=None, cap=None, total_cap=None):
    """Emails due now. Hard limit of `total_cap` a day (default 80). Follow-ups go first (oldest due first);
    new first emails fill the rest, at most `cap` (default 40). Skips anyone who has replied."""
    today = today or now(); cap = cap or int(config.get("DAILY_SEND_CAP", "40"))
    total_cap = total_cap or int(config.get("TOTAL_SEND_CAP", "80")); follow, new = [], []
    for lead in con.execute("select * from leads where status='active' order by id").fetchall():
        steps = [r["step"] for r in con.execute("select step from touches where lead_id=?", (lead["id"],))]
        step = due_step(lead, steps, today)
        if not step: continue
        campaign, subj, body = templates.render(step, lead)
        item = dict(email=lead["email"], lead_id=lead["id"], step=step, day=day_offset(step) + 1,
                    campaign=campaign, subject=subj, body=body, html_body=templates.to_html(body),
                    include_gmail_signature=True, calendly_link=config.CALENDLY_LINK)
        (new if step == 1 else follow).append(item)
    follow = follow[:total_cap]                       # anything over the limit slips to the next run
    return follow + new[:max(0, min(cap, total_cap - len(follow)))]

def mark_sent(con, email, step, ref="", today=None):
    """Record that step N went out (draft sent from Gmail). Starts the day-1 clock on step 1."""
    today = today or now(); lead = con.execute("select * from leads where email=?", (email.lower(),)).fetchone()
    if not lead: raise SystemExit(f"unknown lead {email}")
    _, subj, body = templates.render(step, lead)
    con.execute("insert or ignore into touches(lead_id,step,subject,body,message_id,sent_at) values(?,?,?,?,?,?)",
                (lead["id"], step, subj, body, ref, today.isoformat()))
    if step == 1: con.execute("update leads set started_at=? where id=?", (today.isoformat(), lead["id"]))
    con.commit()

def mark_drafted(con, email, step, ref="", today=None):
    """Fallback mode: a Gmail draft exists, awaiting the user's approval. Does not start the follow-up clock."""
    today = today or now(); lead = con.execute("select * from leads where email=?", (email.lower(),)).fetchone()
    if not lead: raise SystemExit(f"unknown lead {email}")
    _, subj, body = templates.render(step, lead)
    con.execute("insert or ignore into touches(lead_id,step,subject,body,message_id,sent_at,dry_run) values(?,?,?,?,?,?,2)",
                (lead["id"], step, subj, body, ref, today.isoformat())); con.commit()

def approve(con, today=None):
    """User approved and the drafts were sent: turn drafts into sends and start the clock for step 1."""
    today = today or now(); rows = con.execute("select lead_id, step from touches where dry_run=2").fetchall()
    for r in rows:
        con.execute("update touches set dry_run=0, sent_at=? where lead_id=? and step=?", (today.isoformat(), r["lead_id"], r["step"]))
        if r["step"] == 1: con.execute("update leads set started_at=? where id=? and started_at is null", (today.isoformat(), r["lead_id"]))
    con.commit(); return len(rows)

def report(con):
    q = lambda s: con.execute(s).fetchall()
    return {"leads_by_status": {r[0]: r[1] for r in q("select status,count(*) from leads group by 1")},
            "replies_by_category": {r[0]: r[1] for r in q("select category,count(*) from replies group by 1")},
            "drafts_awaiting_approval": con.execute("select count(*) from touches where dry_run=2").fetchone()[0],
            "needs_your_attention": [dict(r) for r in q("select l.name,l.company,l.email,r.category,r.snippet from replies r join leads l on l.id=r.lead_id where r.category in ('interested','question','referral','meeting_booked') order by r.id desc limit 20")]}
