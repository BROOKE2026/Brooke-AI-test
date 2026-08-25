"""
Portal navigation map and how-to knowledge.

This is NOT client data. It describes the portal itself: which tabs exist, which
forms live where, and the steps for common tasks.

Every how-to carries an `open` block. The server turns that into a real button in
the chat, so the model never writes a URL and therefore cannot invent one that
goes nowhere. The model supplies the words, this file supplies the destination.
"""

TABS = {
    "overview":  "Overview",
    "accounts":  "Accounts",
    "documents": "Documents",
    "tax":       "Tax",
    "meetings":  "Meetings",
    "forms":     "Forms",
}

FORMS = {
    "beneficiary": {
        "name": "Beneficiary Designation",
        "why":  "Names who inherits an account. Overrides your will for that account.",
        "turnaround": "2 business days",
    },
    "address_change": {
        "name": "Address Change",
        "why":  "Updates your mailing address across all accounts and tax documents.",
        "turnaround": "Same day",
    },
    "contribution": {
        "name": "Contribution Request",
        "why":  "Moves money into an IRA or brokerage account.",
        "turnaround": "1 to 3 business days",
    },
    "withdrawal": {
        "name": "Withdrawal Request",
        "why":  "Moves money out to a linked bank account.",
        "turnaround": "3 to 5 business days",
    },
    "direct_deposit": {
        "name": "Bank Link and Direct Deposit",
        "why":  "Connects a checking account for transfers in and out.",
        "turnaround": "2 business days after micro-deposit verification",
    },
    "trusted_contact": {
        "name": "Trusted Contact",
        "why":  "Someone the firm may reach if we cannot reach you. They cannot trade or withdraw.",
        "turnaround": "Same day",
    },
}

# topic -> steps + where it lives
HOWTOS = {
    "beneficiary": {
        "title": "Update a beneficiary designation",
        "steps": [
            "Open the Forms tab.",
            "Choose Beneficiary Designation.",
            "Pick the account you want to change. Each account has its own beneficiaries.",
            "Enter each beneficiary's full legal name, date of birth, and percentage share.",
            "Make the percentages add up to 100 for primary beneficiaries, and 100 again for contingent beneficiaries if you name any.",
            "Sign electronically and submit.",
        ],
        "note": "Processed in about 2 business days. You will get an email confirmation when it takes effect.",
        "open": {"tab": "forms", "item": "beneficiary", "label": "Open Beneficiary Designation"},
    },
    "address_change": {
        "title": "Change your mailing address",
        "steps": [
            "Open the Forms tab.",
            "Choose Address Change.",
            "Enter the new address. Use the legal residential address, not a PO box, if this is your primary residence.",
            "Tick whether it applies to all accounts or only some.",
            "Sign electronically and submit.",
        ],
        "note": "Applies same day. Tax documents for the current year will use the new address.",
        "open": {"tab": "forms", "item": "address_change", "label": "Open Address Change"},
    },
    "contribution": {
        "title": "Make a contribution",
        "steps": [
            "Open the Forms tab.",
            "Choose Contribution Request.",
            "Select the receiving account.",
            "Enter the amount and, for an IRA, the tax year you want it applied to.",
            "Choose the funding source from your linked bank accounts.",
            "Sign electronically and submit.",
        ],
        "note": "Takes 1 to 3 business days. Check your remaining room first, ask me and I can look it up.",
        "open": {"tab": "forms", "item": "contribution", "label": "Open Contribution Request"},
    },
    "withdrawal": {
        "title": "Request a withdrawal",
        "steps": [
            "Open the Forms tab.",
            "Choose Withdrawal Request.",
            "Select the account and enter the amount.",
            "Choose the destination bank account.",
            "For a retirement account, choose your federal and state withholding.",
            "Sign electronically and submit.",
        ],
        "note": "Takes 3 to 5 business days. Retirement withdrawals may be taxable, and your advisor should look at anything large before you submit it.",
        "open": {"tab": "forms", "item": "withdrawal", "label": "Open Withdrawal Request"},
    },
    "direct_deposit": {
        "title": "Link a bank account",
        "steps": [
            "Open the Forms tab.",
            "Choose Bank Link and Direct Deposit.",
            "Enter the routing and account numbers, or sign in to your bank to link it instantly.",
            "If you entered the numbers manually, we send two small deposits. Come back in 1 to 2 days and enter those amounts to verify.",
        ],
        "note": "Once verified the account is available for both contributions and withdrawals.",
        "open": {"tab": "forms", "item": "direct_deposit", "label": "Open Bank Link"},
    },
    "trusted_contact": {
        "title": "Add a trusted contact",
        "steps": [
            "Open the Forms tab.",
            "Choose Trusted Contact.",
            "Enter their name, relationship, phone, and email.",
            "Sign electronically and submit.",
        ],
        "note": "A trusted contact can never trade, withdraw, or see your balances. We only contact them if we cannot reach you or we are worried about your wellbeing.",
        "open": {"tab": "forms", "item": "trusted_contact", "label": "Open Trusted Contact"},
    },
    "download_statement": {
        "title": "Download a statement",
        "steps": [
            "Open the Documents tab.",
            "Find the statement you want. They are listed newest first.",
            "Click the download icon on the right of the row.",
        ],
        "note": "Statements are posted about 5 business days after each quarter ends.",
        "open": {"tab": "documents", "label": "Open Documents"},
    },
    "tax_documents": {
        "title": "Find your tax documents",
        "steps": [
            "Open the Tax tab to see filed returns and the figures from them.",
            "For the source forms themselves, such as a 1099-DIV, open the Documents tab and look under Tax Document.",
        ],
        "note": "1099s are posted by mid February. Corrected 1099s, if any, arrive by mid March.",
        "open": {"tab": "tax", "label": "Open Tax"},
    },
    "schedule_meeting": {
        "title": "Schedule a meeting with your advisor",
        "steps": [
            "Open the Meetings tab.",
            "Click Request a meeting.",
            "Choose a meeting type and give a couple of times that work for you.",
            "Submit, and your advisor's office confirms within one business day.",
        ],
        "note": "If it is urgent, say so in the notes and someone will call you instead.",
        "open": {"tab": "meetings", "label": "Open Meetings"},
    },
}


