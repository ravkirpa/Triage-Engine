"""Step 1 is the user's script verbatim. Steps 2-6 follow the same structure and tone."""
from . import config, campaigns

def render(step, lead):
    key, c = campaigns.build(lead["signal"])
    first = (lead["name"] or "").split(" ")[0] or "there"
    company = lead["company"] or "your team"
    base = f"Simplifying {c['pain']} at {company}"
    bodies = {
     1: (base,
         f"Hi {first},\n\nIs {c['pain']} causing {c['impact']}? TankhaPay is a unified global payroll and HRIS platform that helps {c['solution']}, delivering {c['value']} and improving ROI through reduced {c['roi']}.\n\nYou can book a meeting through the Calendly link in my signature, or share a suitable time and I’ll arrange it, and I will be happy to walk you through it!\n\nThank you so much,\n"),
     2: ("Re: " + base,
         f"Hi {first},\n\nFollowing up on my note. If {c['pain']} is costing {company} time, TankhaPay can help {c['solution']}.\n\nA quick 30-minute walkthrough is easy to set up through the link in my signature, or share a time that suits you.\n"),
     3: ("Re: " + base,
         f"Hi {first},\n\nTeams that move {c['pain']} onto one platform typically see {c['value']}, with less {c['roi']}.\n\nHappy to show you how it would work for {company}. Book a slot via my signature, or tell me what suits you and I’ll arrange it.\n"),
     4: ("Re: " + base,
         f"Hi {first},\n\nIs fixing {c['pain']} a priority for {company} this quarter? If yes, a 30-minute demo will show you exactly how TankhaPay handles it. If not, just tell me and I’ll step back.\n"),
     5: ("Re: " + base,
         f"Hi {first},\n\nIf someone else owns {c['pain']} at {company}, could you point me to them? Otherwise, my calendar link in the signature is open whenever it suits you.\n"),
     6: ("Re: " + base,
         f"Hi {first},\n\nThis is my last note so I don’t clutter your inbox. If timing changes, TankhaPay can help {company} with {c['pain']}, and you can book a time through my signature whenever you’re ready.\n"),
    }
    subj, body = bodies[step]
    optout = "If this isn’t relevant, just reply ‘stop’ and I won’t contact you again."
    head, _, tail = body.rpartition("\n\n") if step == 1 else (body.rstrip("\n"), "", "")
    body = (head + "\n\n" + optout + "\n\n" + tail) if step == 1 else (head + "\n\n" + optout + "\n")
    return key, subj, body.rstrip("\n")

def to_html(body):
    """Plain-text body -> HTML paragraphs. The Gmail signature (with the exact Calendly anchor) is appended by Gmail."""
    import html
    return "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in body.split("\n\n"))
