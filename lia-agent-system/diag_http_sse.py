"""Measure the FULL HTTP SSE pipeline (ASGI + middleware + drain loop) end-to-end.
If frames arrive spread over seconds -> pipeline streams; if all at ~same offset
-> pipeline bunches (the real root cause to fix)."""
import asyncio
import json
import time

import httpx

from app.auth.security import create_access_token

OUT = "/tmp/diag_http_result.txt"
TOKEN = create_access_token(
    subject="13cf82fb-f1f6-4205-9377-758e59040148",
    role="admin",
    company_id="00000000-0000-4000-a000-000000000001",
)
SESSION = "lia-httpprobe-1"
URL = f"http://127.0.0.1:8001/api/v1/chat/{SESSION}/stream"
BODY = {
    "message": "Explique em 2 frases o que e fit cultural.",
    "domain": "recruiter_assistant",
    "context": {},
    "conversation_id": SESSION,
}


async def main():
    lines = []
    t0 = time.monotonic()
    counts = {}
    first = {}
    last = {}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", URL, json=BODY,
                headers={"Authorization": f"Bearer {TOKEN}", "Accept": "text/event-stream"},
            ) as resp:
                lines.append(f"HTTP {resp.status_code}")
                async for raw in resp.aiter_lines():
                    if not raw.startswith("data: "):
                        continue
                    dt = time.monotonic() - t0
                    try:
                        ty = json.loads(raw[6:]).get("type", "?")
                    except Exception:
                        ty = "?"
                    counts[ty] = counts.get(ty, 0) + 1
                    first.setdefault(ty, dt)
                    last[ty] = dt
    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")
    for ty in counts:
        span = last[ty] - first[ty]
        lines.append(f"{ty}: n={counts[ty]} first=+{first[ty]:.2f}s last=+{last[ty]:.2f}s span={span:.2f}s")
    lines.append("VERDICT: token span >1s => pipeline streams; ~0 => pipeline BUNCHES")
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("DONE")


asyncio.run(main())
