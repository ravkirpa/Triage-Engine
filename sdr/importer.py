"""Import a lead database (CSV / JSON / XLSX / SQLite) into the agent's store."""
import csv, json, re, sqlite3
from pathlib import Path

ALIASES = {
    "email": ["email", "poc email", "poc_email", "contact email", "work email", "e-mail"],
    "name": ["name", "poc name", "contact name", "full name", "poc"],
    "company": ["company name", "company", "account", "organization", "company name"],
    "title": ["title", "designation", "role", "job title"],
    "signal": ["bottleneck", "bottlenecks", "pain point", "pain points", "pain_point", "challenge", "challenges", "problem", "bi", "insight", "business intelligence", "signal", "buyer signal", "buyer signals"],
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _norm(h): return re.sub(r"\s+", " ", str(h or "").strip().lower())

def read_rows(path):
    p = Path(path); ext = p.suffix.lower()
    if ext in (".csv", ".tsv"):
        with open(p, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f, delimiter="\t" if ext == ".tsv" else ","))
    if ext == ".json":
        d = json.loads(p.read_text()); return d if isinstance(d, list) else d.get("leads", [])
    if ext in (".xlsx", ".xlsm"):
        try: import openpyxl
        except ImportError: raise SystemExit("XLSX needs openpyxl (pip install openpyxl) or export to CSV.")
        out = []
        for ws in openpyxl.load_workbook(p, read_only=True, data_only=True):
            it = ws.iter_rows(values_only=True); hdr = [_norm(c) for c in next(it, [])]; blank = 0
            for r in it:   # sheets can report ~1M rows; stop after a run of empties
                if not any(r):
                    blank += 1
                    if blank > 20: break
                    continue
                blank = 0; out.append(dict(zip(hdr, r)))
        return out
    if ext in (".db", ".sqlite", ".sqlite3"):
        con = sqlite3.connect(p); con.row_factory = sqlite3.Row
        t = con.execute("select name from sqlite_master where type='table' order by 1").fetchone()[0]
        return [dict(r) for r in con.execute(f'select * from "{t}"')]
    raise SystemExit(f"Unsupported file type: {ext}")

WORKFORCE_IND = ("construction", "farming", "restaurants", "hospitality", "retail", "food", "agricultur", "manufactur",
                 "logistics", "staffing", "facilities", "health", "nonprofit", "civic")
ERP = ("sap", "oracle", "workday", "netsuite", "dynamics")
TOOLS = ("employment hero", "deputy", "xero", "myob", "bamboohr", "zoho", "rippling")

def infer_bottleneck(r):
    """Apollo exports carry no bottleneck column; infer the most likely one from company signals."""
    def num(k):
        try: return float(str(r.get(k) or 0).replace(",", ""))
        except ValueError: return 0
    tech = str(r.get("technologies") or "").lower(); ind = str(r.get("industry") or "").lower()
    title = str(r.get("title") or "").lower()
    cc, pc = str(r.get("company country") or "").strip().lower(), str(r.get("country") or "").strip().lower()
    if r.get("parent company (apollo data)") or num("number of retail locations") >= 3 or (cc and pc and cc != pc):
        return "payroll and HR management across multiple entities and locations", "multi-entity/locations/parent company/cross-country"
    if any(f" {e}" in f" {tech}" or f", {e}" in tech for e in ERP):
        return "disconnected HR, payroll and finance systems (ERP integration)", "uses ERP: " + next(e for e in ERP if e in tech)
    if any(k in ind for k in WORKFORCE_IND) and num("# employees") >= 50:
        return "a mix of on-roll, off-roll and contract workers to manage", f"industry={ind}, {int(num('# employees'))} employees"
    if any(t in tech for t in TOOLS):
        return "payroll accuracy and compliance across disconnected HR tools", "uses " + next(t for t in TOOLS if t in tech)
    if any(k in title for k in ("finance", "cfo", "financial")):
        return "payroll accuracy and statutory compliance", "finance buyer"
    if any(k in title for k in ("people", "hr", "human", "culture", "talent")):
        return "manual HR administration and onboarding", "HR buyer"
    return "attendance tracking and shift management", "default (operations buyer)"

def import_leads(con, path):
    rows = read_rows(path); n_new = n_upd = n_bad = 0
    for raw in rows:
        r = {_norm(k): v for k, v in raw.items()}
        full = " ".join(filter(None, (str(r.get("first name") or "").strip(), str(r.get("last name") or "").strip())))
        if r.get("email status") not in (None, "", "Verified"): n_bad += 1; continue   # skip guessed/unavailable emails
        if str(r.get("replied")).lower() == "true" or r.get("email sent"): n_bad += 1; continue
        pick = lambda f: next((str(r[a]).strip() for a in ALIASES[f] if r.get(a) not in (None, "")), "")
        email = pick("email").lower()
        if not EMAIL_RE.match(email): n_bad += 1; continue
        sig = pick("signal"); why = "from databank"
        if not sig: sig, why = infer_bottleneck(r)
        extra = json.dumps({"bottleneck_basis": why, "country": r.get("company country"), "industry": r.get("industry")}, default=str)
        vals = (pick("name") or full, pick("company"), pick("title"), sig, 0, extra)
        if con.execute("select 1 from leads where email=?", (email,)).fetchone():
            con.execute("update leads set name=coalesce(nullif(?,''),name), company=coalesce(nullif(?,''),company),"
                        "title=coalesce(nullif(?,''),title), signal=coalesce(nullif(?,''),signal), signal_score=?, extra=? where email=?",
                        (*vals, email)); n_upd += 1
        else:
            con.execute("insert into leads(name,company,title,signal,signal_score,extra,email) values(?,?,?,?,?,?,?)", (*vals, email)); n_new += 1
    con.commit()
    return {"rows": len(rows), "new": n_new, "updated": n_upd, "skipped_unverified_invalid_or_contacted": n_bad}
