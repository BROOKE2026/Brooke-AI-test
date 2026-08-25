"""
Computed answers over one client's records. Pure functions, no model anywhere.

Everything here is arithmetic a spreadsheet could do; keeping it in code means
the numbers are exact, instant, and identical every time they are asked.
"""

from datetime import date

ASSET_CLASS = {
    "VTI": "US stocks", "VOO": "US stocks", "QQQ": "US stocks",
    "VXUS": "International stocks",
    "BND": "Bonds", "MUB": "Bonds",
    "CASH": "Cash",
}


def performance(c, years=3):
    """Per-account and combined returns over the last `years` complete
    calendar years, plus current YTD. Combined figures are averages of account
    returns weighted by current balance, and say so."""
    years = max(1, min(int(years or 3), 10))
    this_year = date.today().year
    ys = [this_year - i for i in range(years, 0, -1)]

    rows = []
    for a in c["accounts"]:
        ar = c.get("annual_returns", {}).get(a["id"], {})
        per = {y: ar[y] for y in ys if y in ar}
        cum = 1.0
        for r in per.values():
            cum *= (1 + r / 100.0)
        row = {
            "account_id": a["id"], "type": a["type"], "balance": a["balance"],
            "per_year_pct": per,
            "cumulative_pct": round((cum - 1) * 100, 1) if per else None,
            "ytd_pct": a.get("ytd_return"),
        }
        # Approximate dollar growth, backed out of the current balance and the
        # cumulative return. Contributions are not separated out, so this is an
        # estimate, but it makes rate-vs-dollars questions answerable from data:
        # the highest RETURN and the biggest DOLLAR contributor often differ.
        if row["cumulative_pct"] is not None:
            row["approx_growth_dollars"] = round(
                a["balance"] * (1 - 1 / (cum if cum > 0 else 1)))
        rows.append(row)

    total = sum(a["balance"] for a in c["accounts"]) or 1
    have = [r for r in rows if r["cumulative_pct"] is not None]
    combined = {
        "method": "average of account returns, weighted by current balance",
        "per_year_pct": {
            y: round(sum(r["per_year_pct"].get(y, 0) * r["balance"] for r in have) / total, 1)
            for y in ys},
        "cumulative_pct": round(sum(r["cumulative_pct"] * r["balance"] for r in have) / total, 1),
        "ytd_pct": round(sum((r["ytd_pct"] or 0) * r["balance"] for r in rows) / total, 1),
    }
    biggest = max((r for r in rows if r.get("approx_growth_dollars") is not None),
                  key=lambda r: r["approx_growth_dollars"], default=None)
    return {"years": ys, "accounts": rows, "combined": combined,
            "biggest_dollar_contributor": (
                {"account_id": biggest["account_id"], "type": biggest["type"],
                 "approx_growth_dollars": biggest["approx_growth_dollars"]}
                if biggest else None),
            "note": ("Calendar-year account returns, net of fees. Dollar growth "
                     "figures are estimates that do not separate contributions.")}


def allocation(c):
    """Dollar and percentage split by asset class, across every account."""
    buckets = {}
    for acct_holdings in c.get("holdings", {}).values():
        for h in acct_holdings:
            cls = ASSET_CLASS.get(h["ticker"], "Other")
            buckets[cls] = buckets.get(cls, 0) + h["value"]
    total = sum(buckets.values()) or 1
    split = [{"class": k, "value": v, "pct": round(v * 100.0 / total, 1)}
             for k, v in sorted(buckets.items(), key=lambda kv: -kv[1])]
    return {"total": total, "split": split}


def fees_paid(c, year=None):
    """Advisory fees actually charged in a year, summed from account activity."""
    year = int(year or date.today().year)
    by_acct, total = {}, 0.0
    for acct, entries in c.get("activity", {}).items():
        for e in entries:
            if e["type"] == "Fee" and e["date"].startswith(str(year)):
                amt = abs(e["amount"])
                by_acct[acct] = by_acct.get(acct, 0) + amt
                total += amt
    return {"year": year, "total_paid": round(total, 2), "by_account": by_acct}
