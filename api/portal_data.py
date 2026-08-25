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
