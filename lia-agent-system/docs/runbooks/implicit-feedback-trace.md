# Implicit Feedback Capture — End-to-End Trace (Task #1299)

Explicit feedback (Task #1297: 👍/👎, star rating, inline correction) is rare —
most recruiters never click it. Task #1299 multiplies the learning-loop volume
by harvesting **three implicit signals** from natural chat behaviour and routing
them through the **same storage + learning path** as explicit feedback.

| Signal | Strength | Where detected | Writes `learning_signals` | Demotes `learning_patterns` |
|---|---|---|---|---|
| `regeneration` | strong negative | backend (`/regenerate`) | ✅ `domain=implicit_regeneration` | ✅ |
| `correction_delta` | negative | frontend → `/feedback/implicit` | ✅ `domain=implicit_correction_delta` | ✅ |
| `abandonment` | weak negative | frontend → `/feedback/implicit` | ✅ `domain=implicit_abandonment` | ❌ (signals only) |

Every signal carries `intent` / `stage` / `trace_id` + the **real `company_id`
from the JWT** (never the request body), and is gated by **FairnessGuard
(fail-closed)** before it can become a learned pattern.

Canonical code:
- `app/shared/learning/implicit_feedback_service.py` — `ImplicitFeedbackService`
  (3 capture methods, FairnessGuard gate, `is_abandonment_candidate` pure
  criterion, dual persistence).
- `app/domains/analytics/services/feedback_service.py` —
  `record_implicit_negative` + `_update_patterns_from_feedback` transient
  `_implicit_negative` marker (negative WITHOUT touching thumbs/rating metrics).
- `app/api/v1/lia_feedback.py` — `/regenerate` hook + `POST /feedback/implicit`.
- `plataforma-lia/src/components/unified-chat/implicit-feedback-detect.ts` —
  client classifier; `feedback-api.ts::reportImplicitSignal`; `UnifiedChat.tsx`
  send-time hook (gated on `!dynamicPanel` ⇒ outside the wizard).

---

## Trace 1 — `regeneration` (strong negative, server-side)

1. Recruiter clicks **"Gerar novamente"** on a LIA message.
2. Frontend `UnifiedChat.handleRegenerate` → `POST /api/v1/lia/feedback/regenerate
   { session_id, message_id }`.
3. Endpoint validates ownership, stamps the assistant row `regenerated=true`,
   audits `regenerate_requested`.
4. **Hook (defensive try/except — never breaks the handshake):**
   `implicit_feedback_service.capture_regeneration(...)` with
   `superseded_response` = the message content, `prior_user_message` = the user
   turn it answered, `intent/stage/trace_id/confidence` from `extra_data`.
5. FairnessGuard checks both texts. If blocked → `persisted=False`, nothing
   stored (warning logged). Otherwise:
   - `learning_signals` row: `domain=implicit_regeneration`,
     `feedback_type=regeneration`, `original_response`=superseded answer,
     `corrected_response`=prior user message, `metadata.signal_source=implicit`,
     `metadata.regenerate_of=<message_id>`.
   - `record_implicit_negative(...)` → `interaction_feedback` row
     (`feedback_category=implicit_regeneration`, NO thumbs/rating) →
     `_update_patterns_from_feedback` increments the matching
     `LearningPattern.negative_feedback_count` and appends to
     `example_bad_responses`.
6. The `/regenerate` response returns to the client unchanged; the chat
   re-invokes the prior user message.

## Trace 2 — `correction_delta` (negative, frontend-detected)

1. LIA answers. The recruiter's **next** message strongly reuses that answer but
   edits it (token overlap ≥ `CORRECTION_OVERLAP_MIN`, not identical).
2. `UnifiedChat.handleSend` (only when `!dynamicPanel` ⇒ outside the wizard)
   calls `classifyImplicitSignal(priorLia.content, text)` → `correction_delta`.
3. `reportImplicitSignal('correction_delta', …)` → `POST /api/v1/lia/feedback/implicit
   { signal_type:'correction_delta', message_id, original_response, used_text }`.
   Fire-and-forget: a failure never blocks the send.
4. Endpoint derives `company_id`/`user_id` from the JWT (IDOR-safe) and calls
   `capture_correction_delta(...)`.
5. No-op guards: `original == used` → `skipped_reason=no_delta`; empty used text
   → `empty_used_text`. FairnessGuard gate as above.
6. Persists `learning_signals` (`domain=implicit_correction_delta`,
   `corrected_response`=the edited text the recruiter actually used) **and** the
   negative pattern path via `record_implicit_negative`.
7. Response: `{ persisted, signal_type, signal_id, skipped_reason }`.
   `persisted=False` + reason is a NORMAL outcome, not an error.

## Trace 3 — `abandonment` (weak negative, frontend-detected)

1. LIA gives a substantive answer. The recruiter ignores it and sends an
   unrelated message (topic switch).
2. `UnifiedChat.handleSend` → `classifyImplicitSignal(...)` → `abandonment`
   (client pre-filter mirrors the backend criterion to avoid noisy POSTs).
3. `reportImplicitSignal('abandonment', …)` → `POST /feedback/implicit
   { signal_type:'abandonment', message_id, abandoned_response, next_user_message }`.
4. Endpoint → `capture_abandonment(...)`. **Authoritative conservative gate:**
   - `is_abandonment_candidate(...)` (answer ≥ 60 chars, did not end in `?`,
     next msg ≥ 4 words and not a PT-BR continuation token, topic overlap ≤ 0.08)
     → else `skipped_reason=criterion_not_met`.
   - `_has_explicit_engagement(...)` — if the turn already has explicit feedback,
     `skipped_reason=turn_engaged` (an engaged turn is not abandoned).
   - FairnessGuard gate.
5. Persists **`learning_signals` ONLY** (`domain=implicit_abandonment`,
   `signal_strength=weak_negative`). It deliberately **never** touches
   `learning_patterns` — a single ignored answer must not flip a pattern.

---

## Why these design choices

- **Same tables/service as explicit feedback** — the downstream golden-dataset /
  eval-gate task (planned separately) reads one store; implicit rows are
  namespaced by `domain=implicit_*` and `feedback_category=implicit_*` so they
  never get mistaken for positive examples and explicit satisfaction metrics
  (thumbs/rating) stay clean.
- **FairnessGuard before pattern** — implicit signals are unsupervised; gating
  fail-closed prevents biased candidate text from silently becoming a learned
  pattern (LGPD / EU AI Act).
- **`company_id` from JWT** — never trusts the request body (IDOR / tenant
  isolation).
- **No silent fallbacks** — every skip path returns an explicit
  `skipped_reason`; the regenerate hook logs (does not swallow blindly) and only
  wraps to protect the user-facing handshake.
- **Conservative abandonment** — a missed signal is far cheaper than a false
  positive that teaches LIA the wrong lesson, so the criterion is strict and
  `learning_patterns` is never touched for this type.

## Tests / sentinels

- Backend unit/offline: `tests/unit/test_implicit_feedback_service.py`
  (abandonment criterion, fail-closed FairnessGuard gate, capture-method
  contract, pre-DB short-circuits).
- Contract sensor: `tests/contract/test_lia_feedback_contract.py`
  (`/feedback/implicit` in `_EXPECTED_PATHS`).
- Frontend: `plataforma-lia/src/components/unified-chat/__tests__/implicit-feedback-detect.test.ts`.
- DB-backed behaviour reuses the existing `learning_signals` repository
  integration suite (skips without `DATABASE_URL`).
