# PLAN — WebSocket Realtime Voice Credit Gate (2026-05-22)

Canonical decision log for `RealtimeCreditSession` defaults + bug fixes.
Updated 2026-05-22 — Paulo approved 4 decisions + 1 P0 bug fix.

Source of truth file: `app/domains/voice/services/realtime_credit_session.py`
Companion provider: `app/shared/providers/voice_openai_realtime.py`
Companion sensor: `scripts/check_realtime_uses_canonical_model.py`

---

## Critical bug fixed first (P0)

### B1. OPENAI_REALTIME_MODEL was deprecated — Implemented 2026-05-22 ✅

**Symptom risk:** any Realtime voice session would 404 / model_not_found
once OpenAI's runtime removes the deprecated alias. Possibly already failing
silently in production (no canary metric tracking provider 4xx).

**Root cause:** `app/shared/providers/voice_openai_realtime.py:26` set
`OPENAI_REALTIME_MODEL = "gpt-4o-realtime-preview"` — DEPRECATED by OpenAI
on 2026-05-12. The preview model alias was scheduled for removal.

**Fix:** literal replaced with canonical `gpt-realtime` (GA since 2025-09-08).
Documentation block above the constant cites the deprecation date + names
the supported successor (`gpt-realtime-2` ~20% cheaper alternative).

**Sensor:** `scripts/check_realtime_uses_canonical_model.py` (BLOCKING,
baseline 0). Detects deprecated literal anywhere under `app/` outside of
comment lines. Companion contract test:
`tests/contract/test_voice_openai_realtime_model.py`.

Commit: `0124d8529`

---

## Decisions (Q1–Q6)

### Q1. BYOK strategy — STILL PENDING ANDERSON

When tenant brings their own OpenAI API key, do WeDOTalent credits still
apply, or is BYOK = unmetered? Current default: credits still gate
(defense-in-depth against accidental free-tier abuse). Hard decision
awaits Anderson sign-off. No code change yet.

### Q2. SDK vs raw WebSocket — DEFERRED

Provider uses raw `websockets` lib; OpenAI Python SDK 1.30+ added
`openai.AsyncOpenAI().beta.realtime`. Migration would unify retries /
circuit-breaker patterns, but SDK is still beta as of 2026-05-22.
Revisit when SDK leaves beta.

### Q3. Audio cost multiplier — Implemented 2026-05-22 ✅

**Decision:** `_REALTIME_AUDIO_MULTIPLIER = 3.5` (was 2.0).

**Pricing math (verified 2026-05-22):**
- OpenAI Realtime input audio:  $32/1M tokens → 10.67× Claude $3/M baseline
- OpenAI Realtime output audio: $64/1M tokens → 21.33× Claude $3/M baseline
- Blended ~50/50 in/out mix: ~16× raw, conservatively damped to 3.5×
  because credit ledger uses Whisper token-eq (already inflated baseline).

**Impact:** 2.0× under-charged tenants ~75% on every session, leaking
margin. 3.5× restores correct cost recovery without over-charging.

**Sensor:** `tests/contract/test_realtime_credit_session.py::test_multiplier_is_3_5x_canonical`
pins the value with a regression-resistant assertion message.

Commit: `056889ef7`

### Q4. Min session buffer — Implemented 2026-05-22 ✅

**Decision:** `_MIN_SESSION_BUFFER = 1500` (was 1000).

Buffer covers ~2 typical 30s turns instead of 1. Avoids the edge case
where one turn finishes the buffer but the next one starts mid-flight
and burns into negative ledger.

**Sensor:** `test_min_session_buffer_is_1500` + `test_session_buffer_covers_2_typical_turns`
(sanity bounds: between half-turn and 2-turns).

Commit: `056889ef7`

### Q5. Dual timeout — Implemented 2026-05-22 ✅

**Decision:** Replace single 600s idle timeout with TWO orthogonal limits:
- `_IDLE_TIMEOUT_SEC = 120` — 2 min without any event = orphan WS detection
- `_HARD_CAP_SEC = 1800` — 30 min absolute, force-close even with activity

**Rationale:**
- **120s idle** is tighter than 600s — most real conversations have an
  event at least every 30s. 600s was too lenient and let truly orphaned
  WS connections (browser crash, network drop) burn budget for 10 minutes.
- **1800s hard cap** is the belt against heartbeat-only abuse: malicious
  client emits empty events every 60s to game the idle timer. Hard cap
  forces close regardless.
- **Old 600s default cut WSI 45-min screenings prematurely.** The new
  dual approach allows the full 30-min window with no idle-cut, and
  expects long interviews (45-60min) to split client-side into multiple
  sessions.

**API:** `is_inactive()` returns True if either condition trips.
`inactive_reason()` returns `"idle_timeout"` | `"hard_cap"` | `None` for
telemetry distinction.

