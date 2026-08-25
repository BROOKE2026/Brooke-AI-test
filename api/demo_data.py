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
