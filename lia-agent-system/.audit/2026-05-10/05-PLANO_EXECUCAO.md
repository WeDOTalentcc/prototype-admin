# 05 — Plano de Execução — Resolver TODAS as pendências

> **Plano detalhado para fechar os 20 achados da auditoria 2026-05-10 (Fases 0-4).** Operacional: cada item tem pre-flight + TDD red→green + sensor + acceptance + commit canonical.
>
> **Data:** 2026-05-10
> **Replit canonical HEAD:** `32a346617` (audit fase-4) → branch `feat/benefits-prv-canonical`
> **Princípio canonical:** **código é fonte de verdade.** Cada task valida via grep/sensor SSH ANTES e DEPOIS da mudança.
> **TDD obrigatório:** red phase → fix → green phase → sensor green → commit. Sem skip.

---

## Skills aplicadas (mapeamento canonical)

| Skill | Quando aplicar | Items afetados |
|---|---|---|
| **`harness-engineering`** (auto) | Toda task — classificar guide × sensor; preferir computacional | Todos 20 |
| **`production-quality:modules:compliance-risk`** | LGPD, EU AI Act, EEOC, FairnessGuard, PII | P0-1, P0-3, P1-3, F3-1, F3-3, F3-4 |
| **`production-quality:modules:ai-architecture`** | Agents/tools — register_agent, inheritance, FairnessGuard | P0-3, P1-2 |
| **`production-quality:modules:canonical-standards`** | Padrões cross-domain (HITL decorador, ADR-001) | P1-4, P2-1, P2-2, P2-3 |
| **`production-quality:modules:backend-quality`** | Performance, error handling, async | P0-2, P1-5, P2-4 |
| **`tdd-workflow`** (red→green→refactor) | TODAS | Todos 20 |
| **`engineering:code-review`** | Pre-merge cada PR | Todos 20 |
| **`engineering:testing-strategy`** | Cobertura nova de tests | P1-5, F3-3 |
| **`/create-canonical-agent`** | Se decidir completar `recruitment_campaign` agent | P2-3 |
| **`engineering:debug` / `gsd:debug`** | Backup se fix falhar em runtime | Todos (defensivo) |
| Memory `feedback_code_is_truth.md` | Validar via grep/sensor antes de afirmar status | Todos |
| Memory `project_canonical_clone_no_modify.md` | Garantir que edits ficam no Replit canonical, não no clone GitHub local | Todos |

---

## Princípios operacionais

1. **Replit é canonical** — todos os fixes vão na branch `feat/benefits-prv-canonical` no Replit (`/home/runner/workspace/`). Sem touch no clone GitHub local (REGRA ZERO).
2. **Sem `git push`** — Paulo pusha quando quiser (REGRA ABSOLUTA CLAUDE.md).
3. **Atomic commits** — 1 task = 1 commit (rastreabilidade + reversibilidade).
4. **TDD red→green obrigatório** — toda mudança comportamental tem teste failing antes do fix.
5. **Sensor green obrigatório** — quando há sensor relevante, ele DEVE estar green pós-fix; senão o commit não vai.
6. **Pre-flight discovery** — antes de qualquer task, grep/cat para confirmar estado atual. Não confiar em docs ou memória.
7. **Boy Scout** — ao tocar em arquivo, fixar P2 secundários no mesmo commit (não criar tech debt novo).
8. **Anti-sycophancy** — se algum achado original era falso positivo, descarta-se com justificativa. Não inventar trabalho.

---

## Falsos positivos descartados pré-execução

Durante pre-flight discovery (2026-05-10) descobrimos:

### ❌ P1-1 descartado — `pipeline_monitor.py:299`
**Original (Fase 1):** "auto_rejection sem HITL gate, viola Inegociável #2".

**Realidade (re-leitura código):**
```python
auto_rejection = communication_rules.get("auto_rejection_feedback", True)
if auto_rejection:
    return events  # skip detector se feedback automático já está ativo
```

A função `_detect_rejection_pending_feedback` é um **detector de gaps** — só dispara quando `auto_rejection_feedback=False`. Procura candidatos rejeitados há +48h SEM feedback enviado, gera alertas proativos. **Não está fazendo auto-rejection.** Lógica correta. Achado original foi mal-interpretação do agent Fase 1.

**Decisão:** **REMOVER P1-1 do roadmap.** Reduz lista para 19 itens.