**Sensor:** `test_idle_timeout_is_120_seconds`,
`test_hard_cap_is_1800_seconds`, `test_inactive_reason_returns_idle_when_no_events`,
`test_inactive_reason_returns_hard_cap_when_over_30min`,
`test_dual_timeout_idle_takes_precedence_when_both_exceeded`.

Commit: `056889ef7`

### Q6. Concurrent sessions per tenant — Implemented 2026-05-22 ✅

**Decision:** `_CONCURRENT_PER_TENANT_DEFAULT = 5` (was unlimited),
`_CONCURRENT_PER_TENANT_MAX = 50` (admin override ceiling).

**Implementation:** Redis-backed atomic counter at key
`realtime_sessions_active:<company_id>`. INCR + EXPIRE in a transaction
pipeline during `pre_session_check`; DECR in `close()`. TTL =
`_HARD_CAP_SEC + 60s` so the counter self-heals if a close() path is
missed (pod crash, network partition).

**Worst-case budget burn:**
- At cap (5 sessions × ~$0.90/min) ≈ **$4.50/min/tenant**
- 100 tenants simultaneously at cap = $450/min platform-wide (recoverable
  via credit ledger)
- Without cap (uncapped 100 sessions) = $18/min/tenant = $1800/min/platform
  runaway risk

**Failure semantics (REGRA 4 — fail-loud):**
- Cap exceeded → `ConcurrentSessionLimitExceeded` raised in
  `pre_session_check`. Caller MUST translate to WS close code 4003 +
  structured reason. NEVER silent skip.
- Redis outage → fail-safe ALLOW (logs loud, continues without cap).
  Losing the cap is preferable to blocking all tenants when Redis is
  down; the credit gate still provides defense-in-depth.

**Slot release semantics:**
- Released in `close()` (normal path).
- Released in mid-session credit exhaust path (before raising
  `SessionShouldTerminate`).
- Released if credit gate raises AFTER slot acquired (would otherwise
  leak 5 zombie slots, blocking tenant forever until TTL).
- Idempotent on duplicate close (DECR only once via `_slot_acquired` flag).

**Sensor:** 6 contract tests covering all 4 release paths + cap behaviour:
- `test_concurrent_cap_blocks_6th_session_when_default_5`
- `test_concurrent_cap_allows_5th_session`
- `test_concurrent_slot_released_on_close`
- `test_concurrent_slot_released_on_credit_exhausted`
- `test_concurrent_count_resets_to_zero_if_negative`
- `test_concurrent_slot_release_idempotent_on_double_close`

Commit: `056889ef7`

---

## Open follow-ups (post-decision)

1. **Per-tenant cap override** — `_try_acquire_concurrent_slot` uses
   `_CONCURRENT_PER_TENANT_DEFAULT` as the literal. Enterprise tenants
   may need higher caps (up to `_CONCURRENT_PER_TENANT_MAX = 50`).
   Implementation: read override from `tenant_policies` table when the
   admin UI exposes it.

2. **Concurrent cap canary metric** — Add a Prometheus counter for
   `concurrent_cap_rejection_total{company_id_hash=...}` so we see
   when tenants are actually hitting the cap (signal: legitimate
   growth need or abuse pattern).

3. **Fallback rate canary (REGRA 4 sensor for the bigger pattern)** —
   `wsi_fallback_rate` metric proposed in CLAUDE.md REGRA 4 section
   would also surface "Realtime model 404" if it returned silently
   to a fallback path. Wire when WSI fallback metric is built.

4. **BYOK strategy decision** — Q1 still open. When tenant brings own
   API key, decide: credits still gate (current default) OR BYOK =
   unmetered. Doc-only change → code change once Anderson chooses.

5. **SDK migration** — Q2 deferred. Revisit when `openai-python` Realtime
   SDK leaves beta (currently 1.30+ beta).

---

## Test summary

`tests/contract/test_realtime_credit_session.py`: **30 tests green**
- 13 pre-existing (basics, pre-session, on_event, mid-exhaust, close)
- 7 new constant pins (multiplier, buffer, idle, hard cap, cap default, cap max, buffer/turn sanity)
- 4 new dual-timeout tests
- 6 new concurrent-cap tests

`tests/contract/test_voice_openai_realtime_model.py`: **2 tests green**
- canonical literal pin
- type sanity

`scripts/check_realtime_uses_canonical_model.py`: **baseline 0 violations**.

---

## Commit list (Replit-only, branch `feat/benefits-prv-canonical`)

| # | Hash | Subject |
|---|------|---------|
| 1 | `0124d8529` | fix(voice): canonical model gpt-realtime (B1 P0) |
| 2 | `056889ef7` | fix(voice): calibrate Realtime gate constants + concurrent cap (Q3+Q4+Q5+Q6) |
| 3 | `120a9054d` | test(contract): pin calibrated constants + dual timeout + concurrent cap (17 new tests) |
| 4 | `66ce1e238` | feat(sensor): block regression to deprecated gpt-4o-realtime-preview model |
