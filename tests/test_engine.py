import os, tempfile, unittest
from datetime import datetime, timedelta, timezone
os.environ.update(SDR_SEND="0", CALENDLY_URL="https://calendly.com/x/y", SENDER_NAME="Rav")
from sdr import db, importer, engine, triage

class T(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp(); self.con = db.connect(f"{d}/t.db")
        open(f"{d}/l.csv", "w").write("POC Email,POC Name,Company,Buyer Signal\na@x.com,Ann Lee,Acme,hiring 50 engineers\nbad,,,\nb@y.com,Bob,Beta,\n")
        self.res = importer.import_leads(self.con, f"{d}/l.csv")
    def test_import(self):
        self.assertEqual((self.res["new"], self.res["invalid_email"]), (2, 1))
        self.assertGreater(self.con.execute("select signal_score from leads where email='a@x.com'").fetchone()[0], 0)
    def test_cadence_days_and_stop_on_reply(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc); sent = []
        for day in range(0, 12):
            sent.append(engine.tick(self.con, today=t0 + timedelta(days=day))["emails_sent"])
        # 2 leads, emails on day 1,3,5,7,9,11 => offsets 0,2,4,6,8,10
        self.assertEqual([i for i, n in enumerate(sent) if n], [0, 2, 4, 6, 8, 10])
        self.assertEqual(self.con.execute("select count(*) from touches").fetchone()[0], 12)
    def test_reply_stops_cadence(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc); engine.tick(self.con, today=t0)
        triage.record_reply(self.con, 1, "a@x.com", "Re", "Sounds good, send details", "m1")
        engine.tick(self.con, today=t0 + timedelta(days=2))
        self.assertEqual(self.con.execute("select count(*) from touches where lead_id=1").fetchone()[0], 1)
        self.assertEqual(self.con.execute("select status from leads where id=1").fetchone()[0], "replied")
    def test_classify(self):
        self.assertEqual(triage.classify("", "please unsubscribe me"), "unsubscribe")
        self.assertEqual(triage.classify("", "Not interested, thanks"), "not_interested")
if __name__ == "__main__": unittest.main()