### Hipótese sobre P1-2 (validar em Sprint 2.2)
- `talent_react_agent.py` é **shim de backward-compat** (re-export de `TalentFunnelReActAgent`, R-013 2026-05-08). Sensor pode estar verificando a classe alias, não o canonical real. Provavelmente fix é só adicionar marker `# G7 ok: shim re-export`.
- `automation_react_agent.py` JÁ tem inheritance correta. Falta apenas `@register_agent("automation")`.
- `autonomous_react_agent.py` precisa validação similar.

Em vez de assumir 7 violations × 3 agents requer overhaul, esperar fix XS-S total.

---

## Estado consolidado pós-pre-flight

| Severity | Count | Esforço total estimado | Itens |
|---|---|---|---|
| 🔴 **P0** | **3** | ~3 sprints | P0-1, P0-2, P0-3 |
| 🟡 **P1** | **5** (era 6, P1-1 descartado) | ~2 sprints | P1-2, P1-3, P1-4, P1-5, F3-1 |
| 🟢 **P2** | **7** | ~1.5 sprint | P2-1..P2-7 (inclui F2-1) |
| 🔵 **P3** | **4** | ~1 sprint | F3-2, F3-3, F3-4, F3-5 |

**Total estimado para fechar TODAS pendências (P0+P1+P2+P3):** ~7-8 sprints (14-16 semanas).

---

## ONDA 1 — Compliance Crítico (3 sprints, 6 semanas)

**Meta:** zero P0. Reduz risco LGPD/multi-tenancy/Inegociáveis #3-#4.

---

### Sprint 1.1 — P0-1: PII em logs (25+ violations / ~13 files)

**Skills:** `compliance-risk` + `harness-engineering` + `tdd-workflow`
**Esforço:** L (4-5 dias)
**Dependências:** nenhuma
**Inegociável afetado:** #4 (PII masking 100%) + Production Readiness Gates 3 + 18

#### Pre-flight (4h)
1. **Confirmar lista exaustiva de violations:**
   ```bash
   ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_no_pii_in_logs.py 2>&1 | grep "f-string log" > /tmp/p0-1-violations.txt; wc -l /tmp/p0-1-violations.txt'
   ```
2. **Read** `app/shared/pii_masking.py` — confirmar `mask_pii_text`, `strip_pii_for_llm_prompt` API
3. **Read** `app/shared/observability/pii_masking_filter.py` (se existir) ou planejar criar
4. **Read** ADR-006 em `docs/adr/006-*.md` — patterns canonical
5. **Test feature impact:** rodar grep para identificar quais services consumam logs (downstream impact)

#### Lista de arquivos afetados (25 violations confirmadas)
| Arquivo | Violations | Tipo PII detectado |
|---|---|---|
| `app/api/v1/merge_webhooks.py` | 4 (lines 88, 120, 164, 210) | webhook payload + candidate data |
| `app/api/v1/communications.py` | 4 (lines 81, 335, 337, 388, 534) | email, recipient |
| `app/api/v1/approvals.py` | 4 (lines 146, 255, 332, 406) | user_id, candidate_id, comment |
| `app/api/v1/automations.py` | 2 (lines 161, 266) | candidate_id |
| `app/api/v1/big_five.py` | 2 (lines 259, 487) | candidate_id |
| `app/api/v1/company_departments.py` | 2 (lines 81, 172) | dept name + creator email |
| `app/api/v1/admin_platform.py` | 1 (line 125) | admin email |
| `app/api/v1/attachments.py` | 1 (line 101) | file owner |
| `app/api/v1/client_users.py` | 1 (line 404) | user email |
| `app/api/v1/communication_matrix.py` | 1 (line 223) | recipient |
| `app/api/v1/company.py` | 1 (line 169) | company name + admin |
| `app/api/v1/company_approvers.py` | 1 (line 72) | approver email |

#### Tasks TDD

**T1.1.1 — Criar `PIIMaskingFilter` para root logger** (1d, sensor primary)
1. **Red phase:**
   ```python
   # tests/unit/test_pii_masking_filter.py
   def test_filter_masks_email_in_log_message():
       record = LogRecord(msg=f"Sending email to test@example.com")
       filter = PIIMaskingFilter()
       filter.filter(record)
       assert "test@example.com" not in record.msg
       assert "[EMAIL]" in record.msg
   ```
   Esperado: FAIL (filter não existe).
