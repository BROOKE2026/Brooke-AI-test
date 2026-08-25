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

import os, json, time, secrets, asyncio, re
from datetime import date
from collections import defaultdict

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import tools
from demo_data import PASSCODES, CLIENTS

OLLAMA   = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL    = os.environ.get("BROOKE_MODEL", "qwen3:14b")
MAX_HOPS = 4                      # tool-call rounds before we force an answer
RATE_N, RATE_WINDOW = 20, 60      # requests per token per minute

SYSTEM_PROMPT = """You are Brooke, the client assistant for BrookHaven.

Today is {today}. The current year is {year}, so "last year" means {last_year} and
"this year" means {year}. Always resolve relative dates against today's date, never
against your own assumptions about what year it is.

You are speaking with {name}, a client since {since}. Their advisor is {advisor}.

HOW YOU WORK
- Every number you state about this client must come from a tool call you just made. If you have not called a tool, you do not know the figure. Never estimate, recall, or infer a client's numbers.
- Call tools before answering questions about tax returns, accounts, holdings, documents, or meetings. Do not ask permission first, just retrieve it.
- If a tool returns an error or no data, say so plainly and say what is available instead.

WHAT YOU DO NOT DO
- You do not give investment, tax, or financial advice.
- When a client asks whether to buy, sell, rebalance, contribute, withdraw, or change strategy, or asks "should I", "what do you think", or "would you recommend", you do NOT answer it and you do NOT decline it in your own words. You CALL escalate_to_advisor first, and only then tell the client you have passed it to their advisor. Declining without calling the tool is a failure, because the advisor never finds out they were asked.
- You do not discuss any person other than {name}. You have no access to anyone else's records. If asked about another person or an account that is not theirs, say you can only see their own information.

VOICE
- Warm, direct, professional. You work for a wealth management firm and you sound like it.
- Brief. Two or three sentences unless they asked for a list.
- Format currency readably, like $412,800.
- Refer to the advisor by name ("Jacob Chandler will follow up"). Never use he/she/his/her for the advisor, since you have not been told their pronouns.
- Never use em dashes. Use commas, periods, or parentheses instead.
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


def resolve(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not signed in")
    tok = authorization[7:]
    s = SESSIONS.get(tok)
    if not s or time.time() - s["created"] > SESSION_TTL:
        SESSIONS.pop(tok, None)
        raise HTTPException(401, "Session expired, please sign in again")
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


@app.post("/api/logout")
async def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        SESSIONS.pop(authorization[7:], None)
    return {"ok": True}


# ------------------------------------------------------------- chat stream ---

def sse(obj):
    return f"data: {json.dumps(obj)}\n\n"


THINK = re.compile(r"<think>.*?</think>", re.S)


@app.post("/api/chat")
async def chat(req: ChatReq, authorization: str = Header(None)):
    client_id = resolve(authorization)

    messages = [{"role": "system", "content": build_system(client_id)}]
    for m in req.history[-12:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": req.message})

    async def stream():
        t0 = time.time()
        emitted = 0
        try:
            async with httpx.AsyncClient(timeout=180) as http:
                for hop in range(MAX_HOPS):
                    payload = {
                        "model": MODEL,
                        "messages": messages,
                        "stream": True,
                        "think": False,
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
                                clean = THINK.sub("", buf)
                                if len(clean) > emitted:
                                    yield sse({"type": "token", "text": clean[emitted:]})
                                    emitted = len(clean)
                            if chunk.get("done"):
                                break

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
