"""Reply handling: classify inbound mail and stop the cadence when a lead answers."""
import re

RULES = [  # order matters
 ("unsubscribe", r"\b(stop|unsubscribe|remove me|do not contact|don'?t contact)\b"),
 ("left_company", r"(no longer (working|with|at|employed)|has left|have left|left the (company|organi[sz]ation)|ceased (to be )?employ)"),
 ("out_of_office", r"(out of office|auto[- ]?reply|automatic reply|on leave|away until)"),
 ("bounce", r"(delivery status|undeliverable|mailer-daemon|address not found)"),
 ("meeting_booked", r"(calendly|invitation:|accepted:|scheduled|booked)"),
 ("not_interested", r"\b(not interested|no thanks|not a fit|not now|no budget|already (have|use))\b"),
 ("interested", r"\b(interested|sounds good|let'?s (talk|chat|connect)|send (me )?(more|details|pricing)|yes|happy to)\b"),
 ("referral", r"\b(reach out to|speak (to|with)|contact|forward(ed)? (this )?to|cc'?d)\b"),
 ("question", r"\?"),
]
TERMINAL = {"left_company": "removed", "unsubscribe": "unsubscribed", "bounce": "bounced", "meeting_booked": "meeting_booked"}

def suppress(con, email, reason="manual"):
    """Permanently remove a person from all follow-ups (also blocks future imports)."""
    email = email.lower()
    con.execute("insert or replace into suppressed(email,reason) values(?,?)", (email, reason))
    con.execute("update leads set status='removed' where email=? and status='active'", (email,))
    con.commit()

def classify(subject, text):
    blob = f"{subject}\n{text}".lower()
    return next((c for c, rx in RULES if re.search(rx, blob)), "other")

def record_reply(con, lead_id, from_email, subject, text, message_id, received_at=None):
    cat = classify(subject, text)
    if con.execute("select 1 from replies where message_id=?", (message_id,)).fetchone(): return None
    con.execute("insert into replies(lead_id,from_email,subject,snippet,category,received_at,message_id) values(?,?,?,?,?,?,?)",
                (lead_id, from_email, subject, text[:300], cat, received_at, message_id))
    if lead_id and cat != "out_of_office":   # any real answer ends the cadence
        status = TERMINAL.get(cat, "replied")
        con.execute("update leads set status=?, replied_at=coalesce(replied_at, datetime('now')) where id=? and status='active'", (status, lead_id))
    con.commit(); return cat

import re as _re
EMAIL_ANY = _re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NOT_HR = ("support@", "noreply@", "no-reply@", "it@", "helpdesk@", "mailer-daemon@", "postmaster@")

def cover_contacts(text, own_email, our_emails=()):
    """Addresses named in an auto-reply as cover or HR contacts (not the sender, not us, not IT/support lines)."""
    skip = {own_email.lower(), *[e.lower() for e in our_emails]}
    seen = []
    for e in EMAIL_ANY.findall(text or ""):
        e = e.lower().rstrip(".")
        if e in skip or e in seen or e.startswith(NOT_HR) or e.split("@")[-1].endswith(("trendmicro.com",)): continue
        seen.append(e)
    return seen

def add_cover(con, original_email, cover_email, reason="covering"):
    """Add the covering/HR person named in an auto-reply as a new lead, same company and bottleneck. Returns True if added."""
    import json
    o = con.execute("select * from leads where email=?", (original_email.lower(),)).fetchone()
    cover_email = cover_email.lower()
    if con.execute("select 1 from leads where email=?", (cover_email,)).fetchone() or con.execute("select 1 from suppressed where email=?", (cover_email,)).fetchone():
        return False
    company = o["company"] if o else ""; sig = o["signal"] if o else ""
    extra = json.dumps({"bottleneck_basis": "cover contact", "covering_for": original_email, "reason": reason})
    con.execute("insert into leads(email,name,company,title,signal,signal_score,extra) values(?,?,?,?,?,0,?)",
                (cover_email, "", company, f"cover contact ({reason})", sig, extra)); con.commit(); return True
