# LIA Agent System — API Reference

All HTTP and WebSocket endpoints exposed by the LIA Agent System are
mounted under the canonical `/api/v1` prefix. The reverse proxy,
authentication middleware, CORS rules, and rate-limit policies all key
off this prefix — endpoints outside `/api/v1` are considered legacy or
internal-only.

## Conventions

- **Base URL (HTTP):** `https://<host>/api/v1`
- **Base URL (WebSocket):** `wss://<host>/api/v1`
- **Auth:** `Authorization: Bearer <jwt>` header for HTTP; `?token=<jwt>`
  query parameter for WebSocket (browsers cannot set custom headers on
  WS upgrades).
- **Versioning:** All public endpoints live under `/api/v1`. Future
  breaking changes will be exposed under a new prefix (`/api/v2`, …).

## Chat — real-time

| Channel | Method | Path | Description |
|---|---|---|---|
| Primary | `WS` | `/api/v1/ws/chat/{session_id}` | Bidirectional chat WebSocket. Token via `?token=`. Domain via `?domain=`. |
| Fallback | `GET (SSE)` | `/api/v1/chat/{session_id}/stream` | Server-Sent Events fallback when the WS handshake is blocked. |
| Send | `POST` | `/api/v1/chat/message` | One-shot REST send used by the SSE fallback flow. |

> **Audit note (Task #319 / W17 + W2 — 2026-04-17):** the chat WebSocket
> was previously mounted at the bare root `/ws/chat/{session_id}`, which
> bypassed the auth middleware/CORS/rate-limit rules attached to the
> `/api/v1` prefix. It now lives at `/api/v1/ws/chat/{session_id}`.
> Backend mount: `app.api.routes.register_routes` →
> `app.include_router(agent_chat_ws_router, prefix="/api/v1")`.

### Connect example

```ts
const url = `${WS_BASE_URL}/api/v1/ws/chat/${sessionId}?token=${jwt}` +
            `&domain=recruiter_assistant`;
const ws = new WebSocket(url);
```

## Other surface areas

For the full inventory of HTTP endpoints (jobs, candidates, screening,
WSI, agents, compliance, …) see the live OpenAPI document served at
`/api/v1/openapi.json` and the rendered docs at `/api/v1/docs`.
