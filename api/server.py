"""
Brooke AI - test harness API.

  browser  ->  this server  ->  Ollama (qwen3:14b)
                    |
                    +-> tools.py -> demo client records

This server is the ONLY layer that touches client data. The model host is handed
assembled text and hands back tokens; it holds no credentials and no records.
On the real build the model host is the Mac Studio pool on a private LAN.

DEMO ONLY: passcode auth, in-memory sessions, fictional data.
"""

import os, json, time, secrets, asyncio, re, uuid
from datetime import date, timedelta
from collections import defaultdict

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import tools
import portal_data
import instant
from demo_data import PASSCODES, CLIENTS

OLLAMA   = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL    = os.environ.get("BROOKE_MODEL", "qwen3:14b")
# Reasoning lane for hard questions. On a 16GB host leave STRONG unset: it
# reuses the same weights with thinking enabled (zero extra memory). On the
# Studios point it at a bigger model, e.g. BROOKE_MODEL_STRONG=qwen3:14b.
STRONG   = os.environ.get("BROOKE_MODEL_STRONG", "")
# off   = hard questions use the normal lane (right for a 16GB host)
# think = same weights with thinking enabled (slower, better reasoning)
# strong= use BROOKE_MODEL_STRONG (Studios)
HARD_MODE = os.environ.get("BROOKE_HARD_MODE", "off")
MAX_HOPS = 4                      # tool-call rounds before we force an answer
RATE_N, RATE_WINDOW = 20, 60      # requests per token per minute

SYSTEM_PROMPT = """You are Brooke, the client assistant for BrookHaven.

Today is {today}. The current year is {year}, so "last year" means {last_year} and
"this year" means {year}. Always resolve relative dates against today's date, never
against your own assumptions about what year it is.

You are speaking with {name}, a client since {since}. Their advisor is {advisor}.

HOW YOU WORK
- Every number you state about this client must come from a tool call you just made. If you have not called a tool, you do not know the figure. Never estimate, recall, or infer a client's numbers.
- Call tools before answering questions about tax returns, accounts, holdings, activity, beneficiaries, contribution room, fees, documents, or meetings. Do not ask permission first, just retrieve it.
- If a tool returns an error or no data, say so plainly and say what is available instead.
- If you have no tool for what they asked, say you do not have it and that {advisor} can help. Never direct them to the IRS, a bank, a tax professional, or any other outside party. You do not know what they should contact, and sending them elsewhere is not your call.

HELPING THEM DO THINGS
- When they ask how to do something, where something is, or how to fill in a form, call get_howto. When they just want to be taken somewhere, call navigate_to.
- When instructions are retrieved, the steps and a button are rendered for the client automatically. Do not retype them. Write one short sentence introducing them and stop.
- A button to the right page is added under your message automatically. Never write a URL, never write a markdown link, and never say "click here". Do not mention the button before the steps.
- If a task needs a number you can look up, look it up first. For a contribution question, check their remaining room with get_contribution_room before you send them to the form.

WHAT YOU DO NOT DO
- You do not give investment, tax, or financial advice.
- When a client asks whether to buy, sell, rebalance, contribute, withdraw, or change strategy, or asks "should I", "what do you think", or "would you recommend", you do NOT answer it and you do NOT decline it in your own words. You CALL escalate_to_advisor first, and only then tell the client you have passed it to their advisor. Declining without calling the tool is a failure, because the advisor never finds out they were asked.
- Every tool result carries data_belongs_to. That is whose figures you are holding, and it is always {name}. Never present those figures under any other person's name, no matter whose name appeared in the question.
- You do not discuss any person other than {name}. You have no access to anyone else's records. If asked about another person or an account that is not theirs, say you can only see their own information.

VOICE
- Warm, direct, professional. You work for a wealth management firm and you sound like it.
- Brief. Two or three sentences unless they asked for a list.
- Never offer to help adjust, change, improve, or rebalance their investments, and never invite questions about whether their numbers are good. You would have to refuse the follow-up. Offer more detail, or offer their advisor.
- Format currency readably, like $412,800.
- Refer to the advisor by name ("Jacob Chandler will follow up"). Never use he/she/his/her for the advisor, since you have not been told their pronouns.
- Never use em dashes. Use commas, periods, or parentheses instead.
- Write plain text. No markdown, no asterisks for bold, no pound signs for headings. The chat window shows your text literally, so "**Form 1040**" appears to the client with the asterisks visible. For lists, start each line with "- " and nothing else.
"""


