"""
Brooke's tool layer.

THE SECURITY RULE, made concrete:
    every executor's first parameter is `client_id`, and it is supplied by the
    server from the authenticated session. The model never sees it, never sends
    it, and cannot influence it. The model chooses WHICH tool to call and with
    what non-identity arguments; the server decides WHOSE data that call reads.
"""

from demo_data import CLIENTS
import analytics
from portal_data import HOWTOS, FORMS, TABS

# ---------------------------------------------------------------- schemas ---
# Sent to the model. Note that no schema exposes a client/user/account-owner id.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_tax_return",
            "description": (
                "Retrieve the client's filed tax return figures for a given year, "
                "including AGI, filing status, federal and state tax, and effective rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Tax year, e.g. 2025"}
                },
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_accounts",
            "description": "List all of the client's investment accounts with current balances and YTD return.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_holdings",
            "description": "List the positions held inside one specific account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Account id such as ACC-4471"}
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_documents",
            "description": "List documents available to the client in the portal (statements, tax forms, planning documents).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_meetings",
            "description": "List the client's upcoming and past meetings with their advisor.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_activity",
            "description": "List recent transactions in one account: dividends, buys, sells, contributions, withdrawals, fees.",
            "parameters": {
                "type": "object",
                "properties": {"account_id": {"type": "string", "description": "Account id such as ACC-4471"}},
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_beneficiaries",
            "description": "Show who is named as beneficiary on each of the client's accounts, and which accounts have none named.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_contribution_room",
            "description": "How much the client has contributed to their retirement accounts for a year and how much room is left.",
            "parameters": {
                "type": "object",
                "properties": {"year": {"type": "integer", "description": "Contribution year, e.g. 2026"}},
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fees",
            "description": "The client's advisory fee rate, billing frequency, and the most recent fee charged.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_performance",
            "description": (
                "The client's investment returns: per-account and combined, for the last N "
                "complete calendar years plus year-to-date. Use for any question about returns, "
                "performance, growth, or how their investments have done."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "years": {"type": "integer",
                              "description": "How many complete calendar years back, 1-10. Default 3."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_allocation",
            "description": "How the client's money is split across asset classes (US stocks, international stocks, bonds, cash), in dollars and percent, across all accounts.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_howto",
            "description": (
                "Get step by step instructions for doing something in the portal, plus a button "
                "that takes the client straight to the right place. Use this for any 'how do I', "
                "'where do I', or 'can you help me' question about using the portal or filling in a form."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": sorted(HOWTOS.keys()),
                        "description": "Which task the client is asking about",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": (
                "Give the client a button to a section of the portal, when they just want to be taken "
                "somewhere rather than told how to do a task. Do not use this if a get_howto topic fits."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tab": {"type": "string", "enum": sorted(TABS.keys()), "description": "Which section"}
                },
                "required": ["tab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_advisor",
            "description": (
                "Route a question to the client's human advisor. MUST be used for anything "
                "asking whether to buy, sell, rebalance, contribute, withdraw, or change "
                "strategy, and for any request for a recommendation or opinion on what the "
                "client should do."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Short summary of what the client is asking"}
                },
                "required": ["topic"],
            },
        },
    },
]

# -------------------------------------------------------------- executors ---

def _client(client_id):
    c = CLIENTS.get(client_id)
    if not c:
        raise PermissionError("no such client in session")
    return c


def get_tax_return(client_id, year=None):
    c = _client(client_id)
    try:
        year = int(year)
    except (TypeError, ValueError):
        return {"error": "A valid four-digit year is required."}
    rec = c["tax_returns"].get(year)
    if not rec:
        have = sorted(c["tax_returns"].keys(), reverse=True)
        return {"error": f"No {year} return on file.", "years_available": have}
    return {"year": year, **rec}


def get_accounts(client_id):
    c = _client(client_id)
    total = sum(a["balance"] for a in c["accounts"])
    return {"accounts": c["accounts"], "total_balance": total}


def get_holdings(client_id, account_id=None):
    c = _client(client_id)
    owned = {a["id"] for a in c["accounts"]}
    if account_id not in owned:
        # The model asked for an account this session does not own. Refuse, and
        # do not leak whether that account exists for someone else.
        return {"error": "That account is not available on this login.",
                "your_accounts": sorted(owned)}
    return {"account_id": account_id, "holdings": c["holdings"].get(account_id, [])}


def get_documents(client_id):
    return {"documents": _client(client_id)["documents"]}


def get_meetings(client_id):
    return {"meetings": _client(client_id)["meetings"]}


def escalate_to_advisor(client_id, topic=None):
    c = _client(client_id)
    return {
        "status": "routed",
        "advisor": c["advisor"],
        "topic": topic or "unspecified",
        "note": "A message has been sent to the advisor. Tell the client their advisor "
                "will follow up, and do not attempt to answer the question yourself.",
    }


def get_activity(client_id, account_id=None):
    c = _client(client_id)
    owned = {a["id"] for a in c["accounts"]}
    if account_id not in owned:
        return {"error": "That account is not available on this login.",
                "your_accounts": sorted(owned)}
    return {"account_id": account_id, "activity": c["activity"].get(account_id, [])}


def get_beneficiaries(client_id):
    c = _client(client_id)
    out, missing = [], []
    for a in c["accounts"]:
        named = c["beneficiaries"].get(a["id"], [])
        out.append({"account_id": a["id"], "type": a["type"], "beneficiaries": named})
        if not named:
            missing.append(a["id"])
    return {"accounts": out, "accounts_with_none_named": missing}


def get_contribution_room(client_id, year=None):
    c = _client(client_id)
    try:
        year = int(year)
    except (TypeError, ValueError):
        return {"error": "A valid four-digit year is required."}
    rec = c["contributions"].get(year)
    if not rec:
        return {"error": "No contribution tracking on file for %s." % year,
                "years_available": sorted(c["contributions"].keys(), reverse=True)}
    rows = []
    for acct, r in rec.items():
        rows.append({"account_id": acct, "account_type": r["type"],
                     "contributed": r["contributed"], "limit": r["limit"],
                     "remaining": max(0, r["limit"] - r["contributed"])})
    return {"year": year, "accounts": rows,
            "note": "Limits shown are the figures on file for this demo, not tax advice."}


def get_fees(client_id):
    c = _client(client_id)
    paid = analytics.fees_paid(c)
    return {"fees": c["fees"], "paid_this_year": paid}


def get_performance(client_id, years=None):
    c = _client(client_id)
    try:
        years = int(years) if years is not None else 3
    except (TypeError, ValueError):
        years = 3
    return analytics.performance(c, years)


def get_allocation(client_id):
    return analytics.allocation(_client(client_id))


def get_howto(client_id, topic=None):
    _client(client_id)
    h = HOWTOS.get(topic)
    if not h:
        return {"error": "No instructions on file for that.",
                "topics_available": sorted(HOWTOS.keys())}
    return {"title": h["title"], "steps": h["steps"], "note": h.get("note"), "open": h["open"]}


def navigate_to(client_id, tab=None):
    _client(client_id)
    if tab not in TABS:
        return {"error": "No such section.", "sections": sorted(TABS.keys())}
    return {"section": TABS[tab], "open": {"tab": tab, "label": "Open %s" % TABS[tab]}}


REGISTRY = {
    "get_tax_return":      get_tax_return,
    "get_accounts":        get_accounts,
    "get_holdings":        get_holdings,
    "get_documents":       get_documents,
    "get_meetings":        get_meetings,
    "get_activity":          get_activity,
    "get_beneficiaries":     get_beneficiaries,
    "get_contribution_room": get_contribution_room,
    "get_fees":              get_fees,
    "get_performance":       get_performance,
    "get_allocation":        get_allocation,
    "get_howto":             get_howto,
    "navigate_to":           navigate_to,
    "escalate_to_advisor": escalate_to_advisor,
}


def execute(client_id, name, args):
    """Run a model-requested tool against exactly one client's data.

    Every result is stamped with whose data it is. Without this the model happily
    narrated one client's figures under a name lifted from the question, which
    reads exactly like a data breach even though none occurred."""
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    if not isinstance(args, dict):
        args = {}
    # Identity can never arrive from the model.
    for forbidden in ("client_id", "user_id", "client", "user"):
        args.pop(forbidden, None)
    try:
        out = fn(client_id, **args)
        if isinstance(out, dict) and "error" not in out:
            who = CLIENTS.get(client_id, {}).get("name")
            if who:
                out = dict(out)
                out["data_belongs_to"] = who
        return out
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
    except PermissionError as e:
        return {"error": str(e)}
