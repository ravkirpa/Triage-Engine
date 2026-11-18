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
    def test_cadence_days(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc); days = []
        for day in range(12):
            for d in engine.due(self.con, today=t0 + timedelta(days=day)):
                engine.mark_sent(self.con, d["email"], d["step"], today=t0 + timedelta(days=day)); days.append(day)
        self.assertEqual(sorted(set(days)), [0, 2, 4, 6, 8, 10])
        self.assertEqual(self.con.execute("select count(*) from touches").fetchone()[0], 12)
    def test_script_and_campaign(self):
        d = engine.due(self.con)
        self.assertEqual(d[0]["campaign"], "multi_entity")
        self.assertTrue(d[0]["subject"].startswith("Simplifying "))
        self.assertIn("Hi Ann,", d[0]["body"]); self.assertNotIn("google.com/url", d[0]["body"])
        self.assertEqual(d[0]["calendly_link"], "https://calendly.com/rav-singh-akalinfo/30min")
        self.assertIn("<strong>Unified Global Payroll and HRIS platform</strong>", d[0]["html_body"]); self.assertIn("a Unified Global Payroll and HRIS platform", d[0]["body"])
        self.assertIn("<p>", d[0]["html_body"]); self.assertTrue(d[0]["include_gmail_signature"])
        self.assertTrue(d[0]["body"].endswith("Thank you so much,"))
        self.assertEqual(len(d), 2)  # no-bottleneck lead is still emailed (intent never gates)
    def test_reply_stops_cadence(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc); engine.mark_sent(self.con, "a@x.com", 1, today=t0)
        triage.record_reply(self.con, 1, "a@x.com", "Re", "Sounds good, send details", "m1")
        self.assertEqual([d["email"] for d in engine.due(self.con, today=t0 + timedelta(days=2))], ["b@y.com"])
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
    def test_classify(self):
        self.assertEqual(triage.classify("", "please unsubscribe me"), "unsubscribe")
        self.assertEqual(triage.classify("", "Not interested, thanks"), "not_interested")
if __name__ == "__main__": unittest.main()