def build_system(client_id):
    c = CLIENTS[client_id]
    today = date.today()
    return SYSTEM_PROMPT.format(
        name=c["name"], since=c["since"], advisor=c["advisor"],
        today=today.strftime("%B %-d, %Y"), year=today.year, last_year=today.year - 1,
    )


# ------------------------------------------------------------- app + auth ---

app = FastAPI(title="Brooke AI test harness")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("BROOKE_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}                       # token -> {client_id, created}
HITS = defaultdict(list)            # token -> [timestamps]
SESSION_TTL = 8 * 3600


def resolve(authorization, rate=True):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not signed in")
    tok = authorization[7:]
    s = SESSIONS.get(tok)
    if not s or time.time() - s["created"] > SESSION_TTL:
        SESSIONS.pop(tok, None)
        raise HTTPException(401, "Session expired, please sign in again")
    if rate:
        now = time.time()
        HITS[tok] = [t for t in HITS[tok] if now - t < RATE_WINDOW]
        if len(HITS[tok]) >= RATE_N:
            raise HTTPException(429, "Too many messages, give it a minute")
        HITS[tok].append(now)
    return s["client_id"]


class LoginReq(BaseModel):
    passcode: str


class ChatReq(BaseModel):
    message: str
    history: list = []


@app.get("/api/health")
async def health():
    up, models = False, []
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{OLLAMA}/api/tags")
            up = r.status_code == 200
            models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return {"ok": True, "model": MODEL, "ollama_up": up,
            "model_present": MODEL in models, "sessions": len(SESSIONS)}


@app.post("/api/login")
async def login(req: LoginReq):
    cid = PASSCODES.get(req.passcode.strip().lower())
    if not cid:
        await asyncio.sleep(0.5)                     # blunt the guessing loop
        raise HTTPException(401, "That passcode was not recognised")
    tok = secrets.token_urlsafe(32)
    SESSIONS[tok] = {"client_id": cid, "created": time.time()}
    c = CLIENTS[cid]
    return {"token": tok, "name": c["name"], "advisor": c["advisor"], "since": c["since"]}


@app.get("/api/portal")
async def portal(authorization: str = Header(None)):
    """Everything the tabs render, for exactly one client."""
    cid = resolve(authorization, rate=False)
    c = CLIENTS[cid]
    return {
        "name": c["name"], "advisor": c["advisor"], "since": c["since"],
        "accounts": c["accounts"],
        "holdings": c["holdings"],
        "documents": c["documents"],
        "meetings": c["meetings"],
        "tax_returns": {str(k): v for k, v in sorted(c["tax_returns"].items(), reverse=True)},
        "activity": c["activity"],
        "beneficiaries": c["beneficiaries"],
        "contributions": {str(k): v for k, v in c["contributions"].items()},
        "fees": c["fees"],
        "forms": portal_data.FORMS,
        "tabs": portal_data.TABS,
    }


class MeetingReq(BaseModel):
    topic: str = ""
    advisor_type: str = "advisor"
    date: str = ""
    time: str = ""


@app.post("/api/meeting_request")
async def meeting_request(req: MeetingReq, authorization: str = Header(None)):
    cid = resolve(authorization, rate=False)
    c = CLIENTS[cid]
    open_reqs = [m for m in c["meetings"] if m.get("status") == "requested"]
    if len(open_reqs) >= 3:
        raise HTTPException(429, "You already have 3 open meeting requests. "
                                 "The office will be in touch about those first.")
    kind = "Tax Planning Call" if req.advisor_type == "tax" else "Advisor Call"
    meeting = {"date": req.date or "TBD",
               "time": req.time or "flexible",
               "type": kind, "status": "requested",
               "topic": req.topic[:140]}
    c["meetings"].insert(0, meeting)
    ics = build_ics(kind, req.topic, req.date, req.time) if req.date and req.time else None
    return {"ok": True, "meeting": meeting, "ics": ics,
            "note": "The office confirms requests within one business day."}


@app.post("/api/logout")
async def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        SESSIONS.pop(authorization[7:], None)
    return {"ok": True}


# ------------------------------------------------------------- chat stream ---

def sse(obj):
    return f"data: {json.dumps(obj)}\n\n"


def proposed_slots(n=3):
    """Next n weekdays, alternating morning and afternoon."""
    out, d, i = [], date.today(), 0
    while len(out) < n:
        d += timedelta(days=1)
        if d.weekday() >= 5:
            continue
        t = "10:00 AM" if i % 2 == 0 else "2:00 PM"
        out.append({"date": d.isoformat(), "time": t,
                    "label": d.strftime("%A, %B %-d") + " at " + t})
        i += 1
    return out


def build_ics(kind, topic, iso_date, time_str):
    try:
        hour = int(time_str.split(":")[0])
        if "PM" in time_str.upper() and hour != 12:
            hour += 12
        start = iso_date.replace("-", "") + "T%02d0000" % hour
        endh = "T%02d3000" % hour
        end = iso_date.replace("-", "") + endh
    except Exception:
        return None
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BrookHaven//Brooke//EN",
        "BEGIN:VEVENT",
        "UID:" + uuid.uuid4().hex + "@brookhaven.us",
        "DTSTART:" + start, "DTEND:" + end,
        "SUMMARY:BrookHaven " + kind,
        "DESCRIPTION:" + (topic or "").replace("\n", " ")[:180],
        "STATUS:TENTATIVE",
        "END:VEVENT", "END:VCALENDAR", ""])