2. **Implement:** `app/shared/observability/pii_masking_filter.py`
   - Class `PIIMaskingFilter(logging.Filter)`
   - `filter(record)` aplica `strip_pii_for_llm_prompt(record.msg)` + cada `record.args`
   - Aplica também a `extra` keys com value não-mascarado (defesa em profundidade)
3. **Boundary:** registrar filter no root logger em `app/main.py`:
   ```python
   import logging
   from app.shared.observability.pii_masking_filter import PIIMaskingFilter
   logging.getLogger().addFilter(PIIMaskingFilter())
   ```
4. **Green phase:** test passa.
5. **Commit:** `feat(pii-masking): add PIIMaskingFilter to root logger (P0-1 ADR-006)`

**T1.1.2 — Migration script para fix em batch** (4h)
1. Criar `scripts/migrate_pii_logs_adr006.py`:
   - Parsear arquivo Python via AST
   - Detectar f-string logs com variáveis (regex `logger\.(info|warning|debug|error)\(f"[^"]*\{[^}]*\}[^"]*"`)
   - Sugerir conversão: `logger.info(f"User {user.email} logged in")` → `logger.info("User logged in", extra={"user_email_masked": mask_email(user.email)})`
   - Output: diff por arquivo (não aplica — humano valida)

**T1.1.3 a T1.1.14 — Per-file fix (12 arquivos × ~30min = 6h)**
Para cada arquivo da tabela acima:
1. **Read** arquivo, identificar f-string logs flagados
2. **Refactor manual** seguindo padrão:
   ```python
   # ANTES
   logger.info(f"✅ Email sent to {request.to_email} for company {company_id}")

   # DEPOIS
   logger.info(
       "Email sent successfully",
       extra={
           "to_email_hash": hashlib.sha256(request.to_email.encode()).hexdigest()[:8],
           "company_id": company_id,
       }
   )
   ```
3. **Test:** rodar local `python -c "import app.api.v1.<module>"` para garantir não quebra
4. **Commit por arquivo:** `fix(pii-logs): mask PII in <file>.py logs (P0-1, ADR-006)`

**T1.1.15 — Validar sensor green** (30min)
```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_no_pii_in_logs.py 2>&1 | tail -3'
```
Esperado: `OK — scanned X files, 0 violations`.

**T1.1.16 — Smoke test runtime** (30min)
1. Trigger request real que antes logava PII (ex: `POST /api/v1/communications/email`)
2. `tail -f /tmp/lia-backend-stdout.log` durante o request
3. Verificar logs **não contém** email/PII em texto plano

#### Acceptance criteria
- [ ] Sensor `check_no_pii_in_logs` retorna 0 violations
- [ ] Test `test_pii_masking_filter.py` passing
- [ ] Smoke test runtime confirma zero PII em logs durante request real
- [ ] CI green em todos os arquivos modificados

#### Risk + mitigation
| Risk | Probability | Mitigation |
|---|---|---|
| Filter introduz overhead em logs (latency) | Baixa | Benchmark: 10k logs/s antes vs depois, target <5% slowdown |
| Filter mascara dados que devem ficar visíveis (debug) | Média | `LIA_LOG_PII_LEVEL=debug` env permite bypass em dev local |
| Migration script aplica fix incorreto | Média | NUNCA aplicar automaticamente — apenas gera diff humano-validado |

#### Sensors guard (harness-engineering)
- ✅ Computational guard: `PIIMaskingFilter` em runtime (defesa em profundidade)
- ✅ Sensor: `check_no_pii_in_logs` BLOCKING em CI (já existe)
- ✅ Test: `test_pii_masking_filter.py` regression test

---

### Sprint 1.2 — P0-2: Multi-tenancy bypass (~80-100 endpoints reais)

**Skills:** `compliance-risk` + `backend-quality` + `tdd-workflow`
**Esforço:** L (5-7 dias)
**Dependências:** nenhuma
**Inegociável afetado:** Multi-tenancy (defesa-em-profundidade) + Production Readiness Gate 4

#### Pre-flight obrigatório (1d)
1. **Lista completa via sensor:**
   ```bash
   ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_company_id_in_routes.py 2>&1 > /tmp/p0-2-violations.txt; grep -cE "^\s*app/" /tmp/p0-2-violations.txt'
   ```
