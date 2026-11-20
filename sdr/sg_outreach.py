"""Singapore HR/payroll outreach list: hand-written hooks per company (from the file's notes column).
Leads are loaded on HOLD and only released after the user approves."""
import json, re
from . import triage

H = {  # company -> (hook question, pain, solution clause after 'helps', outcome)
 "Worldwide Hotels Singapore": ("Do timesheets, overtime and allowances from your properties reach one approved payroll file before cut-off?",
    "timesheet, overtime and allowance consolidation across properties", "bring timesheets, overtime and allowances from every property into one approved payroll file", "a clean payroll file before cut-off"),
 "Fullerton Health Singapore": ("When coverage changes, which entity-level payroll inputs still need manual reconciliation?",
    "entity-level payroll reconciliation when coverage changes", "capture entity-level inputs with documented approvals so coverage changes reach payroll cleanly", "less handover risk"),
 "First Fun": ("Where do new-hire, leave and employee changes still need manual re-entry before the payroll cut-off?",
    "manual re-entry of new-hire, leave and employee changes", "feed new-hire, leave and employee changes straight into payroll with no re-entry", "fewer errors at cut-off"),
 "Amplify Health": ("Where do country payroll vendors still need adjustments outside Workday, and would one approved exception workflow help?",
    "payroll adjustments outside Workday", "run country payroll exceptions through one approved workflow", "fewer off-system adjustments"),
 "Zerra DC": ("As new APAC sites open, how will you standardise employee records and payroll ownership?",
    "standardising employee records and payroll ownership across new APAC sites", "give every new site one employee record and one payroll process from day one", "consistent records as you scale"),
 "Nimbus": ("How do site shifts, relief cover and overtime reach payroll before cut-off?",
    "getting site shifts, relief cover and overtime into payroll", "capture shifts, relief cover and overtime from supervisors and feed them into payroll with approvals", "on-time, accurate pay"),
 "Eastern General Hospital": ("As the hospital builds capacity, how will employee data, rosters and approvals feed into payroll?",
    "feeding employee data, rosters and approvals into payroll as capacity grows", "connect employee master data, rosters and approvals directly to payroll", "payroll that scales with headcount"),
 "CHAGEE": ("Do new stores apply consistent rules for transfers, time approvals and pay adjustments before payroll closes?",
    "consistent transfer, time-approval and pay-adjustment rules across stores", "apply one set of rules for transfers, time approvals and pay adjustments across every store", "consistency as stores open"),
 "IPOS International": ("Which HR-to-payroll handoffs is your digitalisation work prioritising?",
    "HR-to-payroll handoffs", "connect HR records and approvals directly to payroll, removing manual handoffs", "fewer manual handoffs"),
 "AGD": ("Is payroll testing, controls or exception reporting in scope, and how do vendors engage through public procurement?",
    "payroll controls and exception reporting", "provide approval workflows and exception reporting on payroll", "stronger payroll controls"),
 "CSC Singapore": ("Where do local payroll teams still reconcile exceptions across countries during consolidation? I would also like to explore a delivery partnership.",
    "reconciling payroll exceptions across countries", "bring payroll and HR data for each country onto one platform", "faster consolidation"),
 "Xemplo": ("Could additional implementation or overflow capacity help you onboard Singapore payroll clients?",
    "onboarding Singapore payroll clients", "add implementation and overflow capacity for Singapore payroll onboarding", "faster client onboarding"),
 "Tardis": ("If a client is hiring for a payroll role, would Tardis introduce a payroll implementation or interim support partner?",
    "payroll implementation and interim support", "act as an implementation and interim support partner", "faster delivery for your clients"),
 "Frazer Jones": ("On payroll transformation mandates, could you introduce the hiring employer or a delivery partner?",
    "payroll transformation mandates", "partner on payroll transformation mandates with a platform and a delivery team", "a ready delivery option for your clients"),
 "Ascentium Singapore": ("Does client volume ever create temporary capacity pressure for parallel runs or onboarding? I would like to explore a delivery partnership.",
    "capacity pressure during parallel runs and onboarding", "add delivery capacity for parallel runs and onboarding", "less capacity pressure"),
}
PARTNER_TYPE = {"CSC Singapore", "Xemplo", "Tardis", "Frazer Jones", "Ascentium Singapore"}

def load(con, path, status="hold"):
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows = [r for r in ws.iter_rows(values_only=True) if any(v is not None for v in r)][1:]
    added, dup, skipped = [], [], []
    for r in rows:
        poc, company, email = (str(r[0] or "")), str(r[1] or "").strip(), str(r[2] or "").strip()
        email = re.sub(r"\s*\(.*?\)\s*", "", email).strip().lower()                    # "x@y (InCorp domain)" -> "x@y"
        name, _, title = poc.partition("·"); name, title = name.strip(), title.strip()
        company = "Xemplo" if company.startswith("Xemplo") else company
        if company not in H or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email): skipped.append((email, company)); continue
        if con.execute("select 1 from suppressed where email=?", (email,)).fetchone(): skipped.append((email, "suppressed")); continue
        if con.execute("select 1 from leads where email=?", (email,)).fetchone(): dup.append(email); continue
        hook, pain, sol, out = H[company]
        extra = json.dumps({"quote_mode": dict(hook=hook, pain=pain, solution=sol, outcome=out), "source": "Singapore outreach",
                            "partner_type": company in PARTNER_TYPE})
        con.execute("insert into leads(email,name,company,title,signal,signal_score,extra,status) values(?,?,?,?,?,0,?,?)",
                    (email, name, company, title, pain, extra, status)); added.append(email)
    con.commit(); return dict(rows=len(rows), added=len(added), duplicates_in_file_or_db=len(dup), skipped=skipped)
