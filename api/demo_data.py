"""
Demo client records for the Brooke AI test harness.

EVERYTHING IN THIS FILE IS FICTIONAL. No real client data belongs here,
and no real client data should ever be loaded into the demo server.
"""

# passcode -> client_id.  Demo-only auth; real build uses Auth0/Clerk + MFA.
PASSCODES = {
    "sarah-2026":  "CLIENT-001",
    "marcus-2026": "CLIENT-002",
    "elena-2026":  "CLIENT-003",
}

CLIENTS = {
    "CLIENT-001": {
        "name": "Sarah Whitfield",
        "advisor": "Jacob Chandler",
        "since": 2019,
        "tax_returns": {
            2025: {"agi": 412_800, "filing_status": "Married filing jointly",
                   "federal_tax": 91_450, "state_tax": 24_768, "effective_rate": 22.2},
            2024: {"agi": 388_200, "filing_status": "Married filing jointly",
                   "federal_tax": 84_100, "state_tax": 23_292, "effective_rate": 21.7},
            2023: {"agi": 351_600, "filing_status": "Married filing jointly",
                   "federal_tax": 74_900, "state_tax": 21_096, "effective_rate": 21.3},
        },
        "accounts": [
            {"id": "ACC-4471", "type": "Joint Brokerage",  "balance": 1_284_300, "ytd_return": 8.4},
            {"id": "ACC-4472", "type": "Traditional IRA",  "balance":   612_900, "ytd_return": 7.1},
            {"id": "ACC-4473", "type": "Roth IRA",         "balance":   198_400, "ytd_return": 9.2},
        ],
        "holdings": {
            "ACC-4471": [
                {"ticker": "VTI",  "name": "Vanguard Total Stock Market ETF", "shares": 2_140, "value": 641_000, "weight": 49.9},
                {"ticker": "VXUS", "name": "Vanguard Total Intl Stock ETF",   "shares": 4_800, "value": 321_600, "weight": 25.0},
                {"ticker": "BND",  "name": "Vanguard Total Bond Market ETF",  "shares": 3_950, "value": 282_400, "weight": 22.0},
                {"ticker": "CASH", "name": "Money Market",                    "shares": 39_300, "value": 39_300, "weight": 3.1},
            ],
            "ACC-4472": [
                {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "shares": 1_020, "value": 305_500, "weight": 49.8},
                {"ticker": "BND", "name": "Vanguard Total Bond Market ETF",  "shares": 4_290, "value": 307_400, "weight": 50.2},
            ],
            "ACC-4473": [
                {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "shares": 662, "value": 198_400, "weight": 100.0},
            ],
        },
        "documents": [
            {"name": "2025 Form 1040",              "type": "Tax Return",   "date": "2026-03-14"},
            {"name": "Q2 2026 Portfolio Statement", "type": "Statement",    "date": "2026-07-05"},
            {"name": "Investment Policy Statement", "type": "Planning",     "date": "2026-01-22"},
            {"name": "2025 Form 1099-DIV",          "type": "Tax Document", "date": "2026-02-01"},
        ],
        "meetings": [
            {"date": "2026-09-12", "time": "10:00 AM", "type": "Annual Review",     "status": "upcoming"},
            {"date": "2026-04-08", "time": "2:00 PM",  "type": "Tax Planning",      "status": "completed"},
            {"date": "2026-01-15", "time": "11:00 AM", "type": "Portfolio Review",  "status": "completed"},
        ],
    },
    "CLIENT-002": {
        "name": "Marcus Delaney",
        "advisor": "Jacob Chandler",
        "since": 2022,
        "tax_returns": {
            2025: {"agi": 196_400, "filing_status": "Single",
                   "federal_tax": 38_900, "state_tax": 11_784, "effective_rate": 19.8},
            2024: {"agi": 178_300, "filing_status": "Single",
                   "federal_tax": 34_200, "state_tax": 10_698, "effective_rate": 19.2},
        },
        "accounts": [
            {"id": "ACC-8812", "type": "Individual Brokerage", "balance": 342_700, "ytd_return": 9.8},
            {"id": "ACC-8813", "type": "Roth IRA",             "balance": 128_500, "ytd_return": 10.4},
        ],
        "holdings": {
            "ACC-8812": [
                {"ticker": "VOO",  "name": "Vanguard S&P 500 ETF",          "shares": 480, "value": 240_000, "weight": 70.0},
                {"ticker": "QQQ",  "name": "Invesco QQQ Trust",             "shares": 145, "value":  72_500, "weight": 21.2},
                {"ticker": "CASH", "name": "Money Market",                  "shares": 30_200, "value": 30_200, "weight": 8.8},
            ],
            "ACC-8813": [
                {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "shares": 257, "value": 128_500, "weight": 100.0},
            ],
        },
        "documents": [
            {"name": "2025 Form 1040",              "type": "Tax Return", "date": "2026-04-02"},
            {"name": "Q2 2026 Portfolio Statement", "type": "Statement",  "date": "2026-07-05"},
        ],
        "meetings": [
            {"date": "2026-10-03", "time": "3:00 PM", "type": "Annual Review", "status": "upcoming"},
        ],
    },
    "CLIENT-003": {
        "name": "Elena Vasquez",
        "advisor": "Jacob Chandler",
        "since": 2015,
        "tax_returns": {
            2025: {"agi": 884_100, "filing_status": "Married filing jointly",
                   "federal_tax": 251_300, "state_tax": 61_887, "effective_rate": 28.4},
            2024: {"agi": 812_500, "filing_status": "Married filing jointly",
                   "federal_tax": 228_900, "state_tax": 56_875, "effective_rate": 28.2},
        },
        "accounts": [
            {"id": "ACC-2201", "type": "Joint Brokerage",   "balance": 3_412_000, "ytd_return": 7.9},
            {"id": "ACC-2202", "type": "Traditional IRA",   "balance": 1_106_400, "ytd_return": 6.8},
            {"id": "ACC-2203", "type": "Donor Advised Fund","balance":   284_000, "ytd_return": 5.2},
        ],
        "holdings": {
            "ACC-2201": [
                {"ticker": "VTI",  "name": "Vanguard Total Stock Market ETF", "shares": 5_690, "value": 1_705_000, "weight": 50.0},
                {"ticker": "VXUS", "name": "Vanguard Total Intl Stock ETF",   "shares": 12_700, "value":  851_000, "weight": 24.9},
                {"ticker": "MUB",  "name": "iShares National Muni Bond ETF",  "shares": 7_420, "value":  788_000, "weight": 23.1},
                {"ticker": "CASH", "name": "Money Market",                    "shares": 68_000, "value":  68_000, "weight": 2.0},
            ],
            "ACC-2202": [
                {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "shares": 1_845, "value": 553_200, "weight": 50.0},
                {"ticker": "BND", "name": "Vanguard Total Bond Market ETF",  "shares": 7_720, "value": 553_200, "weight": 50.0},
            ],
            "ACC-2203": [
                {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "shares": 947, "value": 284_000, "weight": 100.0},
            ],
        },
        "documents": [
            {"name": "2025 Form 1040",                 "type": "Tax Return", "date": "2026-03-28"},
            {"name": "Q2 2026 Portfolio Statement",    "type": "Statement",  "date": "2026-07-05"},
            {"name": "Charitable Giving Plan 2026",    "type": "Planning",   "date": "2026-02-11"},
            {"name": "Estate Summary",                 "type": "Planning",   "date": "2025-11-30"},
        ],
        "meetings": [
            {"date": "2026-09-05", "time": "9:00 AM", "type": "Estate Planning", "status": "upcoming"},
            {"date": "2026-06-18", "time": "1:00 PM", "type": "Annual Review",   "status": "completed"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Extra fixtures for the account questions clients actually ask: recent
# activity, who the beneficiaries are, how much IRA room is left, what the fee
# is. Still entirely fictional. Contribution limits here are demo values, not a
# statement of real IRS limits.
# ---------------------------------------------------------------------------

_EXTRA = {
    "CLIENT-001": {
        "activity": {
            "ACC-4471": [
                {"date": "2026-08-14", "type": "Dividend",     "description": "VTI dividend",            "amount":  3_182.00},
                {"date": "2026-08-01", "type": "Contribution", "description": "Transfer from Chase 4021","amount": 10_000.00},
                {"date": "2026-07-22", "type": "Buy",          "description": "Bought 34 VTI",           "amount": -10_180.00},
                {"date": "2026-07-15", "type": "Fee",          "description": "Advisory fee Q2 2026",    "amount": -2_247.00},
            ],
            "ACC-4472": [
                {"date": "2026-08-10", "type": "Dividend",     "description": "BND dividend",            "amount":  1_094.00},
                {"date": "2026-06-30", "type": "Fee",          "description": "Advisory fee Q2 2026",    "amount": -1_072.00},
            ],
            "ACC-4473": [
                {"date": "2026-04-02", "type": "Contribution", "description": "2025 Roth contribution",  "amount":  7_000.00},
            ],
        },
        "beneficiaries": {
            "ACC-4471": [],
            "ACC-4472": [{"name": "Daniel Whitfield", "relationship": "Spouse", "share": 100, "tier": "Primary"}],
            "ACC-4473": [{"name": "Daniel Whitfield", "relationship": "Spouse", "share": 100, "tier": "Primary"},
                         {"name": "Claire Whitfield", "relationship": "Child",  "share": 100, "tier": "Contingent"}],
        },
        "contributions": {
            2026: {"ACC-4472": {"contributed": 0,     "limit": 8_000, "type": "Traditional IRA"},
                   "ACC-4473": {"contributed": 3_500, "limit": 8_000, "type": "Roth IRA"}},
        },
        "fees": {"rate_pct": 0.85, "last_billed": "2026-07-15", "last_amount": 3_319.00, "frequency": "Quarterly"},
    },
    "CLIENT-002": {
        "activity": {
            "ACC-8812": [
                {"date": "2026-08-18", "type": "Buy",          "description": "Bought 12 VOO",            "amount": -6_000.00},
                {"date": "2026-08-01", "type": "Contribution", "description": "Transfer from Ally 8890",  "amount":  6_000.00},
                {"date": "2026-07-15", "type": "Fee",          "description": "Advisory fee Q2 2026",     "amount":   -728.00},
            ],
            "ACC-8813": [
                {"date": "2026-01-08", "type": "Contribution", "description": "2026 Roth contribution",   "amount":  7_000.00},
            ],
        },
        "beneficiaries": {
            "ACC-8812": [],
            "ACC-8813": [{"name": "Rosa Delaney", "relationship": "Parent", "share": 100, "tier": "Primary"}],
        },
        "contributions": {
            2026: {"ACC-8813": {"contributed": 7_000, "limit": 7_000, "type": "Roth IRA"}},
        },
        "fees": {"rate_pct": 0.90, "last_billed": "2026-07-15", "last_amount": 1_060.00, "frequency": "Quarterly"},
    },
    "CLIENT-003": {
        "activity": {
            "ACC-2201": [
                {"date": "2026-08-20", "type": "Dividend",     "description": "MUB dividend",             "amount":  2_041.00},
                {"date": "2026-08-05", "type": "Sell",         "description": "Sold 400 VXUS",            "amount": 26_800.00},
                {"date": "2026-07-15", "type": "Fee",          "description": "Advisory fee Q2 2026",     "amount": -6_398.00},
            ],
            "ACC-2202": [
                {"date": "2026-08-12", "type": "Dividend",     "description": "BND dividend",             "amount":  1_968.00},
            ],
            "ACC-2203": [
                {"date": "2026-06-02", "type": "Grant",        "description": "Grant to Ridgeline Food Bank", "amount": -25_000.00},
                {"date": "2026-02-11", "type": "Contribution", "description": "Appreciated VTI contribution", "amount": 150_000.00},
            ],
        },
        "beneficiaries": {
            "ACC-2201": [],
            "ACC-2202": [{"name": "Miguel Vasquez", "relationship": "Spouse", "share": 100, "tier": "Primary"}],
            "ACC-2203": [],
        },
        "contributions": {
            2026: {"ACC-2202": {"contributed": 8_000, "limit": 8_000, "type": "Traditional IRA"}},
        },
        "fees": {"rate_pct": 0.75, "last_billed": "2026-07-15", "last_amount": 8_998.00, "frequency": "Quarterly"},
    },
}

for _cid, _extra in _EXTRA.items():
    CLIENTS[_cid].update(_extra)


# ---------------------------------------------------------------------------
# Calendar-year account returns (%, net of fees). Source of truth for the
# performance analytics: stored as data, never inferred from balance deltas,
# because balances move with contributions and withdrawals too.
# ---------------------------------------------------------------------------

_ANNUAL_RETURNS = {
    "CLIENT-001": {
        "ACC-4471": {2023: 16.8, 2024: 12.4, 2025: 10.1},
        "ACC-4472": {2023: 11.2, 2024: 8.9,  2025: 7.4},
        "ACC-4473": {2023: 24.1, 2024: 17.9, 2025: 12.6},
    },
    "CLIENT-002": {
        "ACC-8812": {2023: 22.4, 2024: 18.7, 2025: 13.9},
        "ACC-8813": {2023: 24.0, 2024: 17.5, 2025: 12.8},
    },
    "CLIENT-003": {
        "ACC-2201": {2023: 13.1, 2024: 10.2, 2025: 8.7},
        "ACC-2202": {2023: 11.0, 2024: 8.8,  2025: 7.2},
        "ACC-2203": {2023: 24.1, 2024: 17.9, 2025: 12.6},
    },
}
for _cid, _ar in _ANNUAL_RETURNS.items():
    CLIENTS[_cid]["annual_returns"] = _ar
