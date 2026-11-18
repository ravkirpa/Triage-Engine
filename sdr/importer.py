"""Import a lead database (CSV / JSON / XLSX / SQLite) into the agent's store."""
import csv, json, re, sqlite3
from pathlib import Path

ALIASES = {
    "email": ["email", "poc email", "poc_email", "contact email", "work email", "e-mail"],
    "name": ["name", "poc name", "contact name", "full name", "poc"],
    "company": ["company", "account", "organization", "company name"],
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
        ws = openpyxl.load_workbook(p, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True)); hdr = [_norm(c) for c in rows[0]]
        return [dict(zip(hdr, r)) for r in rows[1:]]
    if ext in (".db", ".sqlite", ".sqlite3"):
        con = sqlite3.connect(p); con.row_factory = sqlite3.Row
        t = con.execute("select name from sqlite_master where type='table' order by 1").fetchone()[0]
        return [dict(r) for r in con.execute(f'select * from "{t}"')]
    raise SystemExit(f"Unsupported file type: {ext}")

def import_leads(con, path):
    rows = read_rows(path); n_new = n_upd = n_bad = 0
    for raw in rows:
        r = {_norm(k): v for k, v in raw.items()}
        pick = lambda f: next((str(r[a]).strip() for a in ALIASES[f] if r.get(a) not in (None, "")), "")
        email = pick("email").lower()
        if not EMAIL_RE.match(email): n_bad += 1; continue
        known = set(a for v in ALIASES.values() for a in v)
        extra = json.dumps({k: v for k, v in r.items() if k not in known and v not in (None, "")}, default=str)
        sig = pick("signal"); vals = (pick("name"), pick("company"), pick("title"), sig, 0, extra)
        if con.execute("select 1 from leads where email=?", (email,)).fetchone():
            con.execute("update leads set name=coalesce(nullif(?,''),name), company=coalesce(nullif(?,''),company),"
                        "title=coalesce(nullif(?,''),title), signal=coalesce(nullif(?,''),signal), signal_score=?, extra=? where email=?",
                        (*vals, email)); n_upd += 1
        else:
            con.execute("insert into leads(name,company,title,signal,signal_score,extra,email) values(?,?,?,?,?,?,?)", (*vals, email)); n_new += 1
    con.commit()
    return {"rows": len(rows), "new": n_new, "updated": n_upd, "invalid_email": n_bad}
