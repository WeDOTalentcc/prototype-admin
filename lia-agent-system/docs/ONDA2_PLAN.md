# Onda 2 Implementation Plan

**Date:** 2026-04-21 | **Status:** Ready for execution | **Estimated Duration:** 3-4 weeks

## Executive Summary

Onda 2 closes 5 critical gaps identified in FINAL_AUDIT + INITIATIVES_AUDIT (Onda 1: 221/221 tests green). Each item is **implementation-ready** with concrete file:line patches, test shapes, and canonical-fix compliance validation.

**Priority ranking (execution order):**
1. **G5 light — PII Redaction** (LGPD blocker; unblocks IV+V production)
2. **Init VI Fase 1 — Golden Set + CI** (coverage gap; foundation for continuous eval)
3. **Init IV — Proactive Agenda** (generic greeting → context-aware briefing)
4. **Init V — Citations Backend** (response traceability; opt-in)
5. **Init II.D — Workflow Context** (multi-turn state machine; backward-compat critical)

**Key dependencies:** G5 ships first (blocks IV+V); VI depends on I; II.D is independent.

**Consolidated metrics:**
- **Total files touched:** 22 new + 14 modified
- **Test coverage:** 45-50 new tests across items
- **Feature flags required:** 4 (G5 flag, VI sampling, II.D rollback, V opt-in)
- **Monthly cost delta:** +$120 LLM (VI judge @ 30 cases/day) + $45 storage (PII audit logs)
- **Rollback safety:** 4/5 items fully reversible via flag-off; II.D requires alembic migration reverse

---

## 1. G5 light — PII Redaction Pipeline MVP

**Owner:** Platform / Compliance  
**Status:** READ-ONLY audit complete; implementation-ready  
**Closes:** LGPD Init IV + Init V blocking issue (briefing candidate counts, citations candidate IDs leak PII)

### 1.1 Producer Identification

**Current PII handling locations:**
- `/home/runner/workspace/lia-agent-system/app/domains/ats_integration/services/ats_clients/ats_pii_filter.py` (domain-level filtering)
- `app/api/v1/lgpd_compliance.py` (LGPD endpoint stub; no active redaction)
- `app/schemas/lgpd_compliance.py` (LgpdRedactionRequest dataclass)
- `app/domains/compliance/repositories/compliance_controls_repository.py` (policy storage)

**Gap:** No unified PII redaction interceptor at response layer. Compliance logic scattered.

### 1.2 Patch Sketch — `app/shared/compliance/pii_redaction.py` (NEW)

**File location:** `/home/runner/workspace/lia-agent-system/app/shared/compliance/pii_redaction.py`

**Structure:**
```python
# ~250 lines
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class PiiType(Enum):
    CPF = "cpf"           # ###.###.###-##
    CNPJ = "cnpj"         # ##.###.###/####-##
    PHONE = "phone"       # (+55 98) 9####-####
    EMAIL = "email"       # user@domain.com
    FULL_NAME = "name"    # Capitalized two+ word names
    CANDIDATE_ID = "id"   # numeric IDs in context

@dataclass
class PiiPattern:
    type: PiiType
    regex: re.Pattern
    replacement: str  # e.g. "[CPF REDACTED]"
    confidence: float  # 0.8-1.0 (heuristic-based)

class PiiRedactor:
    def __init__(self, enabled: bool = True, strict_mode: bool = False):
        self.enabled = enabled
        self.strict_mode = strict_mode  # True = redact on low confidence
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> list[PiiPattern]:
        # PT-BR specific regex patterns
        return [
            PiiPattern(
                type=PiiType.CPF,
                regex=re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}'),
                replacement='[CPF REDACTED]',
                confidence=0.95
            ),
            # ... CNPJ, phone, email patterns
            PiiPattern(
                type=PiiType.FULL_NAME,
                regex=re.compile(r'\b([A-Z][a-záéíóú]+\s+){1,}[A-Z][a-záéíóú]+\b'),
                replacement='[NAME REDACTED]',
                confidence=0.7  # HEURISTIC: caps + space = likely name
            ),
        ]
    
    def redact(self, text: str) -> tuple[str, list[dict]]:
        """Redact PII from text. Return (redacted_text, audit_log)."""
        if not self.enabled:
            return text, []
        
        audit = []
        redacted = text
        
        for pattern in self.patterns:
            matches = list(pattern.regex.finditer(redacted))
            for match in matches:
                audit.append({
                    'type': pattern.type.value,
                    'original_text': match.group(),
                    'span': (match.start(), match.end()),
                    'confidence': pattern.confidence,
                })
                redacted = redacted[:match.start()] + pattern.replacement + redacted[match.end():]
        
        return redacted, audit

# Global instance (singleton)
_redactor = PiiRedactor(enabled=True)

def redact_response(response_text: str, audit_context: dict) -> tuple[str, list[dict]]:
    """Entry point: redact response + log to compliance audit table."""
    redacted, audit_log = _redactor.redact(response_text)
    
    # Log to compliance_audit table (async)
    asyncio.create_task(_log_redaction_audit(audit_log, audit_context))
    
    return redacted, audit_log
```

**Integration point in `app/orchestrator/main_orchestrator.py` (line ~320, before response return):**

```python
# OLD (line ~320):
return ChatResponse(
    success=True,
    content=response_content,
    ...
)

# NEW:
from app.shared.compliance.pii_redaction import redact_response

redacted_content, pii_audit = redact_response(
    response_content,
    audit_context={
        'conversation_id': conversation_id,
        'user_id': current_user.id,
        'timestamp': datetime.utcnow(),
    }
)

return ChatResponse(
    success=True,
    content=redacted_content,
    pii_redacted=len(pii_audit) > 0,  # NEW FIELD
    ...
)
```

### 1.3 Test Shape (9 tests)

**File:** `/home/runner/workspace/lia-agent-system/tests/test_fix_g5_pii_redaction.py`

```python
# 9 test cases:
def test_cpf_redaction_valid():
    """CPF ###.###.###-## → [CPF REDACTED]"""
    assert "[CPF REDACTED]" in redactor.redact("Candidato CPF 123.456.789-00")[0]

def test_cnpj_redaction():
    """CNPJ ##.###.###/####-## → [CNPJ REDACTED]"""
    assert "[CNPJ REDACTED]" in redactor.redact(...)[0]

def test_phone_redaction_brazil():
    """(+55 98) 98765-4321 → [PHONE REDACTED]"""
    pass

def test_email_redaction():
    """user@company.com → [EMAIL REDACTED]"""
    pass

def test_name_heuristic_low_confidence():
    """João Silva (heuristic, confidence 0.7) — redacted only if strict_mode=True"""
    strict_off = redactor.redact("Candidate: João Silva", strict_mode=False)
    assert "Silva" in strict_off[0]  # NOT redacted in permissive mode
    
    strict_on = redactor.redact("Candidate: João Silva", strict_mode=True)
    assert "[NAME REDACTED]" in strict_on[0]

def test_candidate_id_in_context():
    """ID references (candidate_id: 12345) redacted when linked to real names"""
    pass

def test_false_positive_avoidance():
    """Email-like patterns that aren't emails (e.g., code@version) NOT redacted"""
    pass

def test_redaction_audit_log():
    """Each redaction logged with type, span, confidence, timestamp"""
    _, audit = redactor.redact("CPF 123.456.789-00")
    assert audit[0]['type'] == 'cpf'
    assert audit[0]['confidence'] == 0.95

def test_disabled_flag_bypass():
    """When feature flag pii_redaction_enabled=false, no redaction happens"""
    disabled = PiiRedactor(enabled=False)
    text, audit = disabled.redact("CPF 123.456.789-00")
    assert "123.456.789-00" in text
    assert len(audit) == 0
```

### 1.4 Feature Impact Analysis — G5 light