2. **Triagem manual em 4 categorias** (cada endpoint flagado):
   - **A. REAL gap** — recurso tenant-scoped sem check (recruitment_stages, ats_integration) → fix code
   - **B. Public intencional** — trust_center, semantic_search NLP tools → marker `# multi-tenancy: <reason>`
   - **C. Admin platform-level** — clients_crud, admin_platform → marker + role check
   - **D. Falso positivo** — pode ser que ALLOWLIST do sensor esteja desatualizada

3. **Output triagem:** `/tmp/p0-2-triage.csv` com colunas `endpoint, category, action, reason`

#### Tasks TDD

**T1.2.1 — Triagem completa (1d)**
- Output: spreadsheet/CSV com cada endpoint × categoria × ação
- Validar com Paulo se A/B/C/D suficiente

**T1.2.2 — Categoria B+C: markers em batch (1d)**
- Para cada endpoint público intencional ou admin platform-level:
  ```python
  # multi-tenancy: public transparency page (trust_center)
  @router.get("/trust-center/overview")
  async def get_trust_center_overview(...):
      ...
  ```
- Boy Scout: validar que role check existe em endpoints C (admin)
- Commit: `chore(multi-tenancy): mark <N> endpoints as intentional public/admin (P0-2 triage)`

**T1.2.3 — Categoria A: real fix (3-4d)**
Para cada endpoint REAL gap:

1. **Red phase test E2E cross-tenant:**
   ```python
   # tests/e2e/test_multi_tenancy_<endpoint>.py
   async def test_endpoint_blocks_cross_tenant_access(client_company_a, client_company_b, resource_b):
       response = await client_company_a.patch(f"/api/v1/recruitment_stages/{resource_b.id}", json={...})
       assert response.status_code in (403, 404)  # NUNCA 200 com dados de B
       assert resource_b.name not in response.text
   ```

2. **Fix code:**
   ```python
   from app.auth.dependencies import _require_company_id

   @router.patch("/recruitment_stages/{stage_id}")
   async def update_stage(
       stage_id: int,
       payload: StageUpdate,
       company_id: str = Depends(_require_company_id),  # ← adicionar
       db: AsyncSession = Depends(get_tenant_db),
   ):
       stage = await stage_repo.get_for_company(db, stage_id, company_id)
       if not stage:
           raise HTTPException(404)
       ...
   ```

3. **Green phase:** test passing.

4. **Sensor green:** `python scripts/check_company_id_in_routes.py` retorna 0 violations.

5. **Commit por arquivo (ou grupo lógico):**
   `fix(multi-tenancy): require company_id in recruitment_stages/* (P0-2)`

#### Lista priorizada (categoria A — exemplos)
- `recruitment_stages/stages_crud.py` (8 endpoints) — alta prioridade
- `recruitment_stages/stages_substatus.py` (4 endpoints)
- `recruitment_stages/stages_transition.py:266`
- `recruitment_stages/stages_ats_mapping.py:79`
- `recruitment_stages/stages_return_events.py` (3 endpoints)
- `recruitment_stages/stages_pipeline.py:386`
- `ats.py` (3 endpoints) — alta prioridade
- `clients_crud.py` (8 endpoints) — categoria C com role check
- `talent_funnel.py:53`

#### Acceptance criteria
- [ ] Sensor `check_company_id_in_routes` retorna 0 violations (após markers + fixes)
- [ ] Test E2E cross-tenant para top 10 endpoints fix-real passing
- [ ] RLS Postgres role continua ativo em runtime (logs)

#### Risk + mitigation
| Risk | Probability | Mitigation |
|---|---|---|
| Marker abusado para suprimir gaps reais | Alta | Code review obrigatório por security-champion |
| Fix quebra endpoint que aceita company_id em path | Média | Test E2E antes do merge |
| Triagem demora — 1580 endpoints | Alta | Auto-triage via heuristic (URL pattern) + human spot-check |

---

### Sprint 1.3 — P0-3: Offer domain SEM FairnessGuard

**Skills:** `compliance-risk` + `ai-architecture` + `canonical-standards` + `tdd-workflow`
**Esforço:** M (2-3d)
**Dependências:** nenhuma
**Inegociável afetado:** #3 (FairnessGuard 100%) + Crença C02

#### Pre-flight (2h)
1. **Read template:** `app/domains/job_creation/compliance.py` (11.6KB) — 100% reutilizável
2. **Read** `app/domains/offer/domain.py` — entender lifecycle
3. **Read** `app/domains/offer/tools/send_offer.py` — entry point onde aplicar FG
4. **Confirm absence:**
   ```bash
   ssh replit-wedo-0405 'grep -rn "FairnessGuard" /home/runner/workspace/lia-agent-system/app/domains/offer/' # esperado: vazio
   ```

