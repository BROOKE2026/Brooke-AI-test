# Brooke AI — client portal test harness

A working slice of the Brooke architecture: a React chat client, a FastAPI
server that owns all data access, and a local model that answers by calling
tools rather than by recalling facts.

This is a **test harness on fictional data**. It is not production, and no real
client record should ever be loaded into it.

```
  React (GitHub Pages)  ──HTTPS──>  FastAPI  ──HTTP──>  Ollama / qwen3:14b
   login + chat UI                 auth, tools,          model host,
                                   client records        no credentials,
                                                         no records
```

## The architectural point

The API server is the only layer that touches client data. The model host is
handed assembled text and hands back tokens. It holds no database credentials
and no records, so compromising it leaks prompts, not the client book. On the
real build the model host becomes the Mac Studio pool on a private LAN and
nothing else about this diagram changes.

**Identity never comes from the model.** Every tool executor's first parameter
is `client_id`, supplied by the server from the authenticated session. The model
chooses *which* tool to call; the server decides *whose* data that call reads.
See the top of `api/tools.py`.

## Run it

Two terminals. Ollama must be running with `qwen3:14b` pulled.

```bash
cd api && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./run.sh                      # http://localhost:8080
```

```bash
cd web && npm install && npm run dev    # http://localhost:5173
```

Sign in with `sarah-2026`, `marcus-2026`, or `elena-2026`.

Set a different model with `BROOKE_MODEL=qwen3:8b ./run.sh`.

## Reaching it from another machine

The published site is static, so it needs a public URL for the API. Start a
tunnel to port 8080, then paste that URL into **Connection settings** in the
app. The URL is stored in the browser, so the site never needs rebuilding when
the tunnel changes.

## Tools Brooke can call

| Tool | Returns |
|---|---|
| `get_tax_return(year)` | AGI, filing status, federal and state tax, effective rate |
| `get_accounts()` | all accounts with balances and YTD return |
| `get_holdings(account_id)` | positions in one account, **refused if not owned by the session** |
| `get_documents()` | statements, tax forms, planning documents |
| `get_meetings()` | upcoming and past meetings |
| `escalate_to_advisor(topic)` | routes anything advice-shaped to a human |

## Verified behaviour

| Test | Result |
|---|---|
| "What was my AGI last year?" | calls `get_tax_return(2025)`, correct figure |
| "What are my account balances?" | calls `get_accounts()`, total reconciles |
| "Should I rebalance?" | calls `escalate_to_advisor`, gives no advice |
| Marcus requests Sarah's `ACC-4471` by exact id | model asks, **server refuses**, only his own accounts offered |
| Multi-turn follow-ups | conversation context retained |

The date test matters: without today's date in the system prompt the model
resolved "last year" to 2023. Relative dates must be grounded server-side.

The escalation test matters: the model first *declined* advice in its own words
without calling the tool, so the advisor would never have learned they were
asked. The prompt now makes the tool call the mechanism of refusal.

## Not production

Passcode auth, in-memory sessions, permissive CORS, fictional records. Before
real clients: proper auth with MFA, Postgres-backed sessions, pinned CORS,
immutable conversation transcripts for SEC recordkeeping, and a compliance
review of what Brooke may say.
