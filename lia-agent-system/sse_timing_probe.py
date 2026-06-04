"""Localize SSE buffering: hit the BACKEND directly (localhost:8001) and record
the wall-clock arrival time of each SSE frame. Incremental arrival => backend
streams fine (buffer is downstream: Next proxy / Replit infra). All-at-once =>
backend buffers."""
import asyncio
import time

import httpx

from app.auth.security import create_access_token

TOKEN = create_access_token(
    subject="13cf82fb-f1f6-4205-9377-758e59040148",
    role="admin",
    company_id="00000000-0000-4000-a000-000000000001",
)
SESSION = "lia-probe-session-1"
URL = f"http://127.0.0.1:8001/api/v1/chat/{SESSION}/stream"
BODY = {
    "message": "Liste 3 dicas rápidas para uma boa descrição de vaga.",
    "domain": "recruiter_assistant",
    "context": {},
    "conversation_id": SESSION,
}
OUT = "/tmp/sse_timing_result.txt"


async def main():
    lines = []
    t0 = time.monotonic()
    n_token = 0
    first_token_at = None
    last_token_at = None
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                URL,
                json=BODY,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Accept": "text/event-stream",
                },
            ) as resp:
                lines.append(f"HTTP {resp.status_code}")
                async for raw in resp.aiter_lines():
                    if not raw.startswith("data: "):
                        continue
                    dt = time.monotonic() - t0
                    payload = raw[6:]
                    etype = ""
                    try:
                        import json

                        etype = json.loads(payload).get("type", "?")
                    except Exception:
                        etype = "(parse-fail)"
                    if etype == "token":
                        n_token += 1
                        if first_token_at is None:
                            first_token_at = dt
                        last_token_at = dt
                        # only log every 10th token to keep file small
                        if n_token % 10 == 1:
                            lines.append(f"[{dt:6.2f}s] token #{n_token}")
                    else:
                        lines.append(f"[{dt:6.2f}s] {etype}")
    except Exception as exc:  # noqa
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")

    lines.append("")
    lines.append(f"total_tokens={n_token}")
    lines.append(f"first_token_at={first_token_at}")
    lines.append(f"last_token_at={last_token_at}")
    if first_token_at is not None and last_token_at is not None:
        span = last_token_at - first_token_at
        lines.append(f"token_span={span:.2f}s  (>0.5s => incremental; ~0 => burst)")
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("DONE ->", OUT)


asyncio.run(main())