#### Template reutilizável (job_creation/compliance.py)
Estruturas canonical:
```python
def mask_pii_for_llm(text: Optional[str]) -> str
class FairnessCheck(@dataclass): is_blocked, category, blocked_terms, educational_message
def _run_fairness_guard(text: str) -> FairnessCheck
def check_input_fairness(text: str) -> FairnessCheck
def check_output_fairness(text: str) -> FairnessCheck
def emit_offer_audit(offer_id, company_id, prompt_hash, model, decision_type)
```

#### Tasks TDD

**T1.3.1 — Red phase: test bias block** (2h)
```python
# tests/domains/offer/test_offer_compliance.py
async def test_send_offer_blocks_biased_text():
    biased_offer = OfferDraft(
        salary_text="Apenas para homens com mais de 30 anos",  # bias explícito
        ...
    )
    with pytest.raises(FairnessGuardBlockedError):
        await offer_service.send_offer(biased_offer)
```
Esperado: FAIL (FairnessGuard não invocado).

**T1.3.2 — Implementar `app/domains/offer/compliance.py`** (4h)
Copiar estrutura de `job_creation/compliance.py`, adaptar:
- `mask_pii_for_llm()` igual
- `_run_fairness_guard()` igual
- `check_input_fairness(offer_text)` — validar texto da oferta antes do LLM
- `check_output_fairness(generated_offer)` — validar texto gerado
- `emit_offer_audit(offer_id, company_id, model, ...)` — `decision_type="offer_send"`

**T1.3.3 — Wire em `domain.py:_dispatch_tool`** (2h)
```python
async def _dispatch_tool(self, tool_name: str, args: dict, ...):
    if tool_name in ("send_offer", "update_offer_draft", "prepare_offer_manual_send"):
        offer_text = args.get("salary_text", "") + args.get("benefits_text", "")
        check = check_input_fairness(offer_text)
        if check.is_blocked:
            return {
                "blocked": True,
                "reason": check.educational_message,
                "category": check.category,
            }
    result = await super()._dispatch_tool(tool_name, args, ...)
    # ... emit audit pós-send
    return result
```

**T1.3.4 — Green phase + audit log** (2h)
- Test T1.3.1 passing
- Audit log gerado em `audit_decisions` table
- Sensor `check_agent_compliance` continua green (offer não tem agent canonical mas usa Fairness via domain dispatch)

**T1.3.5 — Smoke test runtime** (1h)
- Enviar offer via API com texto enviesado → expect 422/400 com mensagem educativa
- Verificar audit log gerado em DB

#### Acceptance criteria
- [ ] grep `FairnessGuard` em `offer/` retorna ≥3 hits
- [ ] Test bias block passing
- [ ] Audit log generated por offer lifecycle
- [ ] Sensor `check_agent_compliance` ainda green
- [ ] Documentation: docstring em `compliance.py` cita LGPD Art.12 + EU AI Act Art.13

#### Risk + mitigation
| Risk | Probability | Mitigation |
|---|---|---|
| Fairness check bloqueia offer válida (false positive) | Baixa | Usar mesma camada do job_creation (já calibrada) |
| Audit log explode storage | Baixa | Audit table tem TTL 7y (LGPD) — esperado growth controlado |

---

## ONDA 2 — Governança fortalecimento (2 sprints, 4 semanas)

### Sprint 2.1 — P1-3 (Layer 3) + P1-4 (HITL decorador)

**Skills:** `ai-architecture` + `canonical-standards` + `tdd-workflow`
**Esforço:** M-S (3d)

#### P1-3 — Promover FairnessGuard Layer 3 default-on (1d)

**Pre-flight:**
- Verify `lia_config/config.py` settings location
- Read tests existentes: `tests/unit/test_fairness_guard_fail_closed.py:128` + `tests/test_sprint2_fairness_agent.py:497`
- Cost analysis: Haiku tokens × estimated high-impact actions/day (sourcing search + JD import) → budget OK

**Tasks:**
1. **Red:** test `test_layer3_default_on.py` — high-impact action sem flag → expect Layer 3 invocado
2. **Fix:** `app/shared/compliance/fairness_guard.py:824`:
   ```python
   _layer3_enabled = getattr(_settings, "FAIRNESS_LAYER3_ENABLED", True)  # ← True default
   ```
