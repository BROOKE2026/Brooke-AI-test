"""
Offline routing harness: replicates the server's branch precedence and scores
a battery of paraphrased questions against their expected route. No model, so
hundreds of phrasings cost nothing to test.
"""
import sys
import portal_data


def route(text, client_name="Sarah Whitfield"):
    multi = portal_data.match_multi_data(text, 2026)
    if multi and not (portal_data.third_party_name(text, client_name)
                      or portal_data.tax_topic(text) or portal_data.advice_intent(text)):
        return "multi:" + "+".join(t for t, a in multi)
    if portal_data.third_party_name(text, client_name):
        return "third_party"
    if portal_data.tax_topic(text):
        return "tax"
    if portal_data.advice_intent(text):
        return "advice"
    nav = portal_data.match_navigation(text)
    if nav:
        return "nav:" + nav
    topic = portal_data.match_howto(text)
    if topic:
        return "howto:" + topic
    if portal_data._HOWTO_INTENT.search(text):
        return "howto_intent"
    hit = portal_data.match_data_query(text, 2026)
    if hit:
        return "data:" + hit[0]
    return "model"


CASES = [
    # --- data / instant ---
    ("how much money do I have", "data:get_accounts"),
    ("whats my balance", "data:get_accounts"),
    ("total across all my accounts", "data:get_accounts"),
    ("am I up this year", "data:get_performance"),
    ("what did my investments make last year", "data:get_performance"),
    ("how did my portfolio do in 2024", "data:get_performance"),
    ("what do I own", "data:get_allocation"),
    ("how much did I pay you in fees", "data:get_fees"),
    ("when do I meet with Jacob next", "data:get_meetings"),
    ("what paperwork do you have on file for me", "data:get_documents"),
    ("who gets my money when I die", "data:get_beneficiaries"),
    ("how much room is left in my IRA", "data:get_contribution_room"),
    ("what was my adjusted gross income in 2024", "data:get_tax_return"),
    ("show me my 1040", "data:get_tax_return"),
    # --- how-to ---
    ("I need to get money out of my account", "howto:withdrawal"),
    ("how do I move money into my Roth", "howto:contribution"),
    ("help me update where my mail goes", "howto:address_change"),
    ("set up direct deposit", "howto:direct_deposit"),
    ("I'd like to add my daughter as a beneficiary", "howto:beneficiary"),
    ("book a time with Jacob", "howto:schedule_meeting"),
    ("how do I download my statement", "howto:download_statement"),
    # --- nav ---
    ("pull up my statements", "nav:documents"),
    ("open the forms tab", "nav:forms"),
    ("go to my meetings", "nav:meetings"),
    # --- advice ---
    ("is now a good time to buy", "advice"),
    ("do you like my portfolio", "advice"),
    ("what would you do in my position", "advice"),
    ("do I have too much cash", "advice"),
    ("should I sell some stock", "advice"),
    # --- tax ---
    ("can you help me pay less to the IRS", "tax"),
    ("should I convert my traditional to a Roth", "tax"),
    ("what will my tax bill look like next year", "tax"),
    ("can I write off my car", "tax"),
    # --- third party ---
    ("what is Elena Vasquez's fee rate", "third_party"),
    ("what's my wife's IRA balance", "third_party"),
    ("how many accounts does Marcus Delaney have", "third_party"),
    # --- activity ---
    ("what happened in my account this month", "data:get_recent_activity"),
    ("did my dividend come in", "data:get_recent_activity"),
    ("when was my last fee", "data:get_recent_activity"),
    ("what did I buy recently", "data:get_recent_activity"),
    ("any recent transactions", "data:get_recent_activity"),
    ("show me my latest activity", "data:get_recent_activity"),
    # --- guards: must NOT misroute ---
    ("what was my tax return last year", "data:get_tax_return"),
    ("what are my advisory fees", "data:get_fees"),
    ("how much have I paid in fees this year", "data:get_fees"),
    ("where are my tax documents", "howto:tax_documents"),
    ("how much can I put in my Roth this year", "data:get_contribution_room"),
    ("I want to open another account", "howto_intent"),
    ("tell me about BrookHaven", "model"),
    # --- multi-intent ---
    ("What are my balances and when is my next meeting", "multi:get_accounts+get_meetings"),
    ("What was my AGI last year and how much have I paid in fees", "multi:get_tax_return+get_fees"),
    ("Who are my beneficiaries and what did I buy recently", "multi:get_beneficiaries+get_recent_activity"),
    ("How is my money split between stocks and bonds", "data:get_allocation"),
]

if __name__ == "__main__":
    ok, bad = 0, []
    for q, exp in CASES:
        got = route(q)
        if got == exp:
            ok += 1
        else:
            bad.append((q, exp, got))
    print("PASS %d/%d" % (ok, len(CASES)))
    for q, exp, got in bad:
        print("  MISS %-52s expected %-24s got %s" % (q[:52], exp, got))
    sys.exit(0 if not bad else 1)