THINK = re.compile(r"<think>.*?</think>", re.S)
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__", re.S)
_MD_HEAD = re.compile(r"^#{1,6}\s*", re.M)


def _strip_md(t):
    """The chat bubble renders literal text, so markup must not survive."""
    t = _MD_BOLD.sub(lambda m: m.group(1) or m.group(2), t)
    return _MD_HEAD.sub("", t)


def _visible(buf, final=False):
    """Text safe to show now. Holds back an unclosed ** so a bold marker is
    never emitted and then retracted once its partner arrives."""
    raw = THINK.sub("", buf)
    if not final:
        trail = re.search(r"[*_]+$", raw)
        if trail:
            raw = raw[:trail.start()]
        if raw.count("**") % 2 == 1:
            raw = raw[:raw.rfind("**")]
    return _strip_md(raw)


@app.post("/api/chat")
async def chat(req: ChatReq, authorization: str = Header(None)):
    client_id = resolve(authorization)

    messages = [{"role": "system", "content": build_system(client_id)}]
    for m in req.history[-12:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": req.message})

    # Router tier. A how-to question is resolved in code before the model runs,
    # because in testing the model sometimes skipped get_howto and invented
    # portal steps. Wrong instructions about a financial form are worse than a
    # slow answer, so this path does not depend on the model choosing correctly.
    # Highest-priority guard: a question about someone else never reaches the
    # model or a tool. It gets a fixed answer, because the failure mode here was
    # the model narrating THIS client's figures under someone else's name.
    third_party = portal_data.third_party_name(req.message, CLIENTS[client_id]["name"])

    # Evaluative questions are advice at an RIA, and they were also the ones the
    # model dead-ended on ("let me check your balances" then no tool call).
    advice = not third_party and portal_data.advice_intent(req.message)
    taxq = not third_party and portal_data.tax_topic(req.message)
    big = portal_data.large_amount(req.message)
    nav_tab = None if third_party or advice else portal_data.match_navigation(req.message)
    howto_topic = portal_data.match_howto(req.message)
    howto_intent = bool(portal_data._HOWTO_INTENT.search(req.message or ""))
    # Unambiguous lookups skip the model's tool-choosing round trip entirely,
    # which is roughly half the latency on a plain question.
    if third_party or advice or taxq:
        howto_topic = None if third_party else howto_topic
        howto_intent = False if third_party else howto_intent
    data_hit = None
    if not third_party and not advice and not taxq and not nav_tab and not howto_topic and not howto_intent:
        data_hit = portal_data.match_data_query(req.message, date.today().year)
    hard = (not third_party and not advice and not taxq and not nav_tab
            and not howto_topic and not howto_intent and not data_hit
            and portal_data.is_hard(req.message))

    async def stream():
        t0 = time.time()
        emitted = 0
        try:
            if third_party:
                msg = ("I can only see %s's information, so I cannot tell you anything "
                       "about %s. If you think you should have access to another "
                       "person's records, %s can sort that out with you."
                       % (CLIENTS[client_id]["name"], third_party, CLIENTS[client_id]["advisor"]))
                yield sse({"type": "token", "text": msg})
                yield sse({"type": "done", "ms": int((time.time() - t0) * 1000)})
                return

            if advice or taxq:
                kind = "tax" if taxq else "advisor"
                who = "your BrookHaven tax team" if taxq else CLIENTS[client_id]["advisor"]
                tools.execute(client_id, "escalate_to_advisor",
                              {"topic": ("TAX: " if taxq else "") + req.message[:280]})
                yield sse({"type": "tool", "name": "escalate_to_advisor",
                           "args": {"topic": req.message[:120]}})
                what = "tax planning" if taxq else "investment"
                yield sse({"type": "token", "text":
                    ("That one crosses into %s advice, and I am just the assistant here, "
                     "so I will not weigh in. I have passed your question to %s so it is "
                     "already on their radar. Would you like to schedule a call? Pick a "
                     "time below and I will put the request in.") % (what, who)})
                yield sse({"type": "schedule", "advisor_type": kind, "who": who,
                           "topic": req.message[:140], "slots": proposed_slots()})
                yield sse({"type": "done", "ms": int((time.time() - t0) * 1000),
                           "instant": True})
                return

            elif nav_tab:
                result = tools.execute(client_id, "navigate_to", {"tab": nav_tab})
                yield sse({"type": "tool", "name": "navigate_to", "args": {"tab": nav_tab}})
                if isinstance(result.get("open"), dict):
                    # navigate = the UI switches tabs right now; the button
                    # stays in the transcript for finding the page again later.
                    yield sse({"type": "navigate", **result["open"]})
                    yield sse({"type": "link", **result["open"]})
                yield sse({"type": "token", "text":
                    "Taking you there now. The button below will bring you back any time."})
                yield sse({"type": "done", "ms": int((time.time() - t0) * 1000),
                           "instant": True})
                return

            elif howto_topic:
                result = tools.execute(client_id, "get_howto", {"topic": howto_topic})
                yield sse({"type": "tool", "name": "get_howto", "args": {"topic": howto_topic}})
                # Steps are fixed data, so they are sent verbatim rather than
                # retyped by the model, which shortened or dropped them whenever
                # it had a second tool result to juggle.
                if result.get("steps"):
                    yield sse({"type": "steps", "title": result.get("title"),
                               "steps": result["steps"], "note": result.get("note")})
                if isinstance(result.get("open"), dict):
                    yield sse({"type": "navigate", **result["open"]})
                    yield sse({"type": "link", **result["open"]})
                # The intro sentence is derivable from the how-to title, and the
                # steps and button are already rendered. No model needed at all.
                title = (result.get("title") or "do that").lower()
                text = "Here is how to %s. I am taking you to the right place now." % title
                if big and howto_topic in ("withdrawal", "contribution"):
                    tools.execute(client_id, "escalate_to_advisor",
                                  {"topic": "Large amount (%s): %s" % (big, req.message[:200])})
                    yield sse({"type": "tool", "name": "escalate_to_advisor",
                               "args": {"topic": "large amount"}})
                    text += (" Because of the amount involved, I have also looped in %s."
                             % CLIENTS[client_id]["advisor"])
                yield sse({"type": "token", "text": text})
                yield sse({"type": "done", "ms": int((time.time() - t0) * 1000),
                           "instant": True})
                return
            elif data_hit:
                dname, dargs = data_hit
                result = tools.execute(client_id, dname, dargs)
                yield sse({"type": "tool", "name": dname, "args": dargs})
                if isinstance(result, dict) and isinstance(result.get("open"), dict):
                    yield sse({"type": "link", **result["open"]})
                # Canonical question + clean data: the server writes the answer
                # itself. No model, so it is instant and fully concurrent.
                text = instant.render(dname, dargs, result, CLIENTS[client_id])
                if text:
                    yield sse({"type": "token", "text": text})
                    yield sse({"type": "done", "ms": int((time.time() - t0) * 1000),
                               "instant": True})
                    return
                messages.append({"role": "assistant", "content": "", "tool_calls": [
                    {"function": {"name": dname, "arguments": dargs}}]})
                messages.append({"role": "tool", "name": dname,
                                 "content": json.dumps(result)})

            elif howto_intent:
                # Reads like a how-to but matched no topic. Escalate in code: asking
                # the model to do it produced answers that PROMISED a follow-up
                # without ever creating one, which is worse than not offering.
                esc = tools.execute(client_id, "escalate_to_advisor",
                                    {"topic": req.message[:300]})
                yield sse({"type": "tool", "name": "escalate_to_advisor",
                           "args": {"topic": req.message[:120]}})
                messages.append({"role": "assistant", "content": "", "tool_calls": [
                    {"function": {"name": "escalate_to_advisor",
                                  "arguments": {"topic": req.message[:300]}}}]})
                messages.append({"role": "tool", "name": "escalate_to_advisor",
                                 "content": json.dumps(esc)})
                messages.append({"role": "system", "content":
                    "You have no instructions on file for what the client just asked. You "
                    "do NOT know the steps, so do not invent them and do not describe any "
                    "tab, form, or button. It has already been sent to their advisor. Say "
                    "briefly that you do not have steps for that one and that their advisor "
                    "will follow up."})

            async with httpx.AsyncClient(timeout=180) as http:
                for hop in range(MAX_HOPS):
                    use_strong = hard and HARD_MODE == "strong" and STRONG
                    payload = {
                        "model": STRONG if use_strong else MODEL,
                        "messages": messages,
                        "stream": True,
                        "think": bool(hard and HARD_MODE == "think"),
                        "options": {"temperature": 0.3, "num_ctx": 8192},
                    }
                    # Last hop: drop the tools so the model is forced to answer.
                    if hop < MAX_HOPS - 1:
                        payload["tools"] = tools.TOOL_SCHEMAS

                    calls, buf = [], ""
                    async with http.stream("POST", f"{OLLAMA}/api/chat", json=payload) as r:
                        if r.status_code != 200:
                            body = (await r.aread()).decode()[:200]
                            yield sse({"type": "error", "text": f"Model host said {r.status_code}: {body}"})
                            return
                        async for line in r.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            msg = chunk.get("message") or {}
                            if msg.get("tool_calls"):
                                calls.extend(msg["tool_calls"])
                            piece = msg.get("content") or ""
                            if piece:
                                buf += piece
                                clean = _visible(buf)
                                if len(clean) > emitted:
                                    yield sse({"type": "token", "text": clean[emitted:]})
                                    emitted = len(clean)
                            if chunk.get("done"):
                                break
                    # flush anything held back by the unclosed-marker guard
                    clean = _visible(buf, final=True)
                    if len(clean) > emitted:
                        yield sse({"type": "token", "text": clean[emitted:]})
                        emitted = len(clean)

                    if not calls:
                        break

                    # Model asked for data. Run it against THIS session's client only.
                    messages.append({"role": "assistant", "content": buf, "tool_calls": calls})
                    for call in calls:
                        fn = call.get("function", {})
                        name = fn.get("name", "")
                        args = fn.get("arguments", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}
                        yield sse({"type": "tool", "name": name, "args": args})
                        result = tools.execute(client_id, name, args)
                        # The destination comes from the tool, never from the model,
                        # so Brooke cannot send a client to a page that does not exist.
                        if isinstance(result, dict) and isinstance(result.get("open"), dict):
                            yield sse({"type": "navigate", **result["open"]})
                            yield sse({"type": "link", **result["open"]})
                        # Even when the MODEL chose get_howto, steps render from
                        # data and a large amount still loops in the advisor.
                        if name == "get_howto" and isinstance(result, dict) and result.get("steps"):
                            yield sse({"type": "steps", "title": result.get("title"),
                                       "steps": result["steps"], "note": result.get("note")})
                            if big and args.get("topic") in ("withdrawal", "contribution"):
                                tools.execute(client_id, "escalate_to_advisor",
                                              {"topic": "Large amount (%s): %s" % (big, req.message[:200])})
                                yield sse({"type": "tool", "name": "escalate_to_advisor",
                                           "args": {"topic": "large amount"}})
                        messages.append({"role": "tool", "name": name,
                                         "content": json.dumps(result)})
                    yield sse({"type": "status", "text": "Checking your records"})

            yield sse({"type": "done", "ms": int((time.time() - t0) * 1000)})

        except httpx.ConnectError:
            yield sse({"type": "error", "text": "Cannot reach the model host. Is Ollama running?"})
        except Exception as e:
            yield sse({"type": "error", "text": f"{type(e).__name__}: {e}"})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