# ---------------------------------------------------------------------------
# Deterministic how-to routing.
#
# Asking the model to "remember to call get_howto" is not reliable: in testing it
# sometimes skipped the tool and invented portal steps that did not exist. Since
# a wrong instruction about a financial form is worse than no answer, how-to
# intent is detected in code and the tool result is pre-loaded before the model
# ever runs. The model then only narrates steps it has actually been given.
# ---------------------------------------------------------------------------

import re

_HOWTO_INTENT = re.compile(
    r"\b(how (do|would|can|to)|where (do|is|can)|what.{0,12}steps|walk me through|"
    r"help me (with|fill|update|change|set ?up|add|link|download|request|schedule)|"
    r"can you (help|show|walk).{0,24}(fill|update|change|find|add|set|link|download|request|schedule|get)|"
    r"i (want|need) to (change|update|add|set ?up|make|request|link|download|schedule|move|take out|put))\b",
    re.I,
)

KEYWORDS = {
    "beneficiary":        ["beneficiar", "inherit", "who gets", "passes away", "pass away", "if i die",
                           "if something happens", "after my death", "estate"],
    "address_change":     ["address", "moved", "moving", "new house", "relocat", "mailing"],
    "contribution":       ["contribut", "put money in", "add money", "fund my", "deposit", "top up",
                           "invest more", "more money in"],
    "withdrawal":         ["withdraw", "take money out", "cash out", "distribution", "pull money", "take out"],
    "direct_deposit":     ["bank account", "link my bank", "direct deposit", "routing", "checking account", "ach"],
    "trusted_contact":    ["trusted contact", "emergency contact"],
    "download_statement": ["statement", "download"],
    "tax_documents":      ["1099", "tax document", "tax form", "w-2", "w2", "tax paperwork"],
    "schedule_meeting":   ["schedule", "book a", "meet with", "appointment", "set up a meeting", "see my advisor"],
}


def match_howto(text):
    """Return a HOWTOS topic if this clearly reads as a how-to question, else None."""
    if not text or not _HOWTO_INTENT.search(text):
        return None
    low = text.lower()
    best, score = None, 0
    for topic, words in KEYWORDS.items():
        hits = sum(1 for w in words if w in low)
        if hits > score:
            best, score = topic, hits
    return best if score else None


# ---------------------------------------------------------------------------
# Fast path for plain data lookups.
#
# Normally a data question costs two model calls: one where the model decides
# which tool to use, and one where it writes the answer. When the question is
# unambiguous we can pick the tool in code and skip the first call entirely,
# which roughly halves time to answer. Deliberately conservative: anything that
# is not a clear match falls through to the model, which still has every tool.
# ---------------------------------------------------------------------------

_YEAR = re.compile(r"\b(19|20)\d{2}\b")

_WORDNUM = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}


