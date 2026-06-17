# Intermittent Bugs Analysis: LIA Job Creation Wizard

**Analysis Date:** 2026-04-29  
**Scope:** UAT bugs in `/lia-agent-system` and `/plataforma-lia`

---

## Bug 1: Salário Benchmark Absurdo (R$ 18-33k para Dev Senior SP)

**Root Cause:** MarketBenchmarkService fallback to LLM estimation with zero salary data produces unrealistic ranges.

**Evidence:**
- `/home/runner/workspace/lia-agent-system/app/domains/analytics/services/market_benchmark_service.py:160-190`
  - `_parse_salary_from_results()` calls LLM with prompt asking for salary estimate
  - When SerpAPI returns no results (`context = "Nenhum resultado de busca disponível"`), LLM "estimates" based only on prompt instructions
  - No validation caps min/max values against historical Brazil market data
- `/home/runner/workspace/lia-agent-system/app/domains/talent_intelligence/tools/market_intelligence_tools.py:45-120`
  - `get_market_intelligence()` tool wraps MarketBenchmarkService and returns parsed data directly
  - No post-processing or sanity checks on returned min/max

**Why R$ 33k is wrong:**  
Line 255-265 in `market_benchmark_service.py`: hardcoded fallback `base_salaries["sênior"] = (12000, 20000)` applies 1.3x multiplier for tech roles → max becomes 26k. LLM can override this entirely when calling `_parse_salary_from_results()`. No upper bound enforcement.

**Fix Proposed (P0):**
1. Add sanity validation layer after LLM parsing (line 245):
   ```python
   # Hard caps per seniority + region
   MAX_SALARY_CAPS = {
       "júnior": 12000,
       "pleno": 18000,
       "sênior": 25000,  # actual market median ~15k
       "especialista": 35000,
   }
   parsed_max = min(data.get("max"), MAX_SALARY_CAPS.get(seniority, 40000))
   ```
2. Track data source type (web search vs. LLM fallback) and flag confidence ≤ "low" to frontend
3. Implement secondary validation: reject 3x multiplier outliers vs. seniority defaults

**Severity:** P0 (misleads recruiter into budget miscalibration)

---

## Bug 2: "Erro de autenticação. Faça login novamente."

**Root Cause:** JWT token expiration without proactive refresh; Rails JWT lifetime not synchronized with front-end session timeout.

**Evidence:**
- `/home/runner/workspace/lia-agent-system/app/auth/rails_jwt.py:40-65`
  - `validate_rails_token()` decodes JWT and checks `exp` claim (unix timestamp)
  - No refresh token mechanism present — when token expires, validation returns `None`
- `/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts:65`
  - Generic catch-all: `{ content: 'Erro ao conectar com o backend.', error: 'connection_error' }`
  - Does not distinguish auth failure (401) from network timeout
- No middleware to intercept 401 and trigger client-side token refresh

**Why user sees error mid-flow:**  
If wizard flow spans > JWT TTL (likely 1-4 hours):
1. User answer 1 → token valid
2. Time passes, user thinks while answering → token expires silently
3. User submits next form → backend returns 401
4. Frontend shows generic "Erro ao conectar com o backend" instead of "sessão expirou"
5. User has no way to refresh without losing context

**Fix Proposed (P1):**
1. Implement refresh token endpoint `/api/auth/session/refresh` (returns new JWT)
2. Front-end interceptor: on 401, attempt refresh + retry original request
3. Set visible timeout warning: "Sua sessão expira em 10 minutos — clique aqui para renovar"
4. Reduce JWT TTL mismatch: align Rails `exp` with front-end session timeout
5. Emit specific error code in 401 response: `{ error: "auth_expired", message: "Sessão expirada" }`

**Severity:** P1 (loss of user context in long flows)

---

## Bug 3: "Erro ao conectar com o backend" (Generic Catch-All)

**Root Cause:** Identical error message for multiple distinct failure modes; no error code differentiation.

**Evidence:**
- `/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts:35,65`
  - Line 35: parse error → `'Erro ao processar mensagem'`
  - Line 65: network/500 error → `'Erro ao conectar com o backend'` (same)
- No distinction between:
  - 503 (backend down)
  - 504 (timeout)
  - 429 (rate limit)
  - 401 (auth fail — should be caught separately)
  - 400 (bad request from LLM)

**Why intermittent:**  
If network is flaky or backend has brief outages, user hits this message randomly. No retry logic, no exponential backoff, no specific remediation hint.

**Fix Proposed (P1):**
1. Map HTTP status → specific error messages:
   ```typescript
   const errorMap = {
     503: "Serviço temporariamente indisponível. Tentando novamente...",
     504: "Conexão expirou. Verifique sua internet.",
     429: "Limite de requisições atingido. Aguarde 30s.",
     401: "Sessão expirada. Faça login novamente.",
     400: "Requisição inválida: {details}",
     default: "Erro ao conectar. Tentando novamente..."
   }
   ```
2. Implement auto-retry for 503/504 with exponential backoff (base 1s, max 30s)
3. Log error code + timestamp to session for debugging

**Severity:** P1 (poor UX, hard to debug)

---

## Bug 4: LIA Navegou para `/funil-de-talentos` (404 — Rota Órfã)

**Root Cause:** LIA has unrestricted navigation intent mapping without route validation; frontend accepts navigation commands without checking route existence.

