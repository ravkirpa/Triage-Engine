import os, tempfile, unittest
from datetime import datetime, timedelta, timezone
os.environ.update(CALENDLY_URL="https://calendly.com/rav-singh-akalinfo/30min")
from sdr import db, importer, engine, triage

class T(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp(); self.con = db.connect(f"{d}/t.db")
        self.csv = f"{d}/l.csv"; open(f"{d}/l.csv", "w").write("POC Email,POC Name,Company,Bottleneck\na@x.com,Ann Lee,Acme,separate tools across multiple entities\nbad,,,\nb@y.com,Bob,Beta,\n")
        self.res = importer.import_leads(self.con, f"{d}/l.csv")
    def test_import(self):
        self.assertEqual((self.res["new"], self.res["skipped_unverified_invalid_or_contacted"]), (2, 1))
    def test_daily_weekday_cadence_two_rounds(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)          # a Thursday
        sent = {}; subjects = {}
        for day in range(40):
            now = t0 + timedelta(days=day)
            due = engine.due(self.con, today=now, cap=100, total_cap=100)
            if now.weekday() >= 5: self.assertEqual(due, [])      # nothing on Saturday or Sunday
            for d in due:
                engine.mark_sent(self.con, d["email"], d["step"], today=now)
                sent.setdefault(d["email"], []).append((day, d["step"])); subjects.setdefault(d["email"], set()).add(d["subject"])
        for email, rows in sent.items():
            self.assertEqual([st for _, st in rows], list(range(1, 12)))              # first email + 10 follow-ups, then stop
            self.assertTrue(all(a < b for (a, _), (b, _) in zip(rows, rows[1:])))     # at most one a day
            self.assertEqual(len(subjects[email]), 1)
        self.assertEqual(sent["a@x.com"][:4], [(0, 1), (1, 2), (4, 3), (5, 4)])     # Thu, Fri, then Mon, Tue (weekend skipped)
        self.assertEqual(self.con.execute("select status from leads where email='a@x.com'").fetchone()[0], "completed")
        from sdr import templates
        lead = self.con.execute("select * from leads where email='a@x.com'").fetchone()
        self.assertEqual([templates.framework_name(s) for s in range(2, 12)], ["Problem", "Insight", "Proof", "Solution", "Next step"] * 2)
        self.assertEqual(templates.render(7, lead)[2], templates.render(2, lead)[2])  # round 2 repeats round 1
    def test_cover_contacts(self):
        txt = "I am on leave. Please contact rebecca@macfarmmanagement.com. IT: support@netier.com.au. Eva eva@macfarmmanagement.com"
        self.assertEqual(triage.cover_contacts(txt, "eva@macfarmmanagement.com"), ["rebecca@macfarmmanagement.com"])
        self.assertTrue(triage.add_cover(self.con, "a@x.com", "cover@x.com", "on leave")); self.assertFalse(triage.add_cover(self.con, "a@x.com", "cover@x.com"))
    def test_script_and_campaign(self):
        d = engine.due(self.con)
        self.assertEqual(d[0]["campaign"], "multi_entity")
        self.assertEqual(d[0]["subject"], "Simplifying payroll and HR management for Acme")
        self.assertIn("Hi Ann,", d[0]["body"]); self.assertNotIn("google.com/url", d[0]["body"])
        self.assertEqual(d[0]["calendly_link"], "https://calendly.com/rav-singh-akalinfo/30min")
        self.assertIn("<strong>Unified Global Payroll and HRIS platform</strong>", d[0]["html_body"]); self.assertIn("a Unified Global Payroll and HRIS platform", d[0]["body"])
        self.assertIn("<p>", d[0]["html_body"]); self.assertTrue(d[0]["include_gmail_signature"])
        self.assertTrue(d[0]["body"].endswith("Thank you so much,"))
        self.assertEqual(len(d), 2)  # no-bottleneck lead is still emailed (intent never gates)
    def test_reply_stops_cadence(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc); engine.mark_sent(self.con, "a@x.com", 1, today=t0)
        triage.record_reply(self.con, 1, "a@x.com", "Re", "Sounds good, send details", "m1")
        self.assertEqual([d["email"] for d in engine.due(self.con, today=t0 + timedelta(days=4))], ["b@y.com"])
        self.assertEqual(self.con.execute("select count(*) from touches where lead_id=1").fetchone()[0], 1)
        self.assertEqual(self.con.execute("select status from leads where id=1").fetchone()[0], "replied")
    def test_suppress_blocks_followups_and_reimport(self):
        triage.suppress(self.con, "a@x.com", "on leave")
        self.assertEqual([d["email"] for d in engine.due(self.con)], ["b@y.com"])
        self.con.execute("delete from leads"); self.con.commit()
        r = importer.import_leads(self.con, self.csv)
        self.assertEqual(r["new"], 1)
    def test_left_company(self):
        self.assertEqual(triage.classify("Automatic reply", "I am no longer working at Netier"), "left_company")
    def test_new_quota_and_followups_fill_the_rest(self):
        mon = datetime(2026, 1, 5, tzinfo=timezone.utc); tue = mon + timedelta(days=1)
        d = engine.due(self.con, today=mon, cap=1, total_cap=3); self.assertEqual([x["step"] for x in d], [1])      # 1 new/day
        engine.mark_sent(self.con, d[0]["email"], 1, today=mon)
        d2 = engine.due(self.con, today=tue, cap=1, total_cap=3)
        self.assertEqual(sorted(x["step"] for x in d2), [1, 2])             # 1 new + the follow-up
        d3 = engine.due(self.con, today=tue, cap=1, total_cap=1)
        self.assertEqual([x["step"] for x in d3], [1])                       # total limit: the new quota is protected
    def test_drafts_wait_for_approval(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        engine.mark_drafted(self.con, "a@x.com", 1, ref="d1", today=t0)
        self.assertNotIn("a@x.com", [x["email"] for x in engine.due(self.con, today=t0 + timedelta(days=1))])  # no re-draft
        self.assertIsNone(self.con.execute("select started_at from leads where email='a@x.com'").fetchone()[0])
        t1 = t0 + timedelta(days=1); self.assertEqual(engine.approve(self.con, today=t1), 1)
        self.assertEqual(self.con.execute("select started_at is not null from leads where email='a@x.com'").fetchone()[0], 1)
        self.assertNotIn("a@x.com", [x["email"] for x in engine.due(self.con, today=t1 + timedelta(days=1))])
        self.assertIn("a@x.com", [x["email"] for x in engine.due(self.con, today=t1 + timedelta(days=3))])  # next business day (Mon)
    def test_quote_mode_and_subjects(self):
        import json
        from sdr import templates
        ex = json.dumps({"quote_mode": dict(hook="Where does X break?", pain="X handling", solution="fix X", outcome="less X")})
        self.con.execute("insert into leads(email,name,company,extra,status) values('q@y.com','Quin Lee','Quark',?, 'hold')", (ex,)); self.con.commit()
        self.assertNotIn("q@y.com", [x["email"] for x in engine.due(self.con)])          # held until approved
        engine.release(self.con) if False else None
        self.con.execute("update leads set status='active' where email='q@y.com'"); self.con.commit()
        lead = self.con.execute("select * from leads where email='q@y.com'").fetchone()
        for step in range(1, 8):
            _, subj, body = templates.render(step, lead)
            self.assertEqual(subj, "Simplifying payroll and HR management for Quark")
            self.assertIn("$8 per employee per month", body); self.assertNotIn("global payroll", body.lower())
        b1 = templates.render(1, lead)[2]
        self.assertIn("TankhaPay is a Unified Payroll and HRIS platform that helps bring payroll and HR data for each country onto one platform at $8 per employee per month", b1)
        self.assertIn("<strong>" + templates.PRODUCT_SG + "</strong>", templates.to_html(b1))
        self.assertIn("<strong>" + templates.QUOTE + "</strong>", templates.to_html(templates.render(3, lead)[2]))
        engine.mark_sent(self.con, "a@x.com", 1); self.assertEqual(engine.mark_legacy_subjects(self.con), 1)
        old = self.con.execute("select * from leads where email='a@x.com'").fetchone()
        self.assertEqual(templates.render(2, old)[1], templates.LEGACY_SUBJECT)           # already-emailed lead keeps its thread subject
    def test_no_weekend_sends_even_for_new_leads(self):
        sat = datetime(2026, 1, 3, tzinfo=timezone.utc); mon = datetime(2026, 1, 5, tzinfo=timezone.utc)
        self.assertEqual(engine.due(self.con, today=sat), [])
        self.assertEqual(len(engine.due(self.con, today=mon)), 2)
    def test_generic_copy_has_no_specific_pain_points(self):
        import re
        from sdr import templates
        lead = self.con.execute("select * from leads where email='a@x.com'").fetchone()
        for step in range(1, 12):
            body = templates.render(step, lead)[2].lower()
            self.assertIsNone(re.search(r"timesheet|casual|shift|roster|rework on hours|reconciliation across managers", body), (step, body))
            self.assertIn("unified platform" if step in (1, 3, 4, 6) or step else "", body) if step in (1, 3, 6) else None
        self.assertIn("automating hr workflows", templates.render(1, lead)[2].lower())
    def test_subject_override_for_intro_threads(self):
        import json
        from sdr import templates
        self.con.execute("update leads set extra=? where email='a@x.com'", (json.dumps({"subject_override": "Introduction | TankhaPay Payroll & HRIS"}),)); self.con.commit()
        lead = self.con.execute("select * from leads where email='a@x.com'").fetchone()
        self.assertTrue(all(templates.render(s, lead)[1] == "Introduction | TankhaPay Payroll & HRIS" for s in range(1, 8)))
    def test_priority_first_followup(self):
        import json
        mon = datetime(2026, 1, 5, tzinfo=timezone.utc); tue = mon + timedelta(days=1)
        engine.mark_sent(self.con, "a@x.com", 1, today=mon); engine.mark_sent(self.con, "b@y.com", 1, today=mon + timedelta(hours=5))
        self.con.execute("update leads set extra=? where email='b@y.com'", (json.dumps({"priority_first_followup": True}),)); self.con.commit()
        d = engine.due(self.con, today=tue, cap=0, total_cap=1)
        self.assertEqual([x["email"] for x in d], ["b@y.com"])          # b was emailed later but has priority
    def test_classify(self):
        self.assertEqual(triage.classify("", "please unsubscribe me"), "unsubscribe")
        self.assertEqual(triage.classify("", "Not interested, thanks"), "not_interested")
if __name__ == "__main__": unittest.main()