def _parse_year_window(low):
    """'past three years' -> 3; 'last year' -> 1; 'this year'/'ytd' -> 0 (YTD only)."""
    m = re.search(r"\b(?:past|last)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b", low)
    if m:
        tok = m.group(1)
        return int(tok) if tok.isdigit() else _WORDNUM[tok]
    if re.search(r"\b(this year|ytd|year to date|so far this year)\b", low):
        return 0
    if re.search(r"\blast year\b", low):
        return 1
    return 3


_DATA_PATTERNS = [
    ("get_performance",       [r"(?<!tax )\breturns?\b", r"\bperformance\b",
                               r"\bhow (did|have) my (accounts?|portfolio|investments?|money) (do|done|perform|grown?)",
                               r"\bhow much.{0,24}\b(grown|growth|made|earned)\b"]),
    ("get_allocation",        [r"\ballocation\b", r"\basset mix\b",
                               r"\bhow.{0,26}\b(invested|split|divided|spread)\b",
                               r"\bstocks?\s+(vs\.?|versus|and)\s+bonds?\b"]),
    ("get_accounts",          [r"\b(account )?balance", r"\bhow much (do i have|is in)",
                               r"\bmy accounts\b", r"\btotal (value|balance)", r"\bnet worth\b",
                               r"\bwhat.{0,12}\bi have\b.{0,16}\b(invested|accounts?)\b"]),
    ("get_tax_return",        [r"\bagi\b", r"\badjusted gross\b", r"\btax return\b",
                               r"\bwhat did i (pay|owe) in tax", r"\beffective (tax )?rate\b",
                               r"\bfiling status\b"]),
    ("get_documents",         [r"\bwhat documents\b", r"\bmy documents\b", r"\bdocuments (do i|on file)",
                               r"\bwhat.{0,14}(statements?|paperwork)\b.{0,14}\b(have|file)"]),
    ("get_meetings",          [r"\bnext meeting\b", r"\bmy meetings?\b", r"\bwhen.{0,20}\bmeeting\b",
                               r"\bupcoming (meeting|appointment)"]),
    ("get_fees",              [r"\bmy fees?\b", r"\badvisory fees?\b", r"\bwhat.{0,12}\bfee",
                               r"\bhow much.{0,20}\b(charge|fee)"]),
    ("get_beneficiaries",     [r"\bbeneficiar", r"\bwho (gets|inherits)\b"]),
    ("get_contribution_room", [r"\bcontribution room\b", r"\bhow much (more )?can i (contribute|put)",
                               r"\bhow much.{0,20}\broom\b", r"\bmaxed out\b"]),
]


def match_data_query(text, this_year):
    """Return (tool_name, args) for an unambiguous lookup, else None."""
    if not text:
        return None
    low = text.lower()

    # Never fast-path something that is really a how-to or an advice question.
    if _HOWTO_INTENT.search(text):
        return None
    if re.search(r"\b(should i|do you (think|recommend)|would you|is it (a )?good|"
                 r"what do you think|advise|advice|better off)\b", low):
        return None

    for tool, pats in _DATA_PATTERNS:
        if not any(re.search(p, low) for p in pats):
            continue
        if tool == "get_performance":
            # "tax return" must never land here
            if re.search(r"\btax\b", low):
                continue
            n = _parse_year_window(low)
            # n==0 means "this year": YTD is always included in the result,
            # so fetch the smallest window and let the answer lead with YTD.
            return tool, {"years": n or 1}
        if tool == "get_tax_return":
            m = _YEAR.search(text)
            if m:
                year = int(m.group(0))
            elif "last year" in low or "previous year" in low:
                year = this_year - 1
            elif "this year" in low or "current year" in low:
                year = this_year
            else:
                year = this_year - 1      # a filed return means the prior year
            return tool, {"year": year}
        if tool == "get_contribution_room":
            m = _YEAR.search(text)
            return tool, {"year": int(m.group(0)) if m else this_year}
        return tool, {}
    return None


# ---------------------------------------------------------------------------
# Third-party guard.
#
# Asked "what is <other client>'s tax return", the model looked up the SESSION
# client's data (correctly, the server gave it nothing else) and then narrated it
# under the name from the question. No data crossed, but the client is told it
# did. Refuse these in code before any lookup happens.
# ---------------------------------------------------------------------------

_POSSESSIVE = re.compile(r"\b([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){0,2})'s\b")
_ABOUT = re.compile(
    r"\b(?:about|for|does|is|has|of)\s+([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,2})\b")


