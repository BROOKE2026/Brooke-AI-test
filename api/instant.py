"""
Server-written answers for canonical questions.

When the router has already identified the question AND the answer is pure
data, having a model retype the numbers adds seconds and a rounding risk but
no value. These templates produce the final sentence directly. Anything not
covered returns None and falls through to normal model narration.

Because no model is involved, these answers are also fully concurrent: any
number of clients can ask them at the same moment, even while the model is
busy on someone's hard question.
"""

from datetime import datetime


def _money(v):
    return "${:,.0f}".format(v)


def _money2(v):
    return "${:,.2f}".format(v)


def _day(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return iso


def render(name, args, result, client):
    if not isinstance(result, dict) or result.get("error"):
        return None
    fn = _RENDERERS.get(name)
    if not fn:
        return None
    try:
        return fn(args or {}, result, client)
    except Exception:
        return None          # never let a template bug eat an answer


def _accounts(args, r, c):
    accts = r["accounts"]
    lines = ["You have {} accounts with a total balance of {}:".format(len(accts), _money(r["total_balance"])), ""]
    for a in accts:
        lines.append("- {} ({}): {}, {}{}% YTD".format(
            a["type"], a["id"], _money(a["balance"]),
            "+" if a["ytd_return"] >= 0 else "", a["ytd_return"]))
    return "\n".join(lines)


def _tax(args, r, c):
    return ("Your {} return shows an adjusted gross income of {}, filed {}. "
            "Federal tax was {}, state tax {}, an effective rate of {}%.").format(
        r["year"], _money(r["agi"]), r["filing_status"].lower(),
        _money(r["federal_tax"]), _money(r["state_tax"]), r["effective_rate"])


def _fees(args, r, c):
    f, paid = r["fees"], r.get("paid_this_year", {})
    parts = ["Your advisory fee is {}%, billed {}.".format(f["rate_pct"], f["frequency"].lower())]
    if paid.get("total_paid"):
        by = ", ".join("{} {}".format(k, _money2(v)) for k, v in sorted(paid["by_account"].items()))
        parts.append("So far in {} you have paid {} ({}).".format(paid["year"], _money2(paid["total_paid"]), by))
    parts.append("The most recent charge was {} on {}.".format(_money2(f["last_amount"]), _day(f["last_billed"])))
    return " ".join(parts)


def _meetings(args, r, c):
    up = [m for m in r["meetings"] if m.get("status") == "upcoming"]
    if not up:
        req = [m for m in r["meetings"] if m.get("status") == "requested"]
        if req:
            return ("You have no confirmed meetings yet, but your request for {} is in and "
                    "the office will confirm within one business day.").format(req[0]["type"])
        return "You have nothing scheduled at the moment. Ask me and I can help you request a meeting."
    m = up[0]
    extra = " You also have {} more upcoming.".format(len(up) - 1) if len(up) > 1 else ""
    return "Your next meeting is {} on {} at {}.{}".format(m["type"], _day(m["date"]), m["time"], extra)


def _room(args, r, c):
    lines = ["Your {} contribution room:".format(r["year"]), ""]
    for a in r["accounts"]:
        lines.append("- {} ({}): {} of {} used, {} remaining".format(
            a["account_type"], a["account_id"], _money(a["contributed"]),
            _money(a["limit"]), _money(a["remaining"])))
    return "\n".join(lines)


def _bene(args, r, c):
    lines = ["Here is who is named on each account:", ""]
    for a in r["accounts"]:
        if a["beneficiaries"]:
            named = "; ".join("{} ({}, {}, {}%)".format(
                b["name"], b["relationship"].lower(), b["tier"].lower(), b["share"])
                for b in a["beneficiaries"])
            lines.append("- {} ({}): {}".format(a["type"], a["account_id"], named))
        else:
            lines.append("- {} ({}): none named".format(a["type"], a["account_id"]))
    if r.get("accounts_with_none_named"):
        lines += ["", "If you would like to name someone on {}, ask me how and I will take you straight to the form.".format(
            ", ".join(r["accounts_with_none_named"]))]
    return "\n".join(lines)


def _docs(args, r, c):
    lines = ["You have {} documents on file:".format(len(r["documents"])), ""]
    for d in r["documents"]:
        lines.append("- {} ({}, {})".format(d["name"], d["type"], _day(d["date"])))
    return "\n".join(lines)


def _perf(args, r, c):
    ys, comb = r["years"], r["combined"]
    n = len(r["accounts"])
    if len(ys) == 1:
        head = "Last year ({}) your combined return across your {} accounts was {}%.".format(
            ys[0], n, comb["per_year_pct"][ys[0]])
    else:
        per = ", ".join("{}: {}%".format(y, comb["per_year_pct"][y]) for y in ys)
        head = ("Across your {} accounts, your combined return over {} to {} was {}% ({}).").format(
            n, ys[0], ys[-1], comb["cumulative_pct"], per)
    return (head + " So far this year you are up {}%. Figures are calendar-year account returns "
            "net of fees, averaged and weighted by current balance. Ask about any single account "
            "for the breakdown.").format(comb["ytd_pct"])


def _alloc(args, r, c):
    parts = ", ".join("{} {} ({}%)".format(s["class"], _money(s["value"]), s["pct"]) for s in r["split"])
    return "Across all accounts your {} total is invested as: {}.".format(_money(r["total"]), parts)


def _activity(args, r, c):
    label = (r.get("filter_type") or "").lower()
    period = r.get("filter_month") or ""
    if not r["activity"]:
        what = (label + " activity") if label else "activity"
        when = " in " + period if period else " recently"
        return "I do not see any {}{} across your accounts.".format(what, when)
    lines = ["Here is your recent {}activity, newest first:".format(
        (label + " ") if label else ""), ""]
    for e in r["activity"]:
        amt = ("+" if e["amount"] >= 0 else "-") + "${:,.2f}".format(abs(e["amount"]))
        lines.append("- {} · {} ({}) · {} · {}".format(
            _day(e["date"]), e["account_type"], e["account_id"], e["description"], amt))
    if r["count"] > len(r["activity"]):
        lines += ["", "That is the latest {} of {} entries. The Accounts tab has the full history.".format(
            len(r["activity"]), r["count"])]
    return "\n".join(lines)


def _navigate(args, r, c):
    return "Taking you there now. The button below will bring you back to it any time."


_RENDERERS = {
    "navigate_to": _navigate,
    "get_recent_activity": _activity,
    "get_accounts": _accounts,
    "get_tax_return": _tax,
    "get_fees": _fees,
    "get_meetings": _meetings,
    "get_contribution_room": _room,
    "get_beneficiaries": _bene,
    "get_documents": _docs,
    "get_performance": _perf,
    "get_allocation": _alloc,
}