3. **Add cap:** token budget per company para Layer 3 (defesa custo)
4. **Green:** test passing
5. **Sensor:** `check_agent_compliance` continua green

**Commit:** `feat(fairness): promote Layer 3 to default-on for high-impact actions (P1-3)`

#### P1-4 — Decorador `@require_hitl` para domain tools (2d)

**Pre-flight:**
- Read `app/domains/cv_screening/services/hitl_service.py` (canonical HITLService)
- Read `app/api/v1/lia_assistant_flags.py:72-91` (SENSITIVE_FLAGS_REQUIRING_HITL pattern)
- List tools com `SafetyCategory.HIGH_IMPACT`

**Tasks TDD:**
1. **Red:** test `test_require_hitl_decorator.py`:
   ```python
   @require_hitl(safety_category=SafetyCategory.HIGH_IMPACT)
   async def my_high_impact_tool(...):
       ...

   async def test_blocks_without_approval(self):
       result = await my_high_impact_tool(...)
       assert result["status"] == "pending_human_approval"
   ```
2. **Implement** `app/shared/hitl_decorator.py`:
   - `@require_hitl(safety_category=...)` decorator
   - Cria `HITLPendingAction` no DB
   - Retorna `{"status": "pending_human_approval", "pending_id": ...}`
   - User aprova via `POST /api/v1/hitl/approve/{pending_id}`
3. **Apply** em `offer.send_offer` (compatible com P0-3 fairness check)
4. **Green:** tests + integration smoke test

**Commit:** `feat(hitl): add @require_hitl decorator for domain tools (P1-4)`

---

### Sprint 2.2 — P1-2: Agent compliance gaps (3 agents, mas mostly XS)

**Skills:** `ai-architecture` + `tdd-workflow`
**Esforço:** S (1-2d) — após pre-flight discovery muito menor que parecia

#### Pre-flight
- Read cada agent file
- Triagem real: shim vs canonical missing
- Sensor `check_agent_compliance` output detalhado

**Tasks:**

**T2.2.1 — `automation_react_agent.py`** (30min)
- Já tem inheritance correta (`LangGraphReActBase, EnhancedAgentMixin`)
- Adicionar 1 linha: `@register_agent("automation")` decorator antes da class
- Sensor green
- Commit: `fix(agents): add @register_agent decorator to AutomationReActAgent (P1-2)`

**T2.2.2 — `autonomous_react_agent.py`** (30min)
- Validar inheritance — provavelmente igual automation
- Adicionar `@register_agent("autonomous")` decorator
- Commit similar

**T2.2.3 — `talent_react_agent.py` (provavelmente shim)** (30min)
- Confirmar é shim de `TalentFunnelReActAgent`
- Adicionar primeira linha: `# G7 ok: shim re-export — canonical is talent_funnel_react_agent.py (R-013 2026-05-08)`
- Sensor green
- Commit: `chore(agents): mark talent_react_agent as shim re-export exempt (P1-2)`

**Total esforço P1-2: 1.5h** (não 2d como estimado).

---

### Sprint 2.3 — F3-1: Anti-sycophancy 5/8 benchmarks faltantes

**Skills:** `compliance-risk` + `tdd-workflow`
**Esforço:** M (2d)

#### Pre-flight
- List atual: 3/8 benchmarks (Gupy 27, LinkedIn 17, Robert Half 1)
- Faltam: ABRH, GPTW, Glassdoor, IBGE, PNAD, MTE/CAGED
- Read `app/prompts/domains/{analytics,hiring_policy,company_settings,recruiter_assistant,sourcing,pipeline_transition}.yaml`

#### Tasks TDD

**T2.3.1 — Red phase: golden snapshot tests** (4h)
```python
# tests/prompts/test_anti_sycophancy_benchmarks.py
EXPECTED_BENCHMARKS = ["ABRH", "GPTW", "Gupy", "Robert Half", "LinkedIn",
                       "Glassdoor", "IBGE", "PNAD", "MTE", "CAGED"]

@pytest.mark.parametrize("prompt_file", [
    "analytics.yaml",
    "hiring_policy.yaml",
    "company_settings.yaml",
])
def test_prompt_covers_8_benchmarks(prompt_file):
    text = load_yaml(prompt_file)
    found = [b for b in EXPECTED_BENCHMARKS if b in text]
    assert len(found) >= 6, f"{prompt_file} cobre apenas {found} benchmarks"
```

