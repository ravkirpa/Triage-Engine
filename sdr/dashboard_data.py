"""Builds the dashboard datasets (aggregates only, no emails) from the campaign database.
Run: python -m sdr.dashboard_data <out_dir>   -> actual_daily.json, projected_daily.json, funnel.json, campaigns.json, events.json"""
import json, os, shutil, sys, tempfile, collections as C
from datetime import datetime, timedelta, timezone
from . import db, engine, config

def build(out):
    os.makedirs(out, exist_ok=True); con = db.connect(); q = lambda s, *a: con.execute(s, a).fetchall()
    meta = lambda label: [{"label": "Built by", "value": "sdr/dashboard_data.py", "type": "code", "lang": "python"}, {"label": "Dataset", "value": label}]
    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    # sends per day (real)
    rows = [dict(date=r[0], new=r[1], follow_ups=r[2], total=r[1] + r[2]) for r in
            q("select date(sent_at), sum(step=1), sum(step>1) from touches where dry_run=0 group by 1 order by 1")]
    json.dump({"rows": rows, "meta": meta("Emails sent per day (actual)") + [{"label": "As of (UTC)", "value": now}]}, open(f"{out}/actual_daily.json", "w"))
    # projection: simulate the real schedule on a copy of the database
    tmp = tempfile.mkdtemp(); shutil.copy(config.DB_PATH(), f"{tmp}/sim.db"); sim = db.connect(f"{tmp}/sim.db")
    d0 = datetime.now(timezone.utc).replace(hour=5, minute=1, second=0, microsecond=0) + timedelta(days=1); proj = []
    for i in range(120):
        t = d0 + timedelta(days=i); due = engine.due(sim, today=t)
        for x in due: engine.mark_sent(sim, x["email"], x["step"], today=t)
        if due: proj.append(dict(date=str(t.date()), new=sum(x["step"] == 1 for x in due), follow_ups=sum(x["step"] > 1 for x in due), total=len(due)))
    left = sim.execute("select count(*) from leads where status='active'").fetchone()[0]
    json.dump({"rows": proj, "meta": meta("Projected sends (same rules, 20 new a day, 80 total, weekdays only)") + [{"label": "Leads still active at the end", "value": str(left)}]}, open(f"{out}/projected_daily.json", "w")); shutil.rmtree(tmp)
    # funnel / status
    st = dict(q("select status,count(*) from leads group by 1")); started = q("select count(distinct lead_id) from touches where dry_run=0")[0][0]
    steps = dict(q("select step,count(*) from touches where dry_run=0 group by 1"))
    names = {1: "First email", 2: "Follow-up 1 · Problem", 3: "Follow-up 2 · Insight", 4: "Follow-up 3 · Proof", 5: "Follow-up 4 · Solution", 6: "Follow-up 5 · Next step"}
    fun = [dict(stage="Leads loaded", leads=sum(st.values())), dict(stage="Emailed at least once", leads=started),
           dict(stage="Waiting for first email", leads=q("select count(*) from leads where status='active' and id not in (select lead_id from touches)")[0][0]),
           dict(stage="Replied (positive or negative)", leads=st.get("replied", 0) + st.get("meeting_booked", 0)),
           dict(stage="Removed (bounce, left company, leave)", leads=st.get("removed", 0)), dict(stage="Finished both rounds", leads=st.get("completed", 0))]
    json.dump({"rows": fun, "meta": meta("Lead funnel")}, open(f"{out}/funnel.json", "w"))
    cs = C.Counter(); 
    from . import templates
    for l in q("select * from leads where status!='removed'"): cs[templates.render(1, l)[0]] += 1
    lab = {"sg_quote": "Singapore list ($8 quote)", "bank_rosters": "Rosters & leave approvals", "bank_timesheets": "Timesheets, employees vs contractors", "bank_locations": "Shifts across locations",
           "bank_approvals": "Joiner / leaver approvals", "bank_mixed_teams": "Time & data across teams", "bank_fragmented_apps": "Data split across apps", "bank_split_shifts": "Split shifts, casual staff",
           "bank_volunteers": "Employees vs volunteers", "attendance": "Attendance & shifts", "multi_entity": "Multiple entities", "integration": "System integration", "payroll_compliance": "Payroll compliance",
           "onboarding_admin": "HR administration", "general": "General"}
    json.dump({"rows": [dict(campaign=lab.get(k, k), leads=v) for k, v in cs.most_common()], "meta": meta("Active leads per campaign")}, open(f"{out}/campaigns.json", "w"))
    # timeline of milestones and incidents (aggregates and reasons only)
    ev = [dict(date="2026-11-18", event="Test round", detail="5 hand-sent emails; 2 auto-replies (left company, on leave)", kind="send"),
          dict(date="2026-11-19", event="Campaign launch", detail="40 first emails (20 shortlist, 20 Employment Hero data)", kind="send"),
          dict(date="2026-11-19", event="Bounce", detail="1 invalid address removed", kind="problem"),
          dict(date="2026-11-20", event="Second batch", detail="40 first emails", kind="send"),
          dict(date="2026-11-20", event="Singapore list", detail="16 contacts, $8 per employee per month quote", kind="send"),
          dict(date="2026-11-20", event="Cover contacts", detail="Auto-replies named 5 cover or HR contacts, all emailed", kind="send"),
          dict(date="2026-11-20", event="Bounces and leave", detail="5 invalid addresses removed; 1 person on long leave removed, cover contact emailed", kind="problem"),
          dict(date="2026-11-23", event="Aggressive cadence starts", detail="Daily on weekdays, 20 new a day, 80 total, 2 rounds then stop", kind="plan")]
    json.dump({"rows": ev, "meta": meta("Campaign milestones and incidents")}, open(f"{out}/events.json", "w"))
    return {k: len(json.load(open(f"{out}/{k}.json"))["rows"]) for k in ("actual_daily", "projected_daily", "funnel", "campaigns", "events")}

if __name__ == "__main__": print(build(sys.argv[1]))