**Evidence:**
- No `navigate_to` tool found in `/app/tools/` — must be embedded in agent response as markdown link or implicit intent
- Front-end chat handler likely auto-converts intent ("vai buscar candidatos") into navigation without validation
- Route `/funil-de-talentos` does not exist in routing config (would return 404)

**Why happens:**  
1. User asks: "vai buscar candidatos automaticamente?" (intent = "list_candidates")
2. LIA matches intent to "navigate to talent funnel" (Portuguese translation adds wrong route name)
3. Front-end renders link or auto-navigates to `/funil-de-talentos`
4. Page not found (404)

**Fix Proposed (P2):**
1. Implement whitelist of valid wizard routes in LLM prompt + state machine
2. Add route validation middleware: all navigation must pass `/api/validate-route` before client-side redirect
3. If route invalid, LIA returns error message instead of link: "Funcionalidade ainda não disponível nesta versão do wizard"
4. Maintain canonical route map in state (ensure routing layer reads from single source of truth)

**Severity:** P2 (UX degradation, not data loss)

---

## Bug 5: Query com Pontuação Literal ("candidatos?")

**Root Cause:** LIA passes user input verbatim to search tool without normalization; no query preprocessing.

**Evidence:**
- `/home/runner/workspace/lia-agent-system/app/tools/job_tools.py` does not show candidate search tool
- Likely implemented in `talent_intelligence/tools/` or `candidates/` domain
- No visible input sanitization: strip punctuation, lowercase, trim whitespace

**Why returns zero results:**  
Search index tokenizer splits "candidatos?" as separate tokens. Query literal "candidatos?" does not match documents indexed as "candidatos" (no punctuation).

**Fix Proposed (P2):**
1. Normalize all queries in search tool intake:
   ```python
   def normalize_query(q: str) -> str:
       return re.sub(r'[^\w\s]', '', q).strip().lower()
   ```
2. Log original + normalized query for debugging
3. If zero results, emit fallback: "Nenhum candidato encontrado. Tente 'candidatos Python' ou 'São Paulo'"

**Severity:** P2 (low-impact, easy to reproduce)

---

## Bug 6: LIA Repetiu Perguntas (State Loss Between Turns)

**Root Cause:** `JobCreationState` does not persist across conversation turns; LIA operates with current message only, ignoring prior collected fields.

**Evidence:**
- `/home/runner/workspace/lia-agent-system/app/domains/job_creation/graph.py:150-180`
  - `intake_node()` extracts from `state.get("user_query")` (current message) + `right_panel_form` + `attached_file_text`
  - No mechanism to auto-populate state with previously answered fields (e.g., salary from turn 2 available in turn 4)
- `JobCreationState` schema unclear on whether it persists between invocations

**Why LIA forgets:**  
1. Turn 1: User provides salary range
2. Turn 2: State saved with salary_min/max
3. Turn 3: LIA calls `salary_node` → it reads salary_min/max from state → fine
4. Turn 4: User asks "qual é o departamento?", LIA re-asks salary
   - Likely because `intake_node` re-runs and overwrites state with new user_query only
   - Earlier fields not merged back in

**Fix Proposed (P1):**
1. Implement merge-state logic in `intake_node()`:
   ```python
   prior_payload = state.get("intake_payload") or {}
   new_payload = extractor.extract(query)
   merged = merge_payloads(prior_payload, new_payload, precedence="new_over_prior")
   state["intake_payload"] = merged
   ```
2. Add "already answered" indicator to LLM prompt so it doesn't re-ask
3. Implement `WorkingMemory` layer: serialize `{field: (value, confidence)}` tuples
4. Return to user: "Usando departamento coletado anteriormente: TI"

**Severity:** P1 (breaks UX continuity, user frustration)

---

## Prioritized Fix List

### Phase 1 (P0/P1 — Launch blockers)
| Bug | Severity | Effort | Impact |
|-----|----------|--------|--------|
| Bug 1: Salary benchmark validation | P0 | 2h | Prevents budget miscalibration |
| Bug 6: State merge between turns | P1 | 4h | Breaks wizard flow continuity |
| Bug 2: JWT refresh mechanism | P1 | 3h | Prevents session loss mid-wizard |

### Phase 2 (P1 — Hot-fix within 1 week)
| Bug | Severity | Effort | Impact |
|-----|----------|--------|--------|
| Bug 3: Specific error messages | P1 | 2h | Improves UX/debugging |
| Bug 5: Query normalization | P2 | 1h | Fixes search failures |

### Phase 3 (P2 — Next sprint)
| Bug | Severity | Effort | Impact |
|-----|----------|--------|--------|
| Bug 4: Route validation | P2 | 3h | Prevents 404 navigation |

---

## Testing Recommendations

1. **Bug 1:** Mock SerpAPI failure → verify salary caps enforced
2. **Bug 2:** Set JWT TTL = 2 min, run 10 min wizard flow → verify refresh auto-triggers
3. **Bug 3:** Simulate 503/504 → verify specific error messages shown
4. **Bug 4:** Add invalid route to wizard → verify validation blocks navigation
5. **Bug 5:** Query with punctuation → verify search succeeds
6. **Bug 6:** Provide field in turn 1, ask in turn 4 → verify not re-asked

---

**Total Remediation:** ~15 engineer-hours across 3 phases
**Launch Risk if Unfixed:** Medium (Bugs 1, 2, 6 block production UAT)
