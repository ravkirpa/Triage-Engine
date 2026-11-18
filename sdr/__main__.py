import argparse, json
from . import config, db, importer, engine, triage

def main():
    config.load_env()
    ap = argparse.ArgumentParser(prog="sdr", description="Outbound SDR agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest", help="import a lead database"); p.add_argument("path")
    sub.add_parser("tick", help="poll replies + send due emails (run on a schedule)")
    sub.add_parser("report", help="pipeline + reply triage summary")
    r = sub.add_parser("reply", help="log a reply manually"); r.add_argument("email"); r.add_argument("text"); r.add_argument("--subject", default="")
    a = ap.parse_args(); con = db.connect()
    if a.cmd == "ingest": print(json.dumps(importer.import_leads(con, a.path)))
    elif a.cmd == "tick": print(json.dumps(engine.tick(con)))
    elif a.cmd == "report": print(json.dumps(engine.report(con), indent=2))
    elif a.cmd == "reply":
        l = con.execute("select id from leads where email=?", (a.email.lower(),)).fetchone()
        print(triage.record_reply(con, l["id"] if l else None, a.email, a.subject, a.text, f"manual-{a.email}-{a.text[:20]}"))
main()
