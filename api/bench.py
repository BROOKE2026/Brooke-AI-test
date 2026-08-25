"""
Concurrency and latency benchmark for the Brooke API.

Fires N simultaneous conversations and reports, per request:
  TTFT  time to first visible token, what the client perceives as "it started"
  TOTAL time to the final token
plus aggregate tokens/sec across all streams.

Usage:
  ./.venv/bin/python bench.py                  # 1,2,4,8 concurrent
  ./.venv/bin/python bench.py 1 4 16           # explicit levels
  BROOKE_API=https://x.trycloudflare.com ./.venv/bin/python bench.py
"""
import os, sys, json, time, asyncio, statistics
import httpx

API = os.environ.get("BROOKE_API", "http://localhost:8080")
PASSCODES = ["sarah-2026", "marcus-2026", "elena-2026"]

# Mix of shapes: a routed how-to, a one-tool lookup, a multi-tool lookup.
QUESTIONS = [
    "What are my account balances?",
    "What was my AGI last year?",
    "How do I change my beneficiaries?",
    "What documents do I have on file?",
    "When is my next meeting?",
    "What are my advisory fees?",
]


async def one(client, idx):
    pc = PASSCODES[idx % len(PASSCODES)]
    q = QUESTIONS[idx % len(QUESTIONS)]
    r = await client.post(f"{API}/api/login", json={"passcode": pc}, timeout=30)
    tok = r.json()["token"]

    t0 = time.perf_counter()
    ttft, chars, err = None, 0, None
    async with client.stream("POST", f"{API}/api/chat",
                             headers={"Authorization": f"Bearer {tok}"},
                             json={"message": q, "history": []},
                             timeout=600) as resp:
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            try:
                e = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if e.get("type") == "token":
                if ttft is None:
                    ttft = time.perf_counter() - t0
                chars += len(e["text"])
            elif e.get("type") == "error":
                err = e["text"]
    return {"q": q, "ttft": ttft, "total": time.perf_counter() - t0,
            "chars": chars, "err": err}


async def level(n):
    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()
        rows = await asyncio.gather(*[one(client, i) for i in range(n)])
        wall = time.perf_counter() - t0

    good = [r for r in rows if r["ttft"] is not None and not r["err"]]
    if not good:
        print(f"  n={n:<3} ALL FAILED: {rows[0].get('err')}")
        return
    ttfts = sorted(r["ttft"] for r in good)
    totals = sorted(r["total"] for r in good)
    chars = sum(r["chars"] for r in good)
    # ~4 chars per token is a good rule of thumb for English
    print("  n=%-3d ok=%d/%d  TTFT med %5.1fs p95 %5.1fs | TOTAL med %5.1fs max %5.1fs "
          "| wall %5.1fs | ~%4.0f tok/s aggregate"
          % (n, len(good), n,
             statistics.median(ttfts), ttfts[max(0, int(len(ttfts) * .95) - 1)],
             statistics.median(totals), max(totals), wall, (chars / 4) / wall))


async def main():
    levels = [int(a) for a in sys.argv[1:]] or [1, 2, 4, 8]
    h = httpx.get(f"{API}/api/health", timeout=20).json()
    print("API   %s" % API)
    print("model %s  (ollama_up=%s present=%s)\n" % (h["model"], h["ollama_up"], h["model_present"]))
    for n in levels:
        await level(n)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
