"""
Brooke's tool layer.

THE SECURITY RULE, made concrete:
    every executor's first parameter is `client_id`, and it is supplied by the
    server from the authenticated session. The model never sees it, never sends
    it, and cannot influence it. The model chooses WHICH tool to call and with
    what non-identity arguments; the server decides WHOSE data that call reads.
"""

from demo_data import CLIENTS

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


REGISTRY = {
    "get_tax_return":      get_tax_return,
    "get_accounts":        get_accounts,
    "get_holdings":        get_holdings,
    "get_documents":       get_documents,
    "get_meetings":        get_meetings,
    "escalate_to_advisor": escalate_to_advisor,
}


def execute(client_id, name, args):
    """Run a model-requested tool against exactly one client's data."""
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    if not isinstance(args, dict):
        args = {}
    # Identity can never arrive from the model.
    for forbidden in ("client_id", "user_id", "client", "user"):
        args.pop(forbidden, None)
    try:
        return fn(client_id, **args)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
    except PermissionError as e:
        return {"error": str(e)}