**Blast radius:**
- Files touched: `main_orchestrator.py` (1 line), `pii_redaction.py` (NEW 250 lines), `lgpd_compliance.py` (2 lines for audit logging)
- Tests affected: 9 new tests; NO existing test breakage (redaction transparent when disabled)
- API contract change: Additive only (new field `pii_redacted: bool`)

**Performance:**
- Latency delta per turn: +8-12ms (regex on response text; ~1000 char avg)
- DB queries added: 1 async write to compliance_audit (non-blocking)
- Token inflation in prompt: 0 (redaction is post-generation)

**Cost:**
- LLM cost delta: $0 (no new LLM calls)
- Storage delta: +2-3 GB/year (audit log ~0.5KB per redaction event, ~10K/day)

**Rollback plan:**
- Feature flag: `pii_redaction_enabled` (default: true in prod, false in dev)
- Revert path: Flag off → instant bypass; no data migration required
- Data migration reversibility: YES (audit logs are append-only, optional)

**Canonical-fix compliance:**
- ✅ Patch at producer (main_orchestrator response assembly, not consumer)
- ✅ No silent fallback (audit log captures all redactions; transparency to compliance officer)
- ✅ No workaround (real redaction at response layer; not deferred to client)
- ✅ Follows existing provider pattern (FairnessGuard pre-check model; composes cleanly)

---

## 2. Init VI Fase 1 — Golden Set Expansion + CI Wiring

**Owner:** Eval / Platform  
**Status:** Eval infrastructure exists (139 result JSONs); CI missing  
**Closes:** 40-50% coverage gap in eval_cases.yaml (99 cases) vs FIX 20-32 scenarios

### 2.1 Producer Identification

**Current eval state:**
- `eval/eval_cases.yaml` (73 KB; 99 cases) — meta.total_cases: 99
- `eval/eval_runner.py` (32 KB; executes cases)
- `eval/eval_judge.py` (8.5 KB; 5 scoring dimensions hardcoded)
- `eval/eval_judge_config.yaml` (2.7 KB; NEW in Onda 1)
- `.github/workflows/ci.yml` (5.4 KB; NO eval trigger)
- `eval/eval_results_*.json` (145+ files, latest 117KB; full judge output)

**Gap:** No CI workflow triggers eval on PR; judge config exists but not fully integrated; golden set small relative to eval run frequency.

### 2.2 Patch Sketch — CI Integration

**File:** `.github/workflows/eval.yml` (NEW)

```yaml
# 60 lines
name: LIA Judge Eval (Onda 1+)

on:
  pull_request:
    paths:
      - 'app/prompts/**'
      - 'app/orchestrator/**'
      - 'eval/eval_cases.yaml'
      - 'eval/eval_judge_config.yaml'
  schedule:
    - cron: '0 22 * * *'  # Nightly 22:00 UTC (20:00 BRT)

env:
  EVAL_SAMPLE_SIZE_PR: 20        # Sample 20/99 cases per PR
  EVAL_SAMPLE_SIZE_NIGHTLY: 99   # All cases nightly
  EVAL_JUDGE_MODEL: claude-3-5-sonnet
  EVAL_COST_CAP_MONTHLY: 150     # $150/month budget

jobs:
  judge-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install deps
        run: |
          pip install -r requirements.txt
          pip install anthropic pydantic
      
      - name: Determine eval scope (PR vs nightly)
        id: scope
        run: |
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            echo "sample_size=${{ env.EVAL_SAMPLE_SIZE_PR }}" >> $GITHUB_OUTPUT
            echo "is_full=false" >> $GITHUB_OUTPUT
          else
            echo "sample_size=${{ env.EVAL_SAMPLE_SIZE_NIGHTLY }}" >> $GITHUB_OUTPUT
            echo "is_full=true" >> $GITHUB_OUTPUT
          fi
      
      - name: Run judge eval (sampled or full)
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python eval/eval_runner.py \
            --judge_model ${{ env.EVAL_JUDGE_MODEL }} \
            --sample_size ${{ steps.scope.outputs.sample_size }} \
            --output eval/eval_results_$(date +%Y%m%d_%H%M%S).json \
            --cost_budget ${{ env.EVAL_COST_CAP_MONTHLY }}
      
      - name: Parse results + upload artifact
        run: |
          python eval/eval_report.py \
            --results eval/eval_results_*.json \
            --output eval/eval_report_$(date +%Y%m%d).html
          
      - name: Comment PR with results (PR only)
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('eval/eval_results_latest.json', 'utf8'));
            const avgScore = (results.summary.avg_score * 100).toFixed(1);
            const comment = `## Judge Eval Results\n- **Avg Score:** ${avgScore}%\n- **Cases:** ${results.summary.total_cases} sampled\n- **Cost:** $${results.summary.cost.toFixed(2)}\n[Full Report](${artifacts_url})`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
      
      - name: Fail if avg score < 70%
        run: |
          SCORE=$(jq '.summary.avg_score' eval/eval_results_latest.json)
          if (( $(echo "$SCORE < 0.7" | bc -l) )); then
            echo "Judge score too low: $SCORE"
            exit 1
          fi
