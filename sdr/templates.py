"""Step 1 is the user's script. Steps 2+ follow the 5-part framework and then loop back to Problem:
2 Problem, 3 Insight, 4 Proof, 5 Solution, 6 Next step, 7 Problem again, ...
Claims come only from the TankhaPay deck/site (26+ years, 1,000+ businesses, ISO/IEC 27001, 100+ HR tasks, 50+ integrations)."""
from . import config, campaigns

LEGACY_SUBJECT = "Simplifying payroll and HR management across multiple entities"   # leads already emailed under it keep it (same thread)
QUOTE = "Payroll and HRIS together is $8 per employee per month."
PRODUCT_SG = "TankhaPay is a Unified Payroll and HRIS platform that helps bring payroll and HR data for each country onto one platform at $8 per employee per month."                # quoted in every email to quote-mode leads

def subject_for(lead, extra):
    if extra.get("subject_override"): return extra["subject_override"]
    return LEGACY_SUBJECT if extra.get("legacy_subject") else f"Simplifying payroll and HR management for {lead['company'] or 'your team'}"

FRAMEWORK = ("Problem", "Insight", "Proof", "Solution", "Next step")
OPTOUT = "If this isn’t relevant, just reply ‘stop’ and I won’t contact you again."

def framework_name(step):
    return None if step < 2 else FRAMEWORK[(step - 2) % len(FRAMEWORK)]

def _extra(lead):
    import json
    try: return json.loads(lead["extra"] or "{}")
    except Exception: return {}

def render_quote(step, lead, extra):
    """Short, to-the-point emails for the Singapore list: says 'payroll' (not 'global payroll') and quotes $8 pepm every time."""
    o = extra["quote_mode"]; first = (lead["name"] or "").split(" ")[0] or "there"; company = lead["company"] or "your team"
    hi = f"Hi {first},"; subj = subject_for(lead, extra)
    if step == 1:
        mid = (f"{o['hook']} {PRODUCT_SG}\n\n"
               "Would a 30-minute walkthrough make sense? Book through the Calendly link in my signature, or reply with a time that suits you and I will arrange it.")
        return "sg_quote", subj, f"{hi}\n\n{mid}\n\n{OPTOUT}\n\nThank you so much,"
    part = framework_name(step)
    partner = bool(extra.get("partner_type"))
    if part == "Problem":
        mid = (f"Following up on my note. {o['hook']} {QUOTE}" if partner else
               f"Following up on my note. {o['hook']} That is usually where payroll time and errors creep in. {QUOTE}")
    elif part == "Insight":
        mid = ((f"One pattern in payroll delivery: delays rarely come from the people. They come from data held in separate places and the manual handoffs between teams. "
                f"One platform for payroll and HRIS removes those handoffs. {QUOTE}") if partner else
               (f"One pattern with {o['pain']}: it is rarely a people problem. The data sits in separate places, so each handoff adds a manual step. "
                f"One platform for payroll and HRIS removes those handoffs. {QUOTE}"))
    elif part == "Proof": mid = ("TankhaPay comes from Akal Information Systems: 26+ years in HR, payroll and compliance, 1,000+ businesses served, "
                                  f"ISO/IEC 27001 certified, with links to SAP, Oracle and 50+ systems. {QUOTE}")
    elif part == "Solution": mid = f"For {company}, TankhaPay would {o['solution']}, giving {o['outcome']}. {QUOTE}"
    else: mid = (f"A 30-minute walkthrough on {o['pain']} would show exactly how it works for {company}. "
                 f"Book through the Calendly link in my signature, or reply with a time and I will arrange it. {QUOTE}")
    return "sg_quote", subj, f"{hi}\n\n{mid}\n\n{OPTOUT}\n\nThank you,"

def render(step, lead):
    """Main campaign copy (from 26 Nov): generic HR-automation message, no specific pain points such as timesheets or shifts.
    The Singapore quote-mode leads keep their own bespoke hooks."""
    extra = _extra(lead)
    if extra.get("quote_mode"): return render_quote(step, lead, extra)
    key, _ = campaigns.build(lead["signal"])          # kept only so reports can group leads
    first = extra.get("greeting_name") or ("there" if "shared inbox" in (lead["title"] or "").lower() else ((lead["name"] or "").split(" ")[0] or "there"))
    company = lead["company"] or "your team"; hi = f"Hi {first},"; subj = subject_for(lead, extra)
    if step == 1:
        body = (f"{hi}\n\nIs managing employee operations and payroll across separate tools and spreadsheets slowing your HR team down? "
                "Automating HR workflows can ease out the hassles of employee management and payroll, and all of it can run from one centralized, unified platform. "
                "TankhaPay is a Unified Global Payroll and HRIS platform that brings onboarding, employee records, attendance, leave, approvals and payroll together, "
                "helping HR and finance teams save time, reduce errors and stay compliant as the business grows.\n\n"
                "You can book a meeting through the Calendly link in my signature, or share a suitable time and I’ll arrange it, and I will be happy to walk you through it!\n\n"
                f"{OPTOUT}\n\nThank you so much,")
        return key, subj, body
    part = framework_name(step)
    if part == "Problem":
        mid = ("Circling back on my earlier note. When employee management and payroll run on separate tools and manual steps, HR teams usually feel it as more admin, "
               f"more errors and more time spent chasing approvals. Is that something {company} is dealing with right now?")
    elif part == "Insight":
        mid = ("One pattern I see: the hassle is rarely the people. It is the manual handoffs between separate tools. Automating HR workflows and running them from one "
               "centralized, unified platform removes those handoffs, and payroll stays in step with the employee record.")
    elif part == "Proof":
        mid = ("TankhaPay comes from Akal Information Systems, with 26+ years of technology and HR experience and 1,000+ clients, including DLF, Bank of Baroda, Wipro, "
               "Tata 1mg and Hitachi India. It is ISO/IEC 27001 certified and connects to SAP, Oracle and 50+ other systems.")
    elif part == "Solution":
        mid = (f"For {company}, TankhaPay would automate your HR workflows, from onboarding, attendance and leave to approvals and payroll, on one centralized platform, "
               "so your team spends less time on admin and has one reliable view of the workforce.")
    else:
        mid = ("A simple next step: a 30-minute walkthrough of how HR workflows and payroll run from one unified platform. Pick a time through the Calendly link in my "
               "signature, or reply with a time that suits you and I will arrange it.")
    return key, subj, f"{hi}\n\n{mid}\n\n{OPTOUT}\n\nThank you,"

def to_html(body):
    """Plain-text body -> HTML paragraphs. Gmail appends the user's signature (logo + exact Calendly link)."""
    import html
    out = "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in body.split("\n\n"))
    out = out.replace(PRODUCT_SG, f"<strong>{PRODUCT_SG}</strong>").replace(QUOTE, f"<strong>{QUOTE}</strong>")   # Singapore list: product sentence and quote in bold
    if PRODUCT_SG not in body:
        for phrase in ("Unified Global Payroll and HRIS platform", "Unified Payroll and HRIS platform"):
            out = out.replace(phrase, f"<strong>{phrase}</strong>")
    return out