def third_party_name(text, client_name):
    """A person named in the question who is not the signed-in client, else None."""
    if not text or not client_name:
        return None
    own = {p.lower() for p in client_name.split()}
    own |= {"i", "me", "my", "mine", "we", "our", "us"}
    for rx in (_POSSESSIVE, _ABOUT):
        for m in rx.finditer(text):
            cand = m.group(1).strip()
            parts = [p.lower() for p in cand.split()]
            if any(p in own for p in parts):
                continue
            # ignore the firm, the advisor, and obvious non-people
            if cand.lower() in {"brookhaven", "brooke", "jacob", "jacob chandler",
                                "roth", "traditional", "the", "form", "forms"}:
                continue
            return cand
    return None


_NAV_INTENT = re.compile(
    r"\b(take me to|go to|open (the |my )?|show me (the |my )?|bring me to|navigate to|jump to)\b", re.I)

_TAB_WORDS = {
    "forms":     ["form", "forms", "paperwork"],
    "documents": ["document", "documents", "statement", "statements", "files"],
    "tax":       ["tax", "taxes", "return", "returns"],
    "meetings":  ["meeting", "meetings", "calendar", "appointment"],
    "accounts":  ["account", "accounts", "holdings", "portfolio", "balances"],
    "overview":  ["overview", "dashboard", "home", "summary"],
}


def match_navigation(text):
    """Return a tab when the client is plainly asking to be taken somewhere."""
    if not text or not _NAV_INTENT.search(text):
        return None
    low = text.lower()
    for tab, words in _TAB_WORDS.items():
        if any(re.search(r"\b%s\b" % w, low) for w in words):
            return tab
    return None


# ---------------------------------------------------------------------------
# Advice intent and large amounts.
#
# "How am I doing?" and "Is my cash allocation normal?" are evaluative, which at
# an RIA is advice. They also exposed a separate failure: the model replied "let
# me check your balances" and then called nothing, dead-ending the conversation.
# Routing them to a human fixes both.
# ---------------------------------------------------------------------------

_ADVICE = re.compile(
    r"\b(how am i doing|am i (on track|doing (ok|okay|well|alright|fine))|"
    r"should i\b|do you (think|recommend|suggest)|would you (recommend|suggest)|"
    r"what do you think|is it (a )?good (idea|time)|am i (over|under)\s?\w*|"
    r"is (my|the|this|that)\b[^?]{0,40}\b(normal|ok|okay|good|bad|right|reasonable|"
    r"healthy|aggressive|conservative|too (high|low|much|little|risky))|"
    r"too (much|little) (cash|risk|bonds|stock)|better off|worth it|"
    r"\bdiversified\b|\brebalanc)", re.I)

_MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(k\b|thousand|m\b|million)?"
                    r"|\b([\d,]+(?:\.\d+)?)\s*(k\b|thousand|m\b|million)\b", re.I)

LARGE_AMOUNT = 25_000


def advice_intent(text):
    return bool(text and _ADVICE.search(text))


def large_amount(text):
    """Return a dollar figure at or above LARGE_AMOUNT mentioned in the text."""
    if not text:
        return None
    for m in _MONEY.finditer(text):
        raw = m.group(1) or m.group(3)
        unit = (m.group(2) or m.group(4) or "").lower()
        try:
            val = float(raw.replace(",", ""))
        except (ValueError, AttributeError):
            continue
        if unit.startswith("k") or unit.startswith("thousand"):
            val *= 1_000
        elif unit.startswith("m"):
            val *= 1_000_000
        if val >= LARGE_AMOUNT:
            return val
    return None


# ---------------------------------------------------------------------------
# Tax planning and strategy topics. These are advice regardless of phrasing,
# and the right move is a call with the tax team, offered immediately.
# ---------------------------------------------------------------------------

_TAX_TOPICS = re.compile(
    r"\broth conversion\b|\bbackdoor\b|\btax[- ]loss\b|\bharvest(?:ing)?\b|"
    r"\bdeduct(?:ion|ions|ible)?\b|\bwrite[- ]?offs?\b|"
    r"\bestimated (?:tax )?payments?\b|\bquarterly (?:taxes|payments)\b|"
    r"\btax (?:plan|planning|strategy|strategies|projection|bill|situation)\b|"
    r"\b(?:lower|reduce|cut|minimi[sz]e)\b.{0,16}\btax(?:es)?\b|"
    r"\brmds?\b|\brequired minimum\b|\bcapital gains (?:tax|strategy)\b|"
    r"\b1031\b|\bcharitable\b.{0,24}\btax\b|\btax\b.{0,24}\bcharitable\b",
    re.I,
)


def tax_topic(text):
    return bool(text and _TAX_TOPICS.search(text))
