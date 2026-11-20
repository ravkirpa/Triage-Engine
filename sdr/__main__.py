import argparse, json
from . import config, db, importer, engine, triage

def main():
    config.load_env()
    ap = argparse.ArgumentParser(prog="sdr", description="Outbound SDR agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest", help="import a lead database"); i.add_argument("path"); i.add_argument("--bank", help="account-intelligence workbook with the Bottleneck Bank")
    sub.add_parser("due", help="JSON list of emails due now (to be drafted via Gmail)")
    m = sub.add_parser("sent", help="mark a step as sent"); m.add_argument("email"); m.add_argument("step", type=int); m.add_argument("--ref", default="")
    x = sub.add_parser("suppress", help="remove a person from all follow-ups"); x.add_argument("email"); x.add_argument("--reason", default="manual")
    d = sub.add_parser("drafted", help="record a Gmail draft awaiting approval"); d.add_argument("email"); d.add_argument("step", type=int); d.add_argument("--ref", default="")
    sub.add_parser("approve", help="user approved: mark all pending drafts as sent")
    c = sub.add_parser("cover", help="add the cover/HR contact named in an auto-reply"); c.add_argument("original"); c.add_argument("cover_email"); c.add_argument("--reason", default="covering")
    sub.add_parser("report", help="pipeline + reply triage summary")
    r = sub.add_parser("reply", help="log an inbound reply (stops the cadence)"); r.add_argument("email"); r.add_argument("text"); r.add_argument("--subject", default=""); r.add_argument("--id", default="")
    a = ap.parse_args(); con = db.connect()
    if a.cmd == "ingest": print(json.dumps(importer.import_leads(con, a.path, a.bank)))
    elif a.cmd == "due": print(json.dumps(engine.due(con), indent=2))
    elif a.cmd == "sent": engine.mark_sent(con, a.email, a.step, a.ref); print("ok")
    elif a.cmd == "suppress": triage.suppress(con, a.email, a.reason); print("removed", a.email)
    elif a.cmd == "drafted": engine.mark_drafted(con, a.email, a.step, a.ref); print("ok")
    elif a.cmd == "approve": print(engine.approve(con), "drafts marked sent")
    elif a.cmd == "cover": print("added" if triage.add_cover(con, a.original, a.cover_email, a.reason) else "already known")
    elif a.cmd == "report": print(json.dumps(engine.report(con), indent=2))
    elif a.cmd == "reply":
        l = con.execute("select id from leads where email=?", (a.email.lower(),)).fetchone()
        print(triage.record_reply(con, l["id"] if l else None, a.email, a.subject, a.text, a.id or f"manual-{a.email}-{a.text[:20]}"))
main()
