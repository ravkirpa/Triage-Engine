"""Six-step cadence copy. Each step is (subject, body); {placeholders} filled per lead."""
from . import config

STEPS = {
 1: ("{company} + {pitch_short}",
     "Hi {first},\n\n{hook}\n\n{pitch}\n\nWorth a quick look? You can grab a time that suits you here: {calendly}\n"),
 2: ("Re: {company} + {pitch_short}",
     "Hi {first},\n\nFollowing up on my note. {hook_short}\n\nTeams in a similar spot usually care about one thing: speed to outcome. Happy to show how, in 20 minutes: {calendly}\n"),
 3: ("A relevant example for {company}",
     "Hi {first},\n\nA short example of what we did for a team like yours: {pitch}\n\nIf useful, pick a slot here: {calendly}\n"),
 4: ("Is this a priority for {company}?",
     "Hi {first},\n\nI don't want to clutter your inbox. Is this on your radar for the next quarter? If yes, here's my calendar: {calendly}\nIf not, tell me and I'll stop.\n"),
 5: ("Should I close the loop?",
     "Hi {first},\n\nStill keen to help {company}. If someone else owns this, a pointer would be great. Otherwise grab a time: {calendly}\n"),
 6: ("Last note from me",
     "Hi {first},\n\nI'll stop here so I'm not a nuisance. If timing changes, my calendar is always open: {calendly}\n\nAll the best.\n"),
}

def render(step, lead):
    first = (lead["name"] or "").split(" ")[0] or "there"
    company = lead["company"] or "your team"
    pitch = config.get("PRODUCT_PITCH", "we help teams like yours move faster")
    sig = (lead["signal"] or "").strip()
    hook = f"I noticed {company}: {sig}. That's usually when {pitch.split('.')[0].lower()} matters most." if sig else f"I've been following {company} and thought this could be relevant."
    ctx = dict(first=first, company=company, pitch=pitch, pitch_short=pitch[:40].rstrip(" ,."), hook=hook,
               hook_short=(f"Re: {sig}." if sig else ""), calendly=config.get("CALENDLY_URL", "<set CALENDLY_URL>"))
    subj, body = STEPS[step]
    sign = f"\n{config.get('SENDER_NAME')}\n{config.get('SENDER_TITLE')}, {config.get('SENDER_COMPANY')}\n\nReply 'stop' and I won't contact you again."
    return subj.format(**ctx), body.format(**ctx) + sign
