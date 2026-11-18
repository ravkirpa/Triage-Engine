"""Reply handling: classify inbound mail and stop the cadence when a lead answers."""
import re

RULES = [  # order matters
 ("unsubscribe", r"\b(stop|unsubscribe|remove me|do not contact|don'?t contact)\b"),
 ("out_of_office", r"(out of office|auto[- ]?reply|automatic reply|on leave|away until)"),
 ("bounce", r"(delivery status|undeliverable|mailer-daemon|address not found)"),
 ("meeting_booked", r"(calendly|invitation:|accepted:|scheduled|booked)"),
 ("not_interested", r"\b(not interested|no thanks|not a fit|not now|no budget|already (have|use))\b"),
 ("interested", r"\b(interested|sounds good|let'?s (talk|chat|connect)|send (me )?(more|details|pricing)|yes|happy to)\b"),
 ("referral", r"\b(reach out to|speak (to|with)|contact|forward(ed)? (this )?to|cc'?d)\b"),
 ("question", r"\?"),
]
TERMINAL = {"unsubscribe": "unsubscribed", "bounce": "bounced", "meeting_booked": "meeting_booked"}

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