**T2.3.2 — Enriquecer prompts** (1d)

**`analytics.yaml`** — adicionar seção:
```yaml
benchmarks_setoriais:
  - "Pesquisa Salarial Robert Half (executive talent)"
  - "GPTW (Great Place to Work) — engagement + cultura"
  - "ABRH-Brasil — Pesquisa de Recursos Humanos"
  - "Gupy Insights — métricas de funil em RH"
  - "LinkedIn Economic Graph — labor market trends"
  - "Glassdoor — salário + employer review"
  - "IBGE/PNAD — emprego formal Brasil"
  - "MTE/CAGED — admissões/desligamentos formal"
```

**`hiring_policy.yaml`** — referenciar 8 fontes em `validate_against_benchmarks` action.

**`pipeline_transition.yaml:39`** — expandir ANTI-SYCOPHANCY com lista 8.

**`company_settings.yaml`** — adicionar benchmarks ABRH para benefits.

**T2.3.3 — Green phase + commit** (2h)
- Tests passam
- Commit: `feat(prompts): cover 8 anti-sycophancy benchmarks per Crença #11 (F3-1)`

---

## ONDA 3 — Qualidade + cobertura (1.5 sprints, 3 semanas)

### Sprint 3.1 — P1-5: `job_management` 0 testes específicos

**Skills:** `testing-strategy` + `tdd-workflow` + `engineering:code-review`
**Esforço:** M (3d)

#### Pre-flight
- Verify `tests/domains/job_management/` ainda 0 files
- Read `app/domains/job_management/actions.py` — 29 actions
- Read `app/domains/job_management/agents/wizard_react_agent.py` — agent canonical
- Identify happy path + 2 edge cases por action critical

#### Tasks
**T3.1.1 — Setup** (4h)
- Criar `tests/domains/job_management/conftest.py` com fixtures (company, user, sample_job, JWT dev)

**T3.1.2 — Smoke test 29 actions** (1d)
- 1 happy path por action (mínimo) — ~29 testes
- Marcar com `@pytest.mark.smoke` para rodar em CI fast-path

**T3.1.3 — Integration test wizard E2E** (1d)
- Conversation flow: user → agent → tools → DB → response
- Cobrir create_job → update_job → publish_job
- Cobrir FairnessGuard pre-check em update_job

**T3.1.4 — Edge cases prioritárias** (4h)
- Job inexistente, company errada (multi-tenancy), JD com bias

#### Acceptance
- [ ] ≥15 tests novos em `tests/domains/job_management/`
- [ ] Coverage report: ≥60% para `app/domains/job_management/`
- [ ] CI green

---

### Sprint 3.2 — P2 cleanup (7 itens)

**Skills:** `canonical-standards` + `compliance-risk` + `tdd-workflow`
**Esforço:** S-M cada (~5d total)

| ID | Task | Esforço |
|---|---|---|
| P2-1 | `hiring_policy` FairnessGuard invokes em check_diversity_targets + validate_job_requirements | 4h |
| P2-2 | `ats` webhook adicionar `_require_company_id` + signature | 2h |
| P2-3 | `recruitment_campaign` decisão arquitetural: complete OU wrapper de job_management | M (planejamento + impl 2-3d) |
| P2-4 | `company_settings` consent gate em import_benefits | 1d |
| P2-5 | ExpandableAIPrompt investigation (frontend-only validation) | 2h |
| P2-6 | Prod env block synthetic dev_mode (sensor strengthen) | 4h |
| F2-1 | Frontend route 404 audit + redirects | 1d |

**Para P2-3:** considerar `/create-canonical-agent` skill se decidir completar.

---

## ONDA 4 — Backlog (P3 + capacidades novas)

### F3-2 — LLM fallback config produção
**XS (1h)** — adicionar Replit Secrets: `OPENAI_API_KEY`, `GEMINI_API_KEY`. Re-test fallback chain via `/api/v1/health`.

### F3-3 — WCAG 2.1 AA visual audit
**M (2-3d)** — Lighthouse a11y por página + manual screen reader (pt-BR + en-US). Skills: `engineering:testing-strategy` + `production-quality:frontend-quality`.

