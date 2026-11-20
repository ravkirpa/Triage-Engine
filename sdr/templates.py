"""Step 1 is the user's script. Steps 2+ follow the 5-part framework and then loop back to Problem:
2 Problem, 3 Insight, 4 Proof, 5 Solution, 6 Next step, 7 Problem again, ...
Claims come only from the TankhaPay deck/site (26+ years, 1,000+ businesses, ISO/IEC 27001, 100+ HR tasks, 50+ integrations)."""
from . import config, campaigns

FIXED_SUBJECT = "Simplifying payroll and HR management across multiple entities"   # fixed by the user for every email
FRAMEWORK = ("Problem", "Insight", "Proof", "Solution", "Next step")
OPTOUT = "If this isn’t relevant, just reply ‘stop’ and I won’t contact you again."

def framework_name(step):
    return None if step < 2 else FRAMEWORK[(step - 2) % len(FRAMEWORK)]

def render(step, lead):
    key, c = campaigns.build(lead["signal"])
    first = "there" if "shared inbox" in (lead["title"] or "").lower() else ((lead["name"] or "").split(" ")[0] or "there")
    company = lead["company"] or "your team"
    hi = f"Hi {first},"
    if step == 1:
        body = (f"{hi}\n\nIs {c['pain']} causing {c['impact']}? TankhaPay is a Unified Global Payroll and HRIS platform that helps {c['solution']}, "
                f"delivering {c['value']} and improving ROI through reduced {c['roi']}.\n\n"
                "You can book a meeting through the Calendly link in my signature, or share a suitable time and I’ll arrange it, and I will be happy to walk you through it!\n\n"
                f"{OPTOUT}\n\nThank you so much,")
        return key, FIXED_SUBJECT, body
    part = framework_name(step)
    if part == "Problem":
        mid = (f"Circling back on my earlier note. Teams dealing with {c['pain']} usually feel it as {c['impact']}. "
               f"Is that something {company} is running into right now?")
    elif part == "Insight":
        mid = (f"One pattern I see with {c['pain']}: it is rarely a people problem. It usually happens because the data sits in separate places, "
               "so every handoff adds a manual step and another chance for error. Bringing it onto one platform removes those handoffs.")
    elif part == "Proof":
        mid = ("TankhaPay comes from Akal Information Systems, with 26+ years of HR, payroll and compliance experience, 1,000+ businesses served and "
               "ISO/IEC 27001 certification. The platform automates 100+ HR tasks and connects to SAP, Oracle and 50+ other systems.")
    elif part == "Solution":
        mid = (f"Here is how it would work for {company}: TankhaPay would {c['solution']}, delivering {c['value']} and reducing {c['roi']}.")
    else:  # Next step
        mid = (f"A simple next step: a 30-minute walkthrough focused on {c['pain']} at {company}. "
               "Pick a time through the Calendly link in my signature, or reply with a time that suits you and I will arrange it.")
    return key, FIXED_SUBJECT, f"{hi}\n\n{mid}\n\n{OPTOUT}\n\nThank you,"

def to_html(body):
    """Plain-text body -> HTML paragraphs. Gmail appends the user's signature (logo + exact Calendly link)."""
    import html
    out = "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in body.split("\n\n"))
    return out.replace("Unified Global Payroll and HRIS platform", "<strong>Unified Global Payroll and HRIS platform</strong>")