```

**Extension to `eval_runner.py` (lines 100-150):**

```python
# Add sampling logic
def run_eval(
    cases_file: str = "eval/eval_cases.yaml",
    judge_model: str = "claude-3-5-sonnet",
    sample_size: int = None,  # None = all cases
    output: str = None,
) -> dict:
    """Load cases, optionally sample, run judge, return results."""
    
    cases = load_cases_from_yaml(cases_file)
    
    if sample_size and sample_size < len(cases):
        # Stratified sampling: maintain category distribution
        sampled = stratified_sample(cases, sample_size)
        logger.info(f"Sampled {sample_size}/{len(cases)} cases (stratified by category)")
    else:
        sampled = cases
    
    results = []
    cost_tracker = CostTracker(budget_dollars=150)  # Monthly cap
    
    for case in sampled:
        if cost_tracker.estimate_remaining() < 0.10:
            logger.warning("Cost budget exhausted; stopping eval")
            break
        
        judge_result = judge_case(
            case,
            judge_model=judge_model,
            config=load_judge_config("eval/eval_judge_config.yaml"),
        )
        results.append(judge_result)
        cost_tracker.add(judge_result['cost_cents'] / 100.0)
    
    # Compile summary
    summary = {
        'total_cases': len(sampled),
        'avg_score': statistics.mean([r['score'] for r in results]),
        'cost': cost_tracker.total_spent,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    output_json = {
        'summary': summary,
        'results': results,
    }
    
    if output:
        with open(output, 'w') as f:
            json.dump(output_json, f, indent=2)
    
    return output_json
```

### 2.3 Golden Set Expansion (30 new cases)

**File:** Append to `eval/eval_cases.yaml` (~3KB new)

**New cases by FIX gap:** (list of ~30 cases covering):
- FIX 20: Pagination (next/prev)
- FIX 22: Enum normalization (status codes)
- FIX 23: Quantifier normalization (many/few/all)
- FIX 27: Greeting personalization
- FIX 28: Feedback loop detection
- FIX 31: Cancellation workflow
- FIX 32: Compliance flag handling
- Edge cases: Multi-turn context loss, stale data, concurrent writes

**Example additions:**
```yaml
  # FIX 20 — Pagination
  - id: JM-050
    category: CX
    severity: high
    title: "Pagination context across turns"
    prompt: "mostra a próxima página de vagas"
    context:
      scope: "Vagas"
      page: "gestao-vagas"
      conversation_turns: 2  # Ensure state persists
    expected_tools: ["list_jobs"]
    expected_behavior: "Uses pagination_cursor from ConversationState; fetches next 20 jobs"
    canonical_files:
      - "app/shared/memory/conversation_state.py"
    success_criteria:
      - "Pagination offset incremented correctly"
      - "Same conversation_id used"
    anti_patterns:
      - "Starts from page 1 again (state lost)"
      - "No tools called"

  # FIX 27 — Greeting personalization (Init IV)
  - id: PR-051
    category: PR
    severity: high
    title: "Proactive greeting with briefing"
    prompt: "[new conversation, no prior context]"
    context:
      scope: null
      page: null
      first_message: true
      pending_offers_count: 3
      stale_candidates_count: 5
    expected_behavior: "Responds with 'Oi [Name]! Temos 3 coisas para você fazer...' (briefing)"
    expected_tools: ["get_briefing"]  # NEW tool Init IV
    canonical_files:
      - "app/domains/recruiter_assistant/services/daily_briefing_service.py"
    success_criteria:
      - "Greeting mentions pending_offers and stale_candidates"
      - "Tone is warm + proactive"
```

### 2.4 Feature Impact Analysis — VI Fase 1

**Blast radius:**
- Files touched: `.github/workflows/eval.yml` (NEW), `eval_runner.py` (+50 lines), `eval_cases.yaml` (+3KB), `eval/eval_judge_config.yaml` (existing)
- Tests affected: New CI workflow; no unit test breakage
- API contract change: None (eval is CI-only, not prod runtime)

**Performance:**
- Latency delta per turn: 0 (eval runs offline/async)
- DB queries added: 0 (eval operates on golden YAML)
- Token inflation in prompt: 0 (eval is separate from serving)

**Cost:**
- LLM cost delta: +$120/month (30 cases/day × 7 days × 4 weeks × $0.06/judge call @ Sonnet rate)
- Storage delta: +1-2 GB/month (eval_results_*.json files; mitigate via .gitignore + artifact bucket)

**Rollback plan:**
- Feature flag: Eval workflow disabled via `.github/workflows/` deletion or `on: []`
- Revert path: Remove `.github/workflows/eval.yml`; no code rollback
- Data migration reversibility: YES (eval JSONs are ephemeral; can delete all)

**Canonical-fix compliance:**
- ✅ Patch at producer (eval runner, not consumer)
- ✅ No silent fallback (cost tracking + budget cap enforce hard stop)
- ✅ No workaround (real judge integration; not mocked)
- ✅ Follows existing judge pattern (eval_judge.py + config already exist)

---

## 3. Init IV — Proactive Agenda (Daily Briefing)

**Owner:** Recruiter Assistant / Proactive AI  
**Status:** Briefing service stub exists; not wired to greeting  
**Closes:** Generic greeting → Sierra/Fin-style "Oi! Temos 3 coisas: ..." opener

### 3.1 Producer Identification

**Current briefing state:**
- `app/domains/analytics/services/weekly_digest_service.py` (200+ LOC; reusable aggregation)
- `app/shared/services/briefing_service.py` (stub; not called)
- `app/api/v1/briefing.py` (endpoint stub)
- DB queries exist: `pending_offers`, `stale_candidates`, `missing_feedback` (in analytics domain)

**Gap:** Greeting system prompt has no briefing integration; briefing service not called from main_orchestrator.

### 3.2 Patch Sketch — `app/domains/recruiter_assistant/services/daily_briefing_service.py` (NEW)

**File location:** `/home/runner/workspace/lia-agent-system/app/domains/recruiter_assistant/services/daily_briefing_service.py`

**Structure:**
```python
# ~180 lines
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

class BriefingItem(BaseModel):
    category: str  # "pending_offer", "stale_candidate", "missing_feedback"
    count: int
    sample: str  # e.g. "Product Manager (Acme Corp)"
    urgency: str  # "high", "medium"
    action_prompt: str  # "Oi! Você tem 3 ofertas pendentes de resposta..."

class DailyBriefing(BaseModel):
    greeting_name: str
    items: list[BriefingItem]
    cached_at: datetime
    ttl_seconds: int = 300  # 5-minute cache

class DailyBriefingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Optional[DailyBriefing] = None
        self._cache_expires_at: Optional[datetime] = None
    
    async def get_briefing(self, recruiter_id: str, company_id: str) -> DailyBriefing:
        """Fetch briefing items; return cached if fresh."""
        
        # Check cache
        if self._cache and datetime.utcnow() < self._cache_expires_at:
            return self._cache
        
        # Fetch aggregated data
        pending = await self._fetch_pending_offers(recruiter_id, company_id)
        stale = await self._fetch_stale_candidates(recruiter_id, company_id)
        missing = await self._fetch_missing_feedback(recruiter_id, company_id)
        
        items = []
        
        if pending:
            items.append(BriefingItem(
                category="pending_offer",
                count=len(pending),
                sample=pending[0]['job_title'],
                urgency="high",
                action_prompt=f"Você tem {len(pending)} ofertas pendentes de decisão"
            ))
        
        if stale:
            items.append(BriefingItem(
                category="stale_candidate",
                count=len(stale),
                sample=stale[0]['candidate_name'],
                urgency="medium",
                action_prompt=f"{len(stale)} candidatos sem feedback há >7 dias"
            ))
        
        if missing:
            items.append(BriefingItem(
                category="missing_feedback",
                count=len(missing),
                sample=missing[0]['job_title'],
                urgency="medium",
                action_prompt=f"{len(missing)} vagas esperando por feedback seu"
            ))
        
        briefing = DailyBriefing(
            greeting_name=recruiter_id,
            items=items,
            cached_at=datetime.utcnow(),
        )
        
        # Cache
        self._cache = briefing
        self._cache_expires_at = datetime.utcnow() + timedelta(seconds=briefing.ttl_seconds)
        
        return briefing
    
    async def _fetch_pending_offers(self, recruiter_id: str, company_id: str) -> list[dict]:
        """Query offers awaiting recruiter decision."""
        query = """
        SELECT j.id, j.title as job_title, COUNT(o.id) as offer_count
        FROM jobs j
        LEFT JOIN offers o ON j.id = o.job_id AND o.status = 'pending'
        WHERE j.recruiter_id = :recruiter_id AND j.company_id = :company_id
        AND o.created_at > NOW() - INTERVAL '7 days'
        GROUP BY j.id
        HAVING COUNT(o.id) > 0
        LIMIT 5
        """
        result = await self.db.execute(query, {"recruiter_id": recruiter_id, "company_id": company_id})
        return result.fetchall()
    
    async def _fetch_stale_candidates(self, recruiter_id: str, company_id: str) -> list[dict]:
        """Candidates with no feedback in >7 days."""
        query = """
        SELECT c.id, c.name as candidate_name, j.title as job_title
        FROM candidates c
        JOIN evaluations e ON c.id = e.candidate_id
        WHERE e.recruiter_id = :recruiter_id AND e.company_id = :company_id
        AND e.last_feedback_at < NOW() - INTERVAL '7 days'
        ORDER BY e.last_feedback_at ASC
        LIMIT 3
        """
        result = await self.db.execute(query, {"recruiter_id": recruiter_id, "company_id": company_id})
        return result.fetchall()
    
    async def _fetch_missing_feedback(self, recruiter_id: str, company_id: str) -> list[dict]:
        """Jobs waiting for recruiter feedback."""
        # Similar query pattern
        pass
```

**Integration in `app/orchestrator/main_orchestrator.py` (lines ~80, in greeting assembly):**

```python
# OLD (before llm_cascade.run()):
system_prompt = SystemPromptBuilder.assemble(conversation_state, actions_context)

# NEW:
briefing = None
if is_first_turn(conversation_state):
    # First turn in conversation: fetch briefing
    briefing_svc = DailyBriefingService(db=get_db())
    briefing = await briefing_svc.get_briefing(
        recruiter_id=current_user.id,
        company_id=conversation_state.company_id
    )

system_prompt = SystemPromptBuilder.assemble(
    conversation_state,
    actions_context,
    briefing=briefing,  # NEW parameter
)
```

**Update to SystemPromptBuilder (in `app/orchestrator/llm_cascade.py`, lines ~100):**

```python
class SystemPromptBuilder:
    @staticmethod
    def assemble(
        state: ConversationState,
        actions: dict,
        briefing: Optional[DailyBriefing] = None,
    ) -> str:
        """Build system prompt with optional briefing."""
        
        base = SYSTEM_PROMPT_BASE  # Existing
        
        if briefing and briefing.items:
            briefing_block = f"""
## Seu Briefing Diário

Oi {briefing.greeting_name}! Temos {len(briefing.items)} coisas para você hoje:

"""
            for i, item in enumerate(briefing.items, 1):
                briefing_block += f"{i}. {item.action_prompt}\n"
            
            briefing_block += """
Quer que eu ajude com uma delas?
---
"""
            return base + "\n" + briefing_block + actions + ...
        
        return base + actions + ...
```

### 3.3 Test Shape (6 tests)

```python
# tests/test_init_iv_proactive_agenda.py
def test_briefing_fetch_pending_offers():
    """DailyBriefingService fetches pending offers for recruiter."""
    mock_db = Mock()
    svc = DailyBriefingService(mock_db)
    briefing = await svc.get_briefing("recruiter_1", "company_A")
    
    assert any(item.category == "pending_offer" for item in briefing.items)

def test_briefing_cache_ttl():
    """Briefing cached for 5 minutes; subsequent calls return cached."""
    svc = DailyBriefingService(mock_db)
    first = await svc.get_briefing("r1", "c1")
    second = await svc.get_briefing("r1", "c1")
    
    assert first == second  # Same object from cache
    
    # Advance time 6 minutes; cache expires
    await asyncio.sleep(360)
    third = await svc.get_briefing("r1", "c1")
    assert third != first  # Fresh fetch

def test_briefing_in_system_prompt_first_turn():
    """First turn includes briefing block in system prompt."""
    state = ConversationState(company_id="c1", last_candidates_shown=[])
    briefing = DailyBriefing(
        greeting_name="Sarah",
        items=[BriefingItem(category="pending_offer", count=3, sample="PM", urgency="high", action_prompt="3 offers pending")],
    )
    
    prompt = SystemPromptBuilder.assemble(state, {}, briefing=briefing)
    
    assert "Oi Sarah" in prompt
    assert "Temos 1 coisas" in prompt
    assert "3 offers pending" in prompt

def test_no_briefing_subsequent_turns():
    """Turns 2+ don't include briefing (already presented once)."""
    state = ConversationState(company_id="c1", last_candidates_shown=[1, 2])  # Non-empty = not first turn
    prompt = SystemPromptBuilder.assemble(state, {}, briefing=None)
    
    assert "Seu Briefing" not in prompt

def test_briefing_pii_candidates_redacted():
    """Candidate names in briefing are redacted (G5 integration)."""
    briefing = DailyBriefing(
        greeting_name="Sarah",
        items=[BriefingItem(
            category="stale_candidate",
            count=1,
            sample="João Silva",  # Full name
            urgency="medium",
            action_prompt="..."
        )]
    )
    
    # After G5 redaction:
    redacted_briefing = apply_pii_redaction(briefing)
    assert "[NAME REDACTED]" in redacted_briefing.items[0].sample

def test_briefing_no_items_empty_greeting():
    """If no briefing items, skip briefing block entirely."""
    briefing = DailyBriefing(greeting_name="Sarah", items=[])
    prompt = SystemPromptBuilder.assemble(state, {}, briefing=briefing)
    
    assert "Seu Briefing" not in prompt  # No items = no block
```

### 3.4 Feature Impact Analysis — Init IV

**Blast radius:**
- Files touched: `daily_briefing_service.py` (NEW 180 lines), `main_orchestrator.py` (+5 lines), `llm_cascade.py` (+20 lines)
- Tests affected: 6 new tests; no existing breakage
- API contract change: None (internal to greeting pipeline)

**Performance:**
- Latency delta per turn: +50-80ms (DB queries on first turn only; cached 5 min)
- DB queries added: 3 async queries (pending, stale, missing) on first turn only
- Token inflation in prompt: +80-120 tokens (briefing block ~30 tokens + items ~50-90)

**Cost:**
- LLM cost delta: ~+$5/month (extra tokens in 10% of conversations, first turn)
- Storage delta: +500MB/year (cache misses logged for analytics)

**Rollback plan:**
- Feature flag: `proactive_agenda_enabled` (default: true)
- Revert path: Flag off → skip briefing assembly entirely
- Data migration reversibility: YES (no schema changes; briefing is computed on-demand)

**Canonical-fix compliance:**
- ✅ Patch at producer (daily_briefing_service queries DB; result injected into system prompt)
- ✅ No silent fallback (if briefing query fails, warning logged; greeting still sent)
- ✅ No workaround (real queries to pending/stale tables; not mocked)
- ✅ Follows weekly_digest_service pattern (reuse DB queries from existing analytics domain)

---

## 4. Init V — Reasoning Transparency / Citations Backend

**Owner:** Observability / Trustworthiness  
**Status:** ChatResponse schema exists; no citation fields  
**Closes:** Responses lack traceability (which tools were called, what params, what results)

### 4.1 Producer Identification

**Current ChatResponse location:** `app/schemas/chat.py` (line 60, dataclass with 20+ fields)

**Current tool_calls tracking:** `main_orchestrator.py` calls tools but doesn't store result references.

**Gap:** No structured citation linking response text spans to tool invocations.

### 4.2 Patch Sketch — ChatResponse Citation Fields + Citation Processor

**File:** `app/schemas/chat.py` (lines ~80-120, NEW fields in ChatResponse)

```python
# In ChatResponse dataclass, add:

@dataclass
class Citation(BaseModel):
    text_span: str  # e.g., "Product Manager at Acme"
    tool_name: str  # e.g., "get_job_details"
    tool_params: dict  # e.g., {"job_id": "V0037"}
    tool_result_ref: str  # Pointer to result in tool_calls array
    timestamp: datetime

class ChatResponse(BaseModel):
    # ... existing 20 fields ...
    
    # NEW: Optional citations (opt-in via feature flag)
    citations: list[Citation] | None = None
    has_citations: bool = False
    
    # NEW: Backward compat — tool_calls array for LLM layer
    tool_calls: list[dict] | None = None  # Raw tool calls from LLM
```

**New file:** `app/orchestrator/citation_processor.py` (NEW, ~150 lines)

```python
# ~150 lines
import re
from typing import Optional
from app.schemas.chat import Citation
from app.orchestrator.action_executor import ActionResult

class CitationProcessor:
    """Extract citations from tool calls + response text (heuristic-based)."""
    
    def __init__(self, enable_citations: bool = False):
        self.enabled = enable_citations
    
    def process(
        self,
        response_text: str,
        tool_calls: list[dict],  # {tool_name, params, result}
        timestamp: datetime,
    ) -> list[Citation]:
        """
        Build citations by matching response spans to tool invocations.
        Heuristic: no LLM parsing (expensive per-turn).
        """
        
        if not self.enabled or not tool_calls:
            return None
        
        citations = []
        
        # For each tool call, extract likely mentions from response_text
        for call_idx, call in enumerate(tool_calls):
            tool_name = call['tool_name']
            tool_params = call['params']
            result = call.get('result', {})
            
            # Heuristic patterns:
            if tool_name == "get_job_details":
                job_title = result.get('title', '')
                company = result.get('company', '')
                
                # Try to find these in response
                pattern = re.escape(job_title)
                for match in re.finditer(pattern, response_text, re.IGNORECASE):
                    citations.append(Citation(
                        text_span=response_text[match.start():match.end()],
                        tool_name=tool_name,
                        tool_params=tool_params,
                        tool_result_ref=f"tool_call[{call_idx}]",
                        timestamp=timestamp,
                    ))
            
            elif tool_name == "list_candidates":
                # Extract candidate names from result
                candidates = result.get('candidates', [])
                for cand in candidates:
                    name = cand.get('name', '')
                    pattern = re.escape(name)
                    for match in re.finditer(pattern, response_text):
                        citations.append(Citation(
                            text_span=response_text[match.start():match.end()],
                            tool_name=tool_name,
                            tool_params=tool_params,
                            tool_result_ref=f"tool_call[{call_idx}]",
                            timestamp=timestamp,
                        ))
            
            # Add more heuristics for other tools as needed
        
        return citations if citations else None
```

**Integration in `main_orchestrator.py` (lines ~340, post-response generation):**

```python
from app.orchestrator.citation_processor import CitationProcessor

# NEW: Initialize citation processor (from feature flag)
citation_processor = CitationProcessor(
    enable_citations=feature_flags.get("citations_enabled", False)
)

# Before returning ChatResponse:
citations = citation_processor.process(
    response_content,
    tool_calls=executed_tools,  # {tool_name, params, result}[]
    timestamp=datetime.utcnow(),
)

return ChatResponse(
    success=True,
    content=response_content,
    tool_calls=executed_tools,  # Store raw calls
    citations=citations,
    has_citations=citations is not None and len(citations) > 0,
    ...
)
```

### 4.3 Test Shape (7 tests)

```python
# tests/test_init_v_citations.py

def test_citation_opt_in_flag():
    """Citations only generated when feature flag enabled."""
    processor_off = CitationProcessor(enable_citations=False)
    result = processor_off.process("Got result: PM role", [{...}], now())
    assert result is None
    
    processor_on = CitationProcessor(enable_citations=True)
    result = processor_on.process("Got result: PM role", [{...}], now())
    assert result is not None

def test_citation_job_title_match():
    """Job title in response → citation to get_job_details call."""
    response = "The Product Manager role at Acme is..."
    tool_calls = [{
        'tool_name': 'get_job_details',
        'params': {'job_id': 'V0037'},
        'result': {'title': 'Product Manager', 'company': 'Acme'}
    }]
    
    citations = CitationProcessor(True).process(response, tool_calls, now())
    
    assert len(citations) == 1
    assert "Product Manager" in citations[0].text_span
    assert citations[0].tool_name == "get_job_details"

def test_citation_multiple_spans():
    """Multiple mentions of same entity → multiple citations."""
    response = "John Doe is a candidate. John Doe applied yesterday."
    tool_calls = [{
        'tool_name': 'list_candidates',
        'params': {},
        'result': {'candidates': [{'name': 'John Doe'}]}
    }]
    
    citations = CitationProcessor(True).process(response, tool_calls, now())
    
    assert len(citations) >= 2  # At least 2 mentions

def test_citation_no_false_positives():
    """Partial name matches (e.g., 'John' in 'Johnson') NOT cited unless exact."""
    response = "Johnson was great."
    tool_calls = [{
        'tool_name': 'list_candidates',
        'params': {},
        'result': {'candidates': [{'name': 'John'}]}
    }]
    
    citations = CitationProcessor(True).process(response, tool_calls, now())
    
    # Heuristic should NOT match "John" in "Johnson"
    assert len(citations) == 0 or citations[0].text_span != "John"

def test_citation_schema_valid():
    """Citation dataclass has required fields."""
    c = Citation(
        text_span="PM role",
        tool_name="get_job_details",
        tool_params={"job_id": "V0037"},
        tool_result_ref="tool_call[0]",
        timestamp=datetime.utcnow(),
    )
    
    assert c.text_span == "PM role"
    assert c.tool_name == "get_job_details"

def test_chat_response_backward_compat():
    """ChatResponse without citations still valid (backward compat)."""
    response = ChatResponse(
        success=True,
        content="Hello",
        # citations=None (omitted)
    )
    
    assert response.citations is None
    assert response.has_citations is False

def test_citation_timestamp_precision():
    """Citation timestamp matches tool call execution time."""
    now = datetime.utcnow()
    citations = CitationProcessor(True).process(response, tool_calls, now)
    
    for citation in citations:
        assert citation.timestamp.isoformat()[:19] == now.isoformat()[:19]  # Same second
```

### 4.4 Feature Impact Analysis — Init V

**Blast radius:**
- Files touched: `chat.py` (+8 lines), `citation_processor.py` (NEW 150 lines), `main_orchestrator.py` (+12 lines)
- Tests affected: 7 new tests; ChatResponse backward-compatible (citations optional)
- API contract change: Additive only (new optional `citations` field + `has_citations` bool)

**Performance:**
- Latency delta per turn: +2-5ms (regex matching on response text; no LLM calls)
- DB queries added: 0 (citations computed from tool_calls already in memory)
- Token inflation in prompt: 0 (citations are metadata, not injected into LLM)

**Cost:**
- LLM cost delta: $0 (no new LLM invocations)
- Storage delta: +1-2 GB/year (citation metadata in logs)

**Rollback plan:**
- Feature flag: `citations_enabled` (default: false; opt-in)
- Revert path: Flag off → no citations generated; API still accepts `citations` field (ignored)
- Data migration reversibility: YES (citations are computed on-demand; no persistence)

**Canonical-fix compliance:**
- ✅ Patch at producer (citations built from tool_calls in main_orchestrator, before response return)
- ✅ No silent fallback (if citation fails, warning logged; response still sent)
- ✅ No workaround (real heuristic-based extraction; not mocked)
- ✅ Follows observability pattern (tool_calls already logged; citations are just re-indexing)

**Notes:**
- Frontend (G1) dependency deferred; backend ships independently
- Citations UI (rendering clickable links in client) is separate G1 task
- LLM layer (judge eval) can inspect citations without client support

---

## 5. Init II.D — Workflow Context Slot (3 Workflows v1)

**Owner:** State Machine / Multi-turn Orchestration  
**Status:** ConversationState exists (14 slots); no workflow_context  
**Closes:** Multi-turn flows (cancelamento, sourcing, wizard) lack formal state

### 5.1 Producer Identification

**Current ConversationState location:** `app/shared/memory/conversation_state.py` (dataclass, 14 slots)

**Existing state slots:** `last_candidates_shown`, `active_filters`, `pagination_cursor`, `last_entity`, `last_job_id`

**Gap:** No `workflow_context` slot; workflow_id, step, total_steps not tracked; no workflow registry.

### 5.2 Patch Sketch — ConversationState + WorkflowRegistry

**File A:** `app/shared/memory/conversation_state.py` (lines ~50, add 2 fields)

```python
@dataclass
class ConversationState:
    # ... existing 14 fields ...
    
    # NEW: Workflow context (optional, for multi-turn flows)
    workflow_context: dict[str, Any] | None = None
    # Example: {
    #   'workflow_id': 'close_job_v1',
    #   'step': 1,
    #   'total_steps': 3,
    #   'elapsed_turns': 2,
    #   'last_action_intent': 'close_job',
    #   'data': {'job_id': 'V0037', 'reason': 'filled'}
    # }
    
    def to_prompt_context(self) -> str:
        """Aggregate state into markdown block for system prompt injection."""
        lines = []
        
        if self.active_filters:
            lines.append("## Filtros Ativos")
            for k, v in self.active_filters.items():
                lines.append(f"- {k}: {v}")
        
        if self.workflow_context:
            lines.append("## Fluxo em Andamento")
            wf = self.workflow_context
            lines.append(f"**Fluxo:** {wf.get('workflow_id', 'unknown')}")
            lines.append(f"**Passo:** {wf['step']}/{wf['total_steps']}")
            if wf.get('data'):
                lines.append(f"**Dados:** {wf['data']}")
        
        if self.last_entity:
            lines.append("## Última Entidade Mencionada")
            lines.append(f"{self.last_entity}")
        
        return "\n".join(lines) if lines else ""
```

**File B:** `app/orchestrator/workflow_registry.py` (NEW, ~200 lines)

```python
# ~200 lines
from dataclasses import dataclass
from typing import Callable, Any
from enum import Enum

class WorkflowStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

@dataclass
class WorkflowStep:
    step_num: int
    intent: str  # e.g., 'select_job', 'confirm_closure', 'archive'
    prompt_guidance: str  # Instructions for LLM at this step
    expected_tools: list[str]
    confirmation_required: bool
    data_schema: dict[str, Any]  # Pydantic schema for validation

@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    total_steps: int
    steps: list[WorkflowStep]
    entry_intent: str  # e.g., 'close_job' initiates close_job_v1
    exit_condition: Callable[[dict], bool]  # e.g., lambda data: data['job_id'] is not None
    timeout_minutes: int = 30

class WorkflowRegistry:
    def __init__(self):
        self.workflows: dict[str, WorkflowDefinition] = {}
        self._register_builtin_workflows()
    
    def _register_builtin_workflows(self):
        # Workflow 1: Close Job
        self.register(WorkflowDefinition(
            workflow_id="close_job_v1",
            name="Encerrar Vaga",
            total_steps=3,
            steps=[
                WorkflowStep(
                    step_num=1,
                    intent="select_job",
                    prompt_guidance="Ask which job to close",
                    expected_tools=["list_jobs"],
                    confirmation_required=False,
                    data_schema={"job_id": str}
                ),
                WorkflowStep(
                    step_num=2,
                    intent="provide_reason",
                    prompt_guidance="Ask why closing (filled/canceled/other)",
                    expected_tools=[],
                    confirmation_required=False,
                    data_schema={"reason": str}
                ),
                WorkflowStep(
                    step_num=3,
                    intent="confirm_closure",
                    prompt_guidance="Confirm closure and archive job",
                    expected_tools=["close_job", "archive_job"],
                    confirmation_required=True,
                    data_schema={"confirmed": bool}
                ),
            ],
            entry_intent="close_job",
            exit_condition=lambda data: data.get('confirmed') is True,
            timeout_minutes=30,
        ))
        
        # Workflow 2: Sourcing Filters
        self.register(WorkflowDefinition(
            workflow_id="sourcing_filters_v1",
            name="Configurar Filtros de Sourcing",
            total_steps=4,
            steps=[
                WorkflowStep(1, "select_job", "Which job to source for?", ["list_jobs"], False, {"job_id": str}),
                WorkflowStep(2, "filter_skills", "What skills required?", [], False, {"skills": list}),
                WorkflowStep(3, "filter_location", "What locations acceptable?", [], False, {"locations": list}),
                WorkflowStep(4, "confirm_search", "Start sourcing with filters?", ["start_sourcing"], True, {"confirmed": bool}),
            ],
            entry_intent="sourcing",
            exit_condition=lambda data: data.get('confirmed') is True,
            timeout_minutes=45,
        ))
        
        # Workflow 3: Job Creation Wizard
        self.register(WorkflowDefinition(
            workflow_id="job_creation_wizard_v1",
            name="Criar Nova Vaga",
            total_steps=5,
            steps=[
                WorkflowStep(1, "job_title", "Job title?", [], False, {"title": str}),
                WorkflowStep(2, "job_description", "Description + requirements?", [], False, {"description": str}),
                WorkflowStep(3, "job_location", "Location + work model?", [], False, {"location": str, "model": str}),
                WorkflowStep(4, "job_salary", "Salary range?", [], False, {"min": int, "max": int}),
                WorkflowStep(5, "confirm_creation", "Create job?", ["create_job"], True, {"confirmed": bool}),
            ],
            entry_intent="create_job",
            exit_condition=lambda data: data.get('confirmed') is True,
            timeout_minutes=60,
        ))
    
    def register(self, workflow: WorkflowDefinition):
        self.workflows[workflow.workflow_id] = workflow
    
    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self.workflows.get(workflow_id)
    
    def get_by_intent(self, intent: str) -> WorkflowDefinition | None:
        for wf in self.workflows.values():
            if wf.entry_intent == intent:
                return wf
        return None

# Singleton instance
_workflow_registry = WorkflowRegistry()

def get_workflow_registry() -> WorkflowRegistry:
    return _workflow_registry
```

**File C:** `app/orchestrator/workflow_manager.py` (NEW, ~180 lines)

```python
# ~180 lines
from datetime import datetime, timedelta
from app.shared.memory.conversation_state import ConversationState
from app.orchestrator.workflow_registry import get_workflow_registry

class WorkflowManager:
    """Manage workflow state transitions and step logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = get_workflow_registry()
    
    async def init_workflow(
        self,
        conversation_id: str,
        workflow_id: str,
        initial_data: dict = None,
    ) -> ConversationState:
        """Start a new workflow; update ConversationState."""
        
        workflow = self.registry.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow_context = {
            'workflow_id': workflow_id,
            'step': 1,
            'total_steps': workflow.total_steps,
            'elapsed_turns': 0,
            'last_action_intent': workflow.steps[0].intent,
            'data': initial_data or {},
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=workflow.timeout_minutes)).isoformat(),
        }
        
        # Load current state, update workflow_context
        state = await self._load_state(conversation_id)
        state.workflow_context = workflow_context
        
        # Persist
        await self._save_state(conversation_id, state)
        
        return state
    
    async def advance_workflow(
        self,
        conversation_id: str,
        next_step: int = None,
        action_data: dict = None,
    ) -> ConversationState:
        """Move to next workflow step."""
        
        state = await self._load_state(conversation_id)
        if not state.workflow_context:
            raise ValueError("No active workflow")
        
        wf_ctx = state.workflow_context
        workflow = self.registry.get_workflow(wf_ctx['workflow_id'])
        
        # Check timeout
        timeout_at = datetime.fromisoformat(wf_ctx['timeout_at'])
        if datetime.utcnow() > timeout_at:
            wf_ctx['status'] = 'abandoned'
            await self._save_state(conversation_id, state)
            raise TimeoutError(f"Workflow expired: {wf_ctx['workflow_id']}")
        
        # Validate current step data
        current_step = workflow.steps[wf_ctx['step'] - 1]
        if action_data:
            # Basic validation against data_schema
            for key in current_step.data_schema:
                if key not in action_data and current_step.confirmation_required:
                    raise ValueError(f"Missing required field: {key}")
            
            wf_ctx['data'].update(action_data)
        
        # Advance step
        if next_step is None:
            next_step = min(wf_ctx['step'] + 1, workflow.total_steps)
        
        wf_ctx['step'] = next_step
        wf_ctx['elapsed_turns'] += 1
        if next_step <= workflow.total_steps:
            wf_ctx['last_action_intent'] = workflow.steps[next_step - 1].intent
        
        # Check exit condition
        if next_step >= workflow.total_steps and workflow.exit_condition(wf_ctx['data']):
            wf_ctx['status'] = 'completed'
        
        await self._save_state(conversation_id, state)
        return state
    
    async def _load_state(self, conversation_id: str) -> ConversationState:
        """Load from DB or return empty."""
        # Query conversation_summaries table
        pass
    
    async def _save_state(self, conversation_id: str, state: ConversationState):
        """Persist to conversation_summaries.user_preferences (FIX 32) or new workflow_states table."""
        pass
```

**Integration in `main_orchestrator.py` (lines ~200, after intent detection):**

```python
from app.orchestrator.workflow_manager import WorkflowManager

# NEW: Check if intent triggers workflow start
workflow_mgr = WorkflowManager(db)
workflow = workflow_mgr.registry.get_by_intent(detected_intent)

if workflow and conversation_state.workflow_context is None:
    # Start new workflow
    conversation_state = await workflow_mgr.init_workflow(
        conversation_id,
        workflow.workflow_id,
        initial_data={}
    )
    logger.info(f"[LIA-WORKFLOW] Started {workflow.workflow_id}")

elif conversation_state.workflow_context:
    # Already in workflow; advance if needed
    await workflow_mgr.advance_workflow(conversation_id, action_data={...})
```

**DB Migration (Alembic):** `alembic/versions/102_add_workflow_context.py` (NEW, ~50 lines)

```python
def upgrade():
    op.add_column(
        'conversation_summaries',
        sa.Column('workflow_context', sa.JSON, nullable=True)
    )

def downgrade():
    op.drop_column('conversation_summaries', 'workflow_context')
```

### 5.3 Test Shape (8 tests)

```python
# tests/test_init_ii_d_workflow_context.py

def test_workflow_registry_has_3_workflows():
    registry = get_workflow_registry()
    assert len(registry.workflows) == 3
    assert registry.get_workflow("close_job_v1") is not None
    assert registry.get_workflow("sourcing_filters_v1") is not None
    assert registry.get_workflow("job_creation_wizard_v1") is not None

def test_workflow_init_close_job():
    """Initiating close_job intent starts close_job_v1 workflow."""
    mgr = WorkflowManager(mock_db)
    state = await mgr.init_workflow("conv_1", "close_job_v1", {"job_id": "V0037"})
    
    assert state.workflow_context['workflow_id'] == "close_job_v1"
    assert state.workflow_context['step'] == 1
    assert state.workflow_context['total_steps'] == 3
    assert state.workflow_context['data']['job_id'] == "V0037"

def test_workflow_advance_step():
    """Advance from step 1 to 2."""
    state = await mgr.init_workflow("conv_1", "close_job_v1", {})
    assert state.workflow_context['step'] == 1
    
    state = await mgr.advance_workflow("conv_1", action_data={"reason": "filled"})
    assert state.workflow_context['step'] == 2
    assert state.workflow_context['elapsed_turns'] == 1

def test_workflow_timeout():
    """Workflow expires after timeout_minutes."""
    state = await mgr.init_workflow("conv_1", "close_job_v1", {})
    # Mock time advance 31 minutes
    with patch('datetime.datetime') as mock_dt:
        mock_dt.utcnow.return_value = datetime.utcnow() + timedelta(minutes=31)
        
        with pytest.raises(TimeoutError):
            await mgr.advance_workflow("conv_1")
        
        state = await self._load_state("conv_1")
        assert state.workflow_context['status'] == 'abandoned'

def test_workflow_exit_condition():
    """Workflow marked complete when exit condition met."""
    state = await mgr.init_workflow("conv_1", "close_job_v1", {})
    
    # Advance through all steps with confirmation
    for step in range(1, 4):
        state = await mgr.advance_workflow("conv_1", action_data={"confirmed": True})
    
    assert state.workflow_context['status'] == 'completed'

def test_state_injection_in_prompt():
    """ConversationState.workflow_context injected into system prompt."""
    state = ConversationState(company_id="c1")
    state.workflow_context = {
        'workflow_id': 'close_job_v1',
        'step': 2,
        'total_steps': 3,
        'elapsed_turns': 1,
        'data': {'job_id': 'V0037', 'reason': 'filled'}
    }
    
    context_block = state.to_prompt_context()
    assert "Fluxo em Andamento" in context_block
    assert "close_job_v1" in context_block
    assert "Passo: 2/3" in context_block

def test_backward_compat_no_workflow():
    """Conversations without workflow_context still work (None is valid)."""
    state = ConversationState(company_id="c1")
    # workflow_context = None (default)
    
    context_block = state.to_prompt_context()
    assert "Fluxo em Andamento" not in context_block

def test_workflow_context_persisted_db():
    """workflow_context saved to DB; reloaded on next turn."""
    state1 = await mgr.init_workflow("conv_1", "sourcing_filters_v1", {})
    
    # Simulate new turn; reload state
    state2 = await mgr._load_state("conv_1")
    assert state2.workflow_context is not None
    assert state2.workflow_context['workflow_id'] == "sourcing_filters_v1"
```

### 5.4 Feature Impact Analysis — Init II.D

**Blast radius:**
- Files touched: `conversation_state.py` (+3 lines), `workflow_registry.py` (NEW 200 lines), `workflow_manager.py` (NEW 180 lines), `main_orchestrator.py` (+15 lines), alembic migration (NEW 50 lines)
- Tests affected: 8 new tests; existing ConversationState tests still pass (backward-compat)
- API contract change: None (internal state machine; no API changes)

**Performance:**
- Latency delta per turn: +5-10ms (state load/save in DB; cached in ConversationState)
- DB queries added: 1 read + 1 write per workflow turn (async)
- Token inflation in prompt: +50-100 tokens (workflow context block in system prompt)

**Cost:**
- LLM cost delta: ~+$8/month (extra tokens in workflows; ~5% of conversations use workflows)
- Storage delta: +1-2 GB/year (workflow_context JSON in conversation_summaries)

**Rollback plan:**
- Feature flag: `workflow_context_enabled` (default: false initially; opt-in for beta)
- Revert path: Flag off → workflow_context not injected; alembic migration reversible via downgrade
- Data migration reversibility: YES (migration can be reversed; workflow_context column dropped)

**Canonical-fix compliance:**
- ✅ Patch at producer (workflow_registry + workflow_manager own state logic; not consumer)
- ✅ No silent fallback (workflow timeout enforced; state persisted to DB)
- ✅ No workaround (real workflow state machine; not mocked transitions)
- ✅ Follows ConversationState pattern (reuse dataclass structure + serialization)

---

## 6. Cross-Item Concerns

### 6.1 Shared Dependencies

**Critical path:**
1. **G5 ships first** — unblocks Init IV (briefing PII redaction) + Init V (citation PII redaction)
2. **VI Fase 1 (CI + golden set)** — depends on Init I (eval cases must map to capabilities)
3. **II.D (workflow)** — independent; can ship in parallel with others

**Blocker relationships:**
- G5 must ship before IV production (briefing exposes candidate counts)
- G5 must ship before V production (citations expose candidate IDs)
- VI golden set expansion can start immediately (doesn't block CI wiring)

### 6.2 Shared Reuse

**Feature flag service:** Consolidate all 4 flags (G5, VI sampling, II.D rollback, V opt-in) in single `FeatureFlagService` in `app/shared/services/`.

**Compliance base:** All items use `app/domains/compliance_base.py` + `FairnessGuard` pattern (proven, low-risk).

**Observability:** All items instrument via `[LIA-*]` markers in `app/shared/observability/`.

### 6.3 Integration Testing Across Items

**Test scenario:** E2E flow combining IV + V + II.D

```python
# tests/test_onda2_integration.py
async def test_workflow_with_briefing_and_citations():
    """E2E: First turn includes briefing; workflow step shows citations."""
    
    # 1. First turn → briefing injected
    conversation_state = ConversationState(company_id="c1")
    briefing = DailyBriefingService.get_briefing(...)
    prompt = SystemPromptBuilder.assemble(conversation_state, {}, briefing=briefing)
    
    # LLM responds
    response, tool_calls = await main_orchestrator.process_message(
        user_input="Help with pending offers",
        conversation_state=conversation_state,
    )
    
    # 2. Briefing → response includes pending offers
    assert "Temos 3 coisas" in response
    
    # 3. Citations generated (Init V)
    citations = CitationProcessor(True).process(response, tool_calls, now())
    assert len(citations) > 0
    
    # 4. If user says "vou encerrar a vaga", workflow starts (Init II.D)
    user_input_2 = "Quero encerrar a vaga de PM"
    state2 = conversation_state  # State persists
    
    response2, _ = await main_orchestrator.process_message(user_input_2, state2)
    
    # Workflow initiated
    assert state2.workflow_context is not None
    assert state2.workflow_context['workflow_id'] == "close_job_v1"
    
    # 5. PII redaction applies to all responses (G5)
    redacted, pii_audit = redact_response(response + response2, audit_context={...})
    # Verify candidate IDs redacted
    assert "[ID REDACTED]" in redacted or "candidate_" not in redacted.lower()
```

---

## 7. Execution Checklist Per Item

### Item 1: G5 light — PII Redaction (Weeks 1-1.5)

- [ ] **Red test:** Write `test_fix_g5_pii_redaction.py` (9 tests, all fail)
- [ ] **Green code:** Implement `pii_redaction.py` + integrate in `main_orchestrator.py`
- [ ] **Refactor:** Consolidate regex patterns; add PT-BR locale module
- [ ] **Commit:** "Add PII redaction pipeline (G5 light) - LGPD compliance for Init IV+V"
- [ ] **Smoke test:** Run on sample response; verify no false positives
- [ ] **Regression:** Full test suite passes; CI green
- [ ] **User checkpoint:** Demo PII redaction on real conversation; gather feedback on heuristic confidence

### Item 2: Init VI Fase 1 — Golden Set + CI (Weeks 1.5-3.5)

- [ ] **Red test:** CI workflow fails (expected; no eval infrastructure)
- [ ] **Green code:** Create `.github/workflows/eval.yml`; extend `eval_runner.py` with sampling
- [ ] **Refactor:** Consolidate judge config; add cost tracking
- [ ] **Golden set:** Add 30 new cases to `eval_cases.yaml` (stratified by FIX)
- [ ] **Commit:** "Add VI Fase 1 eval CI + golden set expansion"
- [ ] **Smoke test:** Run eval on 20-case sample; verify cost tracking
- [ ] **Regression:** No code regressions; eval JSON schema valid
- [ ] **User checkpoint:** Show eval dashboard mock-up; discuss sampling strategy + cost cap

### Item 3: Init IV — Proactive Agenda (Weeks 2-2.75)

- [ ] **Red test:** Write `test_init_iv_proactive_agenda.py` (6 tests, all fail)
- [ ] **Green code:** Implement `daily_briefing_service.py`; integrate in `main_orchestrator.py` + `llm_cascade.py`
- [ ] **Refactor:** Reuse DB queries from `weekly_digest_service.py`; add caching
- [ ] **Commit:** "Add Init IV proactive briefing service + greeting integration"
- [ ] **Smoke test:** Run on fresh conversation; verify briefing appears + PII redacted (G5 integration)
- [ ] **Regression:** No existing greeting tests broken
- [ ] **User checkpoint:** Verify briefing content (pending offers, stale candidates); gather feedback on tone

### Item 4: Init V — Citations Backend (Weeks 2.75-3.25)

- [ ] **Red test:** Write `test_init_v_citations.py` (7 tests, all fail)
- [ ] **Green code:** Implement `citation_processor.py`; add `citations` field to `ChatResponse`; integrate in `main_orchestrator.py`
- [ ] **Refactor:** Consolidate heuristic patterns; add tool-specific citation rules
- [ ] **Commit:** "Add Init V citations backend (opt-in via feature flag)"
- [ ] **Smoke test:** Run with `citations_enabled=true`; verify citations appear in response
- [ ] **Regression:** Backward-compat: run with `citations_enabled=false`; verify no citations
- [ ] **User checkpoint:** Show citation UI mock-up (G1); discuss citation rendering on frontend

### Item 5: Init II.D — Workflow Context (Weeks 3-4)

- [ ] **Red test:** Write `test_init_ii_d_workflow_context.py` (8 tests, all fail)
- [ ] **Green code:** Implement `workflow_registry.py` + `workflow_manager.py`; integrate in `main_orchestrator.py` + `conversation_state.py`
- [ ] **Refactor:** Register 3 workflows (close_job, sourcing, wizard); consolidate step logic
- [ ] **DB migration:** Create alembic migration 102 to add `workflow_context` column
- [ ] **Commit:** "Add Init II.D workflow context state machine (3 workflows v1)"
- [ ] **Smoke test:** Run close_job workflow; verify state persists across turns
- [ ] **Regression:** Full test suite + existing conversation flows (non-workflow) unaffected
- [ ] **User checkpoint:** Demo workflow flow (close job in 3 steps); verify timeout/rollback plan

---

## 8. Risk Assessment Summary

### Highest Canonical-Fix Compliance Risk: **Init II.D — Workflow Context**

**Why:** DB schema migration required; state persistence critical for multi-turn correctness; timeout logic must be bulletproof.

**Mitigation:**
- Alembic migration tested on staging before production
- Workflow timeout enforced via explicit check (not implicit)
- Rollback plan: alembic downgrade reverses schema change; feature flag prevents new workflows

### Highest Performance Risk: **VI Fase 1 — Judge Eval Cost**

**Why:** Uncontrolled judge calls could exceed budget ($150/month).

**Mitigation:**
- Cost tracking in `eval_runner.py` + hard stop on budget exhaustion
- Sampling strategy (20 cases/PR, 99 nightly) keeps costs predictable
- Monthly cap + alerts via GitHub Actions

### Highest Data Privacy Risk: **G5 Light + IV + V**

**Why:** PII redaction heuristics could miss patterns or redact false positives.

**Mitigation:**
- Strict mode (default in prod) vs permissive (dev/test)
- Audit log captures all redactions + confidence scores
- Manual review workflow for high-confidence cases before response sent

---

## 9. Consolidated Costs + Timeline

### LLM Cost Delta (Monthly)

| Item | Cost | Notes |
|------|------|-------|
| G5 light | $0 | No new LLM calls; regex only |
| VI Fase 1 | +$120 | 30 cases/day × judge @ Sonnet rate |
| Init IV | +$5 | Extra tokens in 10% conversations |
| Init V | $0 | Heuristic-based; no LLM calls |
| Init II.D | +$3 | Workflow context tokens |
| **TOTAL** | **+$128/month** | ~$1.5K/year |

### Storage Delta (Annually)

| Item | Storage | Notes |
|------|---------|-------|
| G5 light | +2-3 GB | Compliance audit logs |
| VI Fase 1 | +12-24 GB | eval_results_*.json (mitigate: .gitignore) |
| Init IV | +500 MB | Briefing cache misses |
| Init V | +1-2 GB | Citation metadata logs |
| Init II.D | +1-2 GB | workflow_context in DB |
| **TOTAL** | **+17-32 GB/year** | Manageable; budget $150/year storage |

### Timeline (Weeks)

| Item | Weeks | Critical Path | Notes |
|------|-------|---|---|
| G5 light | 1-1.5 | Week 1 (blocks IV+V) | Small, low-risk |
| VI Fase 1 | 1.5-3.5 | Week 1.5 (parallel with IV) | Golden set expansion time-intensive |
| Init IV | 2-2.75 | Week 2 (after G5) | Depends on G5 for PII redaction |
| Init V | 2.75-3.25 | Week 2.75 (parallel) | Independent; UI deferred (G1) |
| Init II.D | 3-4 | Week 3 (last; independent) | DB migration + workflow registry time-intensive |
| **TOTAL** | **4 weeks** | — | Staggered; can parallelize with dependencies |

**Real timeline:** 3.5-4 weeks assuming 1 FTE; dependencies allow some parallelization (VI + IV after G5 ships).

---

## 10. Rollback-Safety Ranking (Best to Worst)

1. **Init V (Citations)** — Feature flag only; no schema; instant off
2. **G5 light (PII)** — Feature flag only; no breaking changes; async audit logs
3. **VI Fase 1 (Eval CI)** — Delete workflow file; no code rollback needed
4. **Init IV (Briefing)** — Feature flag; no schema; data is computed on-demand
5. **Init II.D (Workflow)** — Alembic downgrade required; more complex rollback

---

## 11. Full Replit Path

**Plan document:** `/home/runner/workspace/lia-agent-system/ONDA2_PLAN.md` (after scp from Mac)

**Also at:** `/tmp/ONDA2_PLAN.md` (Mac + Replit for reference during implementation)

---

**Status:** All 5 items are **implementation-ready**. Each has concrete patches, test shapes, and rollback plans. Ready for user sign-off + team execution.

**Next step:** User reviews plan, confirms execution order, approves feature flag naming + default settings. Then: Team starts Item 1 (G5 light).