### F3-4 — EEOC Disparate Impact (chi-square)
**M (2-3d)** — implementar `_chi_square_test()` em `bias_audit_service.py`. Schema migration: column `disparate_impact_data: JSONB`. Tests 8 casos.

### F3-5 — Backup/restore drill + SAST
**S (1d)** — Postgres standby validation + run SAST + document outputs.

### Capacidades novas (Y3-Y4 plano antigo, ainda relevantes)
- Confidence Calibration 14 agentes (D2 antigo) — 12h
- Score breakdown clicável funil (E1 antigo) — 8h
- Análise comparativa visual side-by-side (D9 antigo) — 12h
- ML adaptativo loop feedback (D6 antigo) — 24h
- Benchmark salarial real Apify/Glassdoor (D7 antigo) — 16h
- Multi-Model per agent (E5 antigo) — 16h
- WSI assíncrono (E3 antigo) — 16h

Total backlog estratégico: ~120h ≈ 3 sprints.

---

## Tracking matrix (atualizar após cada commit)

| ID | Onda | Sprint | Status | Commit | Tests | Sensor |
|---|---|---|---|---|---|---|
| P0-1 | 1 | 1.1 | ⏳ Pendente | — | — | red |
| P0-2 | 1 | 1.2 | ⏳ Pendente | — | — | red (1580 flagged) |
| P0-3 | 1 | 1.3 | ⏳ Pendente | — | — | implícito |
| P1-1 | — | — | ❌ Descartado (FP) | — | — | — |
| P1-2 | 2 | 2.2 | ⏳ Pendente | — | — | red (7 violations) |
| P1-3 | 2 | 2.1 | ⏳ Pendente | — | — | partial |
| P1-4 | 2 | 2.1 | ⏳ Pendente | — | — | n/a |
| P1-5 | 3 | 3.1 | ⏳ Pendente | — | 0 → 15+ | n/a |
| F3-1 | 2 | 2.3 | ⏳ Pendente | — | — | golden snapshot |
| P2-1 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| P2-2 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| P2-3 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| P2-4 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| P2-5 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| P2-6 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| F2-1 | 3 | 3.2 | ⏳ Pendente | — | — | — |
| F3-2 | 4 | — | 🔵 Backlog | — | — | — |
| F3-3 | 4 | — | 🔵 Backlog | — | — | — |
| F3-4 | 4 | — | 🔵 Backlog | — | — | — |
| F3-5 | 4 | — | 🔵 Backlog | — | — | — |

---

## Anti-Sycophancy honesto: o que este plano NÃO promete

1. **Não prometemos zero P0 em 6 semanas se descobrirmos novos** — toda Sprint termina com re-run completo de sensores; novos P0 podem aparecer (ex: alguma migration nova que quebra ADR-029). Roadmap se ajusta.
2. **Não prometemos coverage 100% em job_management** — 15+ testes é alvo realista, não exaustivo. Coverage tool reportará gaps.
3. **Frontend audit visual deferido** — Preview MCP precisa setup; F3-3 fica para Sprint 4.
4. **Performance under load não validada** — Sprint 4 pode incluir load test se Paulo priorizar.
5. **Backup restore drill operacional** — F3-5 valida restore mas não Disaster Recovery completo.
6. **EEOC chi-square pode revelar disparate impact não previsto** — F3-4 pode disparar P0 inesperado.

---

## Critérios de fim do plano

Este plano está **completo** quando:
- [ ] Todos os 19 itens (3 P0 + 5 P1 + 7 P2 + 4 P3) com status `✅ Done` ou `⚠ Documented blocker`
- [ ] Sensores governança: 36/36 GREEN ou WARN documentado
- [ ] Inegociáveis: 7-8/8 PASS (WCAG depende de F3-3)
- [ ] Production Readiness Gates: 17-18/18 PASS
- [ ] LGPD/EU AI Act/EEOC: zero risco LEGAL CRÍTICO
- [ ] Documentação: `MEMORY.md` atualizada com fixes aplicados

---

## Próxima ação

**Executar Onda 1 — Sprint 1.1 P0-1 PII em logs.**

Comando inicial:
```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python scripts/check_no_pii_in_logs.py 2>&1 | tee /tmp/p0-1-baseline.txt'
```

Confirmar baseline → começar T1.1.1 (PIIMaskingFilter unit test red phase).

---

**Fim do 05-PLANO_EXECUCAO.md.**
**Approval Paulo necessária antes de executar Onda 1.**
