# Porte de Segurança, LGPD, Fairness e Guardrails — de `recruiter_agent_v5` para `lia-agent-system`

**Data:** 2026-04-20
**Autor:** Auditoria técnica automatizada
**Status:** Plano de migração (reference guide)
**Origem:** `/home/victhor/ats_mercado/recruiter_agent_v5`
**Destino:** `/home/victhor/ats_mercado/wedotalent02202026/lia-agent-system`

---

## 1. Objetivo

Este documento inventaria tudo que o projeto **`recruiter_agent_v5`** já resolve em termos de **segurança, LGPD, fairness, anti-prompt-injection, guardrails de agentes de IA, multi-tenant isolation, HITL, audit chain e observabilidade defensiva**, e especifica **como portar cada um desses blocos** para a arquitetura do `lia-agent-system` (FastAPI + LangGraph + Claude Sonnet 4.5).

O `recruiter_agent_v5` é mais antigo e saturou de práticas de compliance. O `lia-agent-system` já tem alguns equivalentes parciais (`app/shared/compliance/`, `app/shared/security/`, `app/shared/pii_masking.py`, `app/shared/prompt_injection.py`, `app/shared/tenant_guard.py`), mas falta o desenho coerente e o enforcement end-to-end. Este guia preenche a lacuna.

---

## 2. Sumário Executivo (o que tem de bom lá)

| # | Capacidade | Arquivo-âncora `recruiter_agent_v5` | Status no `lia-agent-system` |
|---|---|---|---|
| A1 | Prompt Injection Guard (23 padrões, NFKC normalize) | `src/shared/compliance/prompt_injection_guard.py` | Esqueleto em `app/shared/prompt_injection.py` — **enriquecer** |
| A2 | Domain Scope Guard (off-topic detector) | `src/services/domain_scope_guard.py` | **Ausente** — criar |
| B1 | PIIMasker 4-layer (logs + LLM + Presidio + rehydrate) | `src/shared/compliance/pii_masking.py` | Parcial em `app/shared/pii_masking.py` — **enriquecer** |
| B2 | PIISafeChatModel (pre-LLM interceptor) | `src/shared/compliance/llm_sanitizer.py` | **Ausente** — criar wrapper `BaseChatModel` |
| B3 | PlaceholderMap (rehydration bidirecional) | `src/shared/compliance/pii_rehydrate.py` | **Ausente** — criar |
| C1 | LGPD Purposes enum (5 finalidades) | `src/shared/compliance/purposes.py` | **Ausente** — criar |
| C2 | Consent enforcement (purpose → consent gate) | `src/shared/compliance/purpose_enforcement.py` | **Ausente** — criar |
| C3 | Granular Consent Service | `src/shared/compliance/lgpd/consent.py` | **Ausente** — criar |
| C4 | DSR Erasure Orchestrator | `src/shared/compliance/lgpd/erasure.py` | **Ausente** — criar |
| C5 | Purpose audit emission | `src/shared/compliance/audit_purpose.py` | **Ausente** — criar |
| D1 | Hash-chained Audit Trail (SHA-256) | `src/shared/compliance/audit/trail.py` | Parcial em `app/shared/governance/` — **enriquecer** |
| D2 | LangChain AuditCallbackHandler | `src/services/audit/audit_callback.py` | **Ausente** — criar |
| D3 | Audit Anonymizer (pseudo-anon para GCS) | `src/shared/compliance/audit_anonymizer.py` | **Ausente** — criar |
| E1 | Tenant ContextVar + `strict_tenant_safe` | `src/shared/tenant.py` | Esqueleto em `app/shared/tenant_guard.py` — **enriquecer com strict mode** |
| E2 | PostgreSQL Row-Level Security | `src/services/tenant_rls.py` + migration 001 | **Ausente** — criar migração + service |
| F1 | Tool Scopes (READ/WRITE/ADMIN/DANGEROUS) | `src/shared/security/tool_scopes.py` | **Ausente** — criar |
| F2 | Action scope filter | `src/domains/registry.py` | **Ausente** — integrar no tool registry |
| G1 | FairnessGuard 3-layer (explicit+implicit+semantic) | `src/shared/compliance/fairness_guard.py` | **Ausente** — criar |
| G2 | Fairness Probes (isomorphic pairs) | `src/evals/fairness_probes.py` | **Ausente** — criar |
| G3 | Bias Audit Service (4/5 rule + chi²) | `src/shared/compliance/bias_audit.py` | **Ausente** — criar |
| G4 | Model Drift Detection | `src/services/model_drift.py` | Parcial em `app/services/golden_drift_monitor.py` — **unificar** |
| H1 | HITL Service (pending actions) | `src/services/hitl.py` | **Ausente** — criar |
| H2 | HITL Gate decorator | `src/services/hitl_gate.py` | **Ausente** — criar |
| I1 | Outbound Guard (PII + fairness no output) | `src/shared/compliance/outbound_guard.py` | **Ausente** — criar |
| I2 | AI Disclosure automático | `src/shared/compliance/ai_disclosure.py` | **Ausente** — criar |
| I3 | Response Filter (tom informal PT-BR) | `src/services/response_filter.py` | **Ausente** — criar |
| J1 | LangSmith Guard (previne vazamento) | `src/shared/compliance/langsmith_guard.py` | **Ausente** — criar |
| J2 | Callback HMAC-signed + SSRF guard | `src/utils/callbacks.py` + `src/services/security.py` | **Ausente** — criar |
| K1 | Circuit Breaker + Token Budget | `src/services/circuit_breaker.py` | Parcial em `app/shared/resilience/` — **enriquecer** |
| K2 | Cost Ladder (provider fallback) | `src/services/cost_ladder.py` | **Ausente** — criar |
| L1 | CompositionalPromptBuilder 8-layer | `src/shared/prompts/compositional.py` | **Ausente** — criar |
| M1 | Lite Eval Runner (faithfulness/relevancy proxies) | `src/evals/lite_runner.py` | **Ausente** — criar em `tests-eval/` |
| M2 | Fairness CI Gate (divergence threshold) | workflow CI | **Ausente** — criar |
| N | Migrations SQL (audit_decisions, guardrail_rules) | `scripts/migrations/002_*.sql`, `003_*.sql` | **Ausente** — criar via Alembic |
| O | Supremacy Flags + Compliance Flags | `src/config/supremacy_flags.py`, `compliance_config.py` | **Ausente** — criar em `app/config/` |

> **Leitura rápida:** lia já tem ~20% do que o v5 tem. O grosso (80%) precisa ser portado/criado — e esse documento é o mapa.

---

## 3. Princípios de Migração

1. **Consultar ADR-017 (observabilidade canônica) antes de tocar em qualquer callback, log, ou tracing.** Tudo que for tracing, structured logging, LLM callbacks, agent monitoring, drift detection, token tracking, WSI observability **deve** viver em `app/shared/observability/` — nunca em outro lugar. Quebrar ADR-017 quebra o build (pre-commit + CI).
2. **Reaproveitar o que já existe no lia.** `app/shared/pii_masking.py`, `app/shared/prompt_injection.py`, `app/shared/tenant_guard.py`, `app/shared/compliance/`, `app/shared/security/`, `app/shared/governance/` já têm alguma estrutura — enriquecer, não duplicar.
3. **Flags primeiro, código depois.** Cada bloco grande entra atrás de uma `SUPREMACY_*` flag (default `True` em dev/staging, `False` em prod). Permite canário domain-a-domain.
4. **Defense in depth.** RBAC no banco (RLS) + em contextvar + em decorator do tool. Tenant isolation em 3 camadas. PII mask nos logs, no prompt e no output.
5. **TDD obrigatório.** Todo componente novo chega com teste (unit + property-based onde aplicável). Port dos testes de `tests/supremacy/` + `tests/properties/` do v5 em paralelo ao código.
6. **Código em inglês, comunicação em português.** (Conforme CLAUDE.md global.)

---

## 4. Mapa de Componentes — Detalhamento Técnico

Cada seção abaixo tem: **O que é → Como funciona no v5 → Onde portar no lia → Notas de integração.**

### A. Proteção contra Prompt Injection / Jailbreak

#### A.1 `PromptInjectionGuard`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/prompt_injection_guard.py`
- **Técnica:** regex puro (sem LLM) com **23 padrões nomeados** agrupados em 10 categorias: `jailbreak`, `data_exfiltration`, `bias_elicitation`, `score_manipulation`, `privilege_escalation`, `pii_extraction`, `fairness_bypass`, `system_override`, `role_manipulation`, `delimiter_injection`.
- **Detalhe importante:** normaliza o texto com **Unicode NFKC** + remove zero-width chars + combining marks antes do match — derrota ataque de homoglifos e invisible-chars.
- **API:**
  ```python
  ThreatDetection = PromptInjectionGuard.check(text)          # risk_level, category, matched_pattern
  safe_text = PromptInjectionGuard.sanitize(text)             # trunca 4000, normaliza
  safe_text, detection = PromptInjectionGuard.safe_process(text)
  ```
- **Escalada de risco:** se ≥3 categorias dão match, eleva de `MEDIUM → HIGH`. `HIGH/CRITICAL` bloqueia automaticamente.
- **Destino no lia:** `app/shared/prompt_injection.py` (já existe esqueleto). Port completo dos 23 padrões, da normalização NFKC, e da enumeração `RiskLevel`/`ThreatCategory`.
- **Integração:** chamar como **primeiro passo** em toda entrada de usuário no orchestrator/supervisor. Em LangGraph, vira um nó `input_guard_node` antes do nó de planner.
- **Padrões a portar (exemplos)** — incluem PT-BR e EN:
  - Jailbreak: `"ignore previous instructions"`, `"DAN mode"`, `"modo desenvolvedor"`, `"esqueça todas as regras"`.
  - Data exfiltration: `"export all data"`, `"dump db"`, `"liste todos os candidatos"`, `"postar todos dados"`.
  - Bias elicitation: `"ignore fairness"`, `"desativar compliance"`, `"prefer men over women"`, `"só mulheres"`.
  - Score manipulation: `"set score to 100"`, `"approve without evaluation"`, `"aprove tudo"`.
  - Privilege escalation: `"as an admin"`, `"como administrador"`, `"with root privileges"`.
  - PII extraction: `"show all CPF/CNPJ"`, `"extract RG"`, `"list all emails"`.
  - System override: delimitadores como \`\`\`system, `[SYSTEM]`, `"show your system prompt"`, `"reveal instructions"`.
- **Testes a portar:** `tests/supremacy/test_pii_property_adversarial.py` → `lia-agent-system/tests/compliance/test_prompt_injection_adversarial.py` (usar Hypothesis para fuzz de encoding).

#### A.2 `DomainScopeGuard`

- **Origem:** `recruiter_agent_v5/src/services/domain_scope_guard.py`
- **Técnica:** duas regex (whitelist recrutamento + blacklist off-topic), fallback para classifier LLM em ambíguos. Retorna `DomainScopeClassification(verdict, reason, via, confidence)`.
- **Destino no lia:** novo arquivo `app/shared/compliance/domain_scope_guard.py`.
- **Integração:** adicionar como node antes do planner no grafo autônomo. Retornos `OUT_OF_SCOPE` cortam a execução e devolvem mensagem padronizada.

---

### B. PII / Mascaramento / Anonimização (LGPD art. 6º V, 12)

#### B.1 `PIIMasker` (4 layers)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/pii_masking.py`
- **Layers:**
  1. **Logs:** regex para CPF, CNPJ, email, telefone (BR e internacional), RG, LinkedIn URL, GitHub URL → `***CPF***`, `***EMAIL***`, etc.
  2. **LLM prompt (stripping de quasi-identifiers):** ano de formatura, data de nascimento, endereço completo, CEP, bairro → `[ANO_FORMATURA]`, `[DATA_NASCIMENTO]`, `[ENDERECO]`, `[CEP]`, `[BAIRRO]`.
  3. **Presidio NER (opcional, feature-gated):** `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `LOCATION`, `DATE_TIME`, `NRP` (National Registration Number).
  4. **Rehydration:** `PlaceholderMap` para reverter seletivamente (ex: na hora de montar o corpo de e-mail para o candidato, reexpandir o nome real).
- **API:**
  ```python
  PIIMasker.mask_for_logs(text) -> str         # layer 1
  PIIMasker.mask_for_llm(text) -> str          # layer 1+2+3
  PIIMaskingFilter(logging.Filter)             # handler que aplica mask_for_logs no root logger
  install_global_pii_masking()                 # registra o filter em todos os handlers
  ```
- **Destino no lia:** `app/shared/pii_masking.py` (existe parcial). Completar com:
  - Os patterns BR (CPF, CNPJ, RG brasileiro, CEP, telefone com DDD).
  - Camada 2 (quasi-identifiers).
  - `PIIMaskingFilter` + `install_global_pii_masking()` chamado no startup do FastAPI (`app/main.py` lifespan).
- **Dependências:** `presidio-analyzer`, `presidio-anonymizer` (opcionais, atrás de flag `PII_PRESIDIO_ENABLED`).
- **Testes a portar:** `test_pii_masking_br.py`, `test_pii_default_on.py`, `test_pii_property_adversarial.py`.

#### B.2 `PIISafeChatModel` — Pre-LLM interceptor (ADR-009)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/llm_sanitizer.py`
- **Técnica:** subclass de `langchain_core.language_models.BaseChatModel` que intercepta `_generate`/`_agenerate`, sanitiza as mensagens **antes** de enviar ao provider (Claude/Gemini/OpenAI/DeepSeek), e armazena um `PlaceholderMap` para rehydration seletiva pós-resposta.
- **Fluxo:**
  ```python
  class PIISafeChatModel(BaseChatModel):
      inner: BaseChatModel
      enabled: bool = True
      _last_placeholder_map: Optional[PlaceholderMap] = PrivateAttr(default=None)

      def _generate(self, messages, stop=None, **kwargs):
          if self.enabled:
              sanitized, pm = sanitize_messages(messages)
              self._last_placeholder_map = pm
          else:
              sanitized = list(messages)
          return self.inner._generate(sanitized, stop=stop, **kwargs)
  ```
- **Destino no lia:** novo arquivo `app/shared/llm/pii_safe_chat_model.py`. Plugar no `app/shared/llm_bootstrap.py` — toda LLM que o sistema cria passa pelo wrapper quando `SUPREMACY_PII_PRE_LLM_INTERCEPT=True`.
- **Atenção:** Sonnet 4.5 (provider Anthropic) usa `ChatAnthropic` — o wrapper é transparente (só precisa do `inner`).

#### B.3 `PlaceholderMap` (rehydration)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/pii_rehydrate.py`
- **Estrutura:**
  ```python
  @dataclass
  class PlaceholderMap:
      _counter: Dict[str, int]      # base_token → count (para sufixos)
      _forward: Dict[str, str]      # original → token
      _reverse: Dict[str, str]      # token → original

      def register(self, original: str, base_token: str) -> str: ...
      def restore(self, text: str) -> str:
          # substitui tokens por originais, ordenando por len desc para não
          # comer substrings de tokens maiores
  ```
- **Destino no lia:** `app/shared/llm/pii_rehydrate.py`.

---

### C. LGPD — Purpose Binding, Consent, DSR, Retenção

#### C.1 `LgpdPurpose` enum

- **Origem:** `recruiter_agent_v5/src/shared/compliance/purposes.py`
- **Valores:**
  ```python
  class LgpdPurpose(str, Enum):
      RECRUITMENT_MATCHING = "recruitment_matching"   # art. 7 I (consentimento)
      HIRING_DECISION      = "hiring_decision"        # art. 7 I
      COMMUNICATION        = "communication"          # art. 7 I
      ANALYTICS            = "analytics"              # anonimizado
      COMPLIANCE_AUDIT     = "compliance_audit"       # art. 16 II (obrigação legal — sempre permitido)
  ```
- **Destino no lia:** `app/shared/compliance/purposes.py`. Anexar `purpose: LgpdPurpose` como campo obrigatório em toda `DomainAction`/tool definition.

#### C.2 `enforce_consent_for_purpose`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/purpose_enforcement.py`
- **Regra de negócio:**
  ```python
  def enforce_consent_for_purpose(*, candidate_id, company_id, purpose: LgpdPurpose):
      if purpose == LgpdPurpose.COMPLIANCE_AUDIT: return          # sempre OK
      if not flags.lgpd_purpose_binding: return                   # legacy mode
      if not candidate_id or not company_id: return               # não aplicável
      consent_purpose = map_purpose_to_consent(purpose)
      if consent_purpose not in BLOCKING_PURPOSES: return
      summary = GranularConsentService.get_summary(candidate_id, company_id)
      if summary.has_consent(consent_purpose): return
      raise LgpdConsentDenied(...)
  ```
- **`BLOCKING_PURPOSES`** = `{AI_SCREENING, AI_SCORING, AI_VIDEO_ANALYSIS, AI_COMPARISON}`.
- **Destino no lia:** `app/shared/compliance/purpose_enforcement.py`. Chamar **dentro** do tool wrapper, antes da execução real.

#### C.3 `GranularConsentService`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/lgpd/consent.py`
- **Modelo:**
  ```python
  ConsentPurpose = {AI_SCREENING, AI_SCORING, AI_VIDEO_ANALYSIS, AI_COMPARISON,
                    DATA_RETENTION, MARKETING, ANALYTICS}

  @dataclass
  class ConsentRecord:
      consent_id: UUID
      candidate_id: str
      company_id: str
      purpose: ConsentPurpose
      action: Literal["GRANTED","REVOKED"]
      granted_at: datetime
      ip_address: str
      user_agent: str
      legal_basis: str       # "art_7_I", "art_7_II", etc.
      version: str           # versão do termo

  class GranularConsentService:
      def grant(candidate_id, company_id, purpose, ip, user_agent) -> ConsentRecord
      def revoke(...) -> ConsentRecord
      def get_summary(candidate_id, company_id) -> ConsentSummary   # has_consent, missing_blocking
  ```
- **Destino no lia:** novo módulo `app/shared/compliance/lgpd/consent.py` + migração Alembic para tabela `lgpd_consents`.
- **Integração:** endpoints FastAPI em `app/api/v1/lgpd/consents/` (grant / revoke / summary) com autenticação via JWT do ats_api.

#### C.4 DSR — Erasure Orchestrator (art. 17 LGPD)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/lgpd/erasure.py`
- **Fluxo:**
  1. Revoga todos consents → `GranularConsentService.revoke(...)` por purpose.
  2. Marca candidate como `erasure_requested=true` em DB.
  3. Enfileira pipeline async (Celery/Arq): apaga CV em storage, anonimiza evaluations, purga audit logs fora do período de retenção legal, apaga feedback.
  4. Emite linha especial em `AuditTrail` com `event_type=DSR_ERASURE`.
- **Destino no lia:** `app/shared/compliance/lgpd/erasure.py` + worker Celery em `app/jobs/lgpd_erasure.py`. A tabela `audit_decisions` (ver D.1) guarda a prova da execução.

#### C.5 `emit_purpose_audit` (art. 37 LGPD)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/audit_purpose.py`
- **Função:** log estruturado SIEM-friendly em toda execução de tool com purpose:
  ```python
  def emit_purpose_audit(domain_id, action_id, purpose, company_id, user_id):
      logger.info("[PURPOSE_AUDIT]", extra={
          "domain_id": domain_id, "action_id": action_id,
          "purpose": purpose.value, "company_id": company_id,
          "user_id": user_id, "ts": datetime.now(UTC).isoformat()
      })
  ```
- **Destino no lia:** `app/shared/observability/purpose_audit.py` (ADR-017 — observabilidade centralizada).

---

### D. Audit Chain Tamper-Evident (SHA-256 hash chain)

#### D.1 `AuditTrail` (append-only + hash chain)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/audit/trail.py` + migration `002_compliance_audit_chain.sql`.
- **Estrutura de evento:**
  ```python
  @dataclass
  class AuditEvent:
      event_type: AuditEventType    # PIPELINE_START, DOMAIN_ACTION, PII_MASKED,
                                    # FAIRNESS_CHECKED, PIPELINE_COMMIT, LLM_CALL_*, TOOL_CALL_*, ...
      tenant_id: str
      trace_id: str
      timestamp: str
      payload: dict
      prev_hash: str        # SHA-256 do evento anterior desse tenant
      line_hash: str        # SHA-256(prev_hash || canonical_json(payload))
  ```
- **Singleton `AuditTrail`:** mantém chain heads por tenant em memória + persiste em `logs/audit/{YYYY-MM-DD}.jsonl` + sincroniza para PostgreSQL (tabela `audit_decisions` particionada por mês).
- **Enforcement append-only:** trigger `audit_decisions_no_mutate()` bloqueia UPDATE/DELETE.
- **Migration (a recriar como Alembic no lia):**
  ```sql
  CREATE TABLE audit_decisions (
      id BIGSERIAL,
      decision_id UUID DEFAULT gen_random_uuid(),
      tenant_id VARCHAR(128) NOT NULL,
      trace_id VARCHAR(128) NOT NULL,
      domain_id VARCHAR(64) NOT NULL,
      action_id VARCHAR(128) NOT NULL,
      timestamp TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      payload JSONB NOT NULL,
      prev_hash CHAR(64),
      line_hash CHAR(64) NOT NULL,
      cost_usd NUMERIC(10, 6),
      tokens_used INT,
      PRIMARY KEY (id, timestamp)
  ) PARTITION BY RANGE (timestamp);

  CREATE TRIGGER audit_decisions_no_update
      BEFORE UPDATE ON audit_decisions
      FOR EACH ROW EXECUTE FUNCTION audit_decisions_no_mutate();
  ```
- **Destino no lia:**
  - Código: `app/shared/observability/audit_trail.py` (respeitar ADR-017).
  - Migration: `lia-agent-system/alembic/versions/xxxx_audit_chain.py`.
  - Script de verificação: portar `scripts/verify_audit_chain.py` para `lia-agent-system/scripts/verify_audit_chain.py`.

#### D.2 `AuditCallbackHandler` (LangChain)

- **Origem:** `recruiter_agent_v5/src/services/audit/audit_callback.py`
- **Intercepta:** `on_chain_start/end/error`, `on_llm_start/end`, `on_tool_start/end`. Emite `AuditEvent` em cada hook, com `duration_ms`, tokens, cost.
- **Destino no lia:** `app/shared/observability/callbacks/audit_callback.py`. Plugar no runner do LangGraph (`app/orchestrator/*`) via `callbacks=[AuditCallbackHandler(session_id=..., domain_id=...)]`.

#### D.3 `AuditAnonymizer`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/audit_anonymizer.py`
- Antes do sync do JSONL para GCS, remove PII dos payloads (pseudo-anon com salt). Satisfaz LGPD art. 6º V.
- **Destino no lia:** `app/shared/observability/audit_anonymizer.py` + job Celery em `app/jobs/audit_gcs_sync.py`.

---

### E. Multi-Tenant Isolation

#### E.1 Tenant ContextVar + `strict_tenant_safe` (ADR-010)

- **Origem:** `recruiter_agent_v5/src/shared/tenant.py`
- **Lógica crítica:**
  ```python
  _current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)

  def strict_tenant_safe(fn):
      @wraps(fn)
      def wrapper(*args, **kwargs):
          tenant_id = _current_tenant_id.get()
          if not tenant_id:
              raise TenantContextMissing("Tenant context missing (ADR 0010)")
          company_id = kwargs.get("company_id")
          if company_id and company_id != tenant_id:
              logger.warning("[TENANT] payload mismatch | context=%s payload=%s | overriding", tenant_id, company_id)
              kwargs["company_id"] = tenant_id    # anti-IDOR via prompt injection
          return fn(*args, **kwargs)
      return wrapper
  ```
- **Por que é crítico:** um atacante que consiga injetar `company_id=99` num prompt **não** consegue desviar para outro tenant — o decorator força override para o `tenant_id` da contextvar (que vem do JWT verificado no middleware).
- **Destino no lia:** `app/shared/tenant_guard.py` já tem parte. Enriquecer com `strict_tenant_safe` + `TenantContextMissing` + auto-wrap em `DomainRegistry` quando `SUPREMACY_TENANT_STRICT_MODE=True`.
- **Middleware FastAPI:** em `app/middleware/tenant_context.py` — ler `tenant_id` do JWT (após `auth_enforcement.py`), setar na contextvar via `set_tenant_context(tenant_id)`; token rebased no `finally` da request.

#### E.2 PostgreSQL Row-Level Security

- **Origem:** `recruiter_agent_v5/src/services/tenant_rls.py` + migration.
- **Setup:**
  ```sql
  CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS INTEGER AS $$
  BEGIN
      RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::INTEGER;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
  $$ LANGUAGE plpgsql STABLE;

  ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;
  ALTER TABLE agent_executions FORCE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation_agent_executions ON agent_executions
      USING (tenant_id = current_tenant_id());
  CREATE POLICY tenant_insert_agent_executions ON agent_executions
      FOR INSERT WITH CHECK (tenant_id = current_tenant_id());
  ```
- **Tabelas alvo no lia:** `agent_executions`, `conversation_history`, `pending_actions`, `hitl_pending_actions`, `hitl_audit_trail`, `tenant_memories`, `semantic_cache`, `query_metrics`, **audit_decisions**, **lgpd_consents**.
- **Python helper:**
  ```python
  def set_tenant_for_connection(conn, tenant_id: int) -> None:
      with conn.cursor() as cur:
          cur.execute("SET app.current_tenant_id = %s", (str(tenant_id),))
  ```
- **Destino no lia:**
  - Código: `app/shared/database/rls.py`.
  - Migration Alembic: `alembic/versions/xxxx_rls_tenant_isolation.py`.
  - Dependência FastAPI que injeta connection e chama `set_tenant_for_connection(conn, tenant_id)` ao entrar.
  - **Importante:** app user **não** deve ter `BYPASSRLS`. Migrations rodam com superuser separado.

---

### F. Tool Scope Enforcement / RBAC (ADR-011)

#### F.1 `ToolScope` + `@requires_scope`

- **Origem:** `recruiter_agent_v5/src/shared/security/tool_scopes.py`
- **Modelo:**
  ```python
  class ToolScope(str, Enum):
      READ      = "read"         # consultas
      WRITE     = "write"        # mutations seguras
      ADMIN     = "admin"        # config, gestão
      DANGEROUS = "dangerous"    # delete, bulk ops, export de dados

  _current_user_scopes: ContextVar[FrozenSet[ToolScope]] = ContextVar(
      "current_user_scopes", default=frozenset()
  )

  def requires_scope(scope: ToolScope):
      def decorator(fn):
          @wraps(fn)
          def wrapper(*args, **kwargs):
              if scope not in get_user_scopes():
                  raise ToolScopeViolation(...)
              return fn(*args, **kwargs)
          wrapper.__required_scope__ = scope
          return wrapper
      return decorator
  ```
- **Default seguro:** contextvar vazio ⇒ apenas `READ`.
- **Destino no lia:** `app/shared/security/tool_scopes.py`.
- **Integração com LangGraph:** no `@tool` wrapper do LangChain, antes da chamada real, valida scope. **Dupla defesa:** também filtra o tool registry antes de apresentar as tools ao LLM (F.2) — o modelo nem vê ferramentas fora do scope.

#### F.2 Action scope filter

- **Origem:** `recruiter_agent_v5/src/domains/registry.py`
- **Lógica:**
  ```python
  def get_allowed_actions_for_current_user(self) -> List[DomainAction]:
      current = get_user_scopes() or frozenset([ToolScope.READ])
      return filter_by_scope(self.get_actions(), current)
  ```
- **Destino no lia:** integrar em `app/shared/tools/` — o tool registry passa a receber o `current_scopes` no momento de montar a lista para o LLM.
- **Razão de segurança:** reduz superfície de ataque via prompt injection. Se o agent não vê `delete_candidate`, ele não tenta invocar.

---

### G. Fairness / Bias Audit / Drift Detection

#### G.1 `FairnessGuard` (3 layers)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/fairness_guard.py`
- **Layers:**
  1. **Explicit (regex):** termos discriminatórios diretos em PT-BR/EN (gender, race, age, religion, sexual orientation, marital status, disability, maternity, nationality). Cada padrão tem **referência legal anexada** (Lei 9.029/95, Lei 7.716/89, CF/88 art. 5º, LBI art. 34, LGPD).
  2. **Implicit (proxies):** "perfil jovem" → age proxy, "bairro nobre" → class/race proxy, "escola particular" → class proxy, "boa aparência" → appearance bias.
  3. **Semantic (LLM):** fallback para casos ambíguos (não usado em path crítico).
- **API:**
  ```python
  FairnessResult = FairnessGuard.check(text, action_id=?, context=?)
  FairnessResult = FairnessGuard.check_filters(where_clause)   # ex: {"gender": "female"} → BLOCK
  # Retorna: allowed, layer, action (BLOCK|WARN|ALLOW), category, matched_term, legal_reference
  ```
- **Destino no lia:** `app/shared/compliance/fairness_guard.py`. Três chamadas **obrigatórias**:
  - Input: depois do `PromptInjectionGuard`, antes do planner.
  - Filter: em toda query que o agente monta para `ats_api` (tool executor valida `params.where` / `params.filter`).
  - Output: em `OutboundGuard` (I.1), antes de mandar a resposta.

#### G.2 `fairness_probes.py` — Isomorphic Pairs

- **Origem:** `recruiter_agent_v5/src/evals/fairness_probes.py`
- **Técnica:** par de queries idênticas variando **apenas o nome do candidato** (João Silva masc majority vs. Maria Silva fem majority; João Silva vs. João Nakamura ethnicity-minority). Se `|score_a − score_b|` médio > threshold ⇒ viés detectado.
  ```python
  def fairness_divergence(score_pairs: Iterable[Tuple[float, float]]) -> float:
      pairs = list(score_pairs)
      return sum(abs(a - b) for a, b in pairs) / len(pairs) if pairs else 0.0
  ```
- **Thresholds:** gender divergence < 0.10, ethnicity divergence < 0.15.
- **Destino no lia:** `lia-agent-system/tests-eval/fairness/probes.py` + workflow CI `.github/workflows/fairness-gate.yml` (pre-merge gate).

#### G.3 `BiasAuditService` — 4/5 Rule + χ²

- **Origem:** `recruiter_agent_v5/src/shared/compliance/bias_audit.py`
- **Técnica:**
  - **4/5 rule (EEOC):** approval rate do grupo com menor taxa ≥ 80% do grupo com maior taxa.
  - **Chi-squared (α=0.05):** significância estatística da diferença.
  - **Min group size = 5** (evitar noise).
  - Retorna `BiasAuditSnapshot(dimensions: List[DemographicAuditResult], overall_compliant)`.
- **Destino no lia:** `app/shared/compliance/bias_audit.py` + job Celery `app/jobs/bias_audit.py` (diário, por empresa/job).
- **Output:** quando `overall_compliant=False`, abre HITL pending action pedindo revisão humana do ranking.

#### G.4 Model Drift (já parcial no lia)

- **Origem:** `recruiter_agent_v5/src/services/model_drift.py` + `lia-agent-system/app/services/golden_drift_monitor.py`
- **Técnica:** compara últimos 7d vs 7d anteriores em: score distribution, approval rate, cost p95, latency p95. Thresholds: score Δ > 0.5, approval Δ > 10pp, cost Δ > 20%, latency Δ > 50%.
- **Destino no lia:** unificar em `app/shared/observability/drift/` (ADR-017), `golden_drift_monitor.py` como ponto de entrada.

---

### H. HITL — Human-in-the-Loop Gate

#### H.1 `HITLService`

- **Origem:** `recruiter_agent_v5/src/services/hitl.py`
- **Modelo:**
  ```python
  @dataclass
  class HITLPendingAction:
      thread_id: str
      gate_type: HITLGateType  # BULK_ACTION, CANDIDATE_REJECTION, DATA_EXPORT, SCHEDULING_CREATE, ...
      action_name: str
      action_params: dict
      requested_by: str
      tenant_id: str
      status: HITLStatus       # PENDING, APPROVED, REJECTED, EXPIRED, AUTO_APPROVED
      fingerprint: str         # SHA-256(thread_id + gate_type + action_name + params) — dedupe
      context: dict            # candidate names etc. para UI

  @dataclass
  class HITLAuditTrail:
      pending_action_id: int
      decision: Literal["APPROVED","REJECTED"]
      decided_by: str
      reason: str
      decided_at: datetime
  ```
- **Tabelas:** `hitl_pending_actions`, `hitl_audit_trail` (migration Alembic).
- **Destino no lia:** `app/shared/compliance/hitl/service.py` + migrations + endpoints FastAPI em `app/api/v1/hitl/` (list pending, approve, reject).

#### H.2 `check_hitl_approval` (gate decorator)

- **Origem:** `recruiter_agent_v5/src/services/hitl_gate.py`
- **Mapa de ações críticas:**
  ```python
  HITL_GATE_ACTIONS = {
      "bulk_reject_applies": HITLGateType.BULK_ACTION,
      "bulk_approve_applies": HITLGateType.BULK_ACTION,
      "send_reject_feedback": HITLGateType.CANDIDATE_REJECTION,
      "export_job": HITLGateType.DATA_EXPORT,
      "erase_candidate_data": HITLGateType.DSR_ERASURE,
      # ...
  }
  ```
- **Uso no executor:**
  ```python
  pending = check_hitl_approval(thread_id=ctx.session_id, action_name=action_id, ...)
  if pending.status == HITLStatus.REJECTED: raise ActionRejectedByHITL(...)
  if pending.status == HITLStatus.PENDING:
      return DomainResponse(success=False, pending_action_id=pending.id,
                            message="Awaiting human approval")
  # APPROVED / AUTO_APPROVED → segue execução
  ```
- **Destino no lia:** `app/shared/compliance/hitl/gate.py`.
- **UX:** em `plataforma-lia`, quando a resposta do LIA contém `pending_action_id`, renderiza card com "Requer aprovação humana" + botões Approve/Reject.

---

### I. Guardrails de Saída

#### I.1 `OutboundGuard` (sanitize_outbound)

- **Origem:** `recruiter_agent_v5/src/shared/compliance/outbound_guard.py`
- **Fluxo:**
  ```python
  def sanitize_outbound(content, domain=None, apply_pii_mask=None, apply_fairness=None) -> OutboundGuardResult:
      # 1. FairnessGuard.check(content) → se blocked, substitui por FAIRNESS_BLOCK_MESSAGE
      # 2. PIIMasker.mask_for_llm(content) → remove PII residual
      # Retorna: content, blocked, block_reason, pii_stripped, fairness_flagged, warnings, metadata
  ```
- **Destino no lia:** `app/shared/compliance/outbound_guard.py`. Chamar em todo retorno do orchestrator antes de serializar o envelope de resposta para o frontend.

#### I.2 `AIDisclosure`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/ai_disclosure.py`
- **Papel:** adiciona disclosure legal automática ("Esta análise foi gerada por sistema de IA. Recomenda-se revisão humana.") em respostas de domínios sensíveis (hiring decisions).
- **Destino no lia:** `app/shared/compliance/ai_disclosure.py`. Plugar em `OutboundGuard` após sanitize.

#### I.3 `ResponseFilter` (tom PT-BR)

- **Origem:** `recruiter_agent_v5/src/services/response_filter.py`
- **Substitui:** `vc → você`, `tá → está`, `tô → estou`, remove `kkk`, `rsrs`.
- **Destino no lia:** `app/shared/compliance/response_filter.py`. Opt-in (flag).

---

### J. Observabilidade Defensiva

#### J.1 `LangSmithGuard`

- **Origem:** `recruiter_agent_v5/src/shared/compliance/langsmith_guard.py`
- **Papel:** wrapper do tracer LangSmith que remove PII/system prompts/contexto interno antes de enviar para cloud. Mantém full trace local.
- **Destino no lia:** `app/shared/observability/langsmith_guard.py` (ADR-017). Config em `app/config/langsmith_config.py`.

#### J.2 Callbacks HTTP assinados + SSRF guard

- **Origem:** `recruiter_agent_v5/src/utils/callbacks.py` + `src/services/security.py`
- **Fluxo do `send_to_rails_callback`:**
  1. `validate_callback_url(url)` — bloqueia schemes ≠ http(s), IPs privados (RFC1918, loopback, link-local, IPv6 uniques), DNS rebinding guard (resolve e valida o IP final).
  2. `sanitize_outbound(content, domain)` — aplica I.1.
  3. `ensure_outbound_disclosure(content, metadata)` — aplica I.2.
  4. HMAC-SHA256 sign do body com `X-Agent-Signature-Timestamp` + `X-Agent-Signature: sha256=…`.
  5. POST com `Authorization: Bearer {token}` + retry exponencial + timeout.
- **Destino no lia:** `app/shared/observability/callbacks/rails_callback.py` (observability ADR-017) + helpers em `app/shared/security/url_validation.py`.

---

### K. Resilience

#### K.1 `CircuitBreaker` + `TokenBudget` + `DomainKillSwitch`

- **Origem:** `recruiter_agent_v5/src/services/circuit_breaker.py`
- **Partes:**
  - **`TokenBudget`**: `max_tokens`, `max_cost_usd`, `warn_threshold`. `check(requested) → ALLOW|WARN|BLOCK`.
  - **`DomainKillSwitch`**: per-domain on/off em Redis (`disable("jobs")` ⇒ agente não invoca mais nada de jobs).
  - **`CircuitBreaker`**: per-service (ex: "gemini", "anthropic"). 3 falhas em 60s ⇒ open. Cooldown 30s ⇒ half-open. Success em half-open ⇒ close.
- **Destino no lia:** `app/shared/resilience/circuit_breaker.py` (existe parcial — enriquecer). Integrar em `app/shared/llm_bootstrap.py` e no API executor.

#### K.2 `CostLadder` (LLM provider fallback)

- **Origem:** `recruiter_agent_v5/src/services/cost_ladder.py`
- **Modelo de rungs:** `[Claude Sonnet 4.5, Claude Haiku 4.5, Claude Opus 4.6 (cache-heavy), Gemini 2.5 Flash]` — escolhe menor tier adequado à tarefa; desce quando circuit abre ou budget explode.
- **Destino no lia:** `app/shared/llm/cost_ladder.py`. Plugar em `llm_bootstrap.py`.

---

### L. CompositionalPromptBuilder — 8 Layers (ADR-016)

- **Origem:** `recruiter_agent_v5/src/shared/prompts/compositional.py`
- **Ordem das camadas (imutável):**
  1. `DomainGuardrailLayer` — "você é especialista em recrutamento".
  2. `PersonaLayer` — tom/estilo da persona.
  3. `DomainScopeLayer` — "responda APENAS sobre recrutamento".
  4. `TenantOverrideLayer` — overrides por empresa ("use termos do nosso glossário").
  5. `UserContextLayer` — preferências do usuário.
  6. `ConversationSummaryLayer` — memória comprimida.
  7. `ToolScopeLayer` — lista de tools (já filtrada por scope!).
  8. `ReActLayer` — instruções do ciclo ReAct.
  9. `AntiSycophancyLayer` — aplicado por último.
- **API fluente:**
  ```python
  prompt = (
      CompositionalPromptBuilder()
      .with_domain_guardrail(DomainGuardrailLayer(enabled=True))
      .with_persona(PersonaLayer(text=persona_yaml))
      .with_domain_scope(DomainScopeLayer(...))
      .with_tool_scope(ToolScopeLayer(available_tools=filtered_tools))
      .with_anti_sycophancy(AntiSycophancyLayer(level="high"))
      .build()
  )
  ```
- **Destino no lia:** `app/shared/prompts/compositional.py`. Flag `SUPREMACY_PROMPT_BUILDER_V2=True`. Manter `prompts.yaml` como fallback.

---

### M. Evals Contínuos + CI Gates

#### M.1 Golden Datasets + LiteEvalRunner

- **Origem:** `recruiter_agent_v5/src/evals/golden_datasets.py`, `lite_runner.py`
- **Dataset:** `EvalSample(domain, query, context, expected_output, category)`.
- **Proxies leves (sem LLM evaluator):**
  - `faithfulness_proxy(answer, context)` — token overlap (tipo BLEU).
  - `answer_relevancy_proxy(query, answer)` — cosine de embeddings ou BM25.
- **Thresholds default:** 0.3 / 0.3.
- **Destino no lia:** `lia-agent-system/tests-eval/lite/runner.py`. Rodar em CI toda PR (fail se regression > 10% ou golden dataset cai abaixo de threshold).

#### M.2 Fairness CI Gate

- **Workflow:** `.github/workflows/fairness-gate.yml`. Roda probes isomorphic, calcula divergence, fail se > threshold. Gate obrigatório antes do merge em `main`.

---

### N. Migrações SQL

| Origem v5 | Destino lia (Alembic) | O que cria |
|---|---|---|
| `scripts/migrations/002_compliance_audit_chain.sql` | `alembic/versions/xxxx_audit_chain.py` | `audit_decisions` (partitioned, append-only, hash chain), `audit_chain_head` |
| `scripts/migrations/003_compliance_guardrails.sql` | `alembic/versions/xxxx_guardrail_rules.py` | `guardrail_rules` (13 regras default), `guardrail_rules_audit` |
| (novo) | `alembic/versions/xxxx_rls_tenant_isolation.py` | RLS policies em 8 tabelas |
| (novo) | `alembic/versions/xxxx_lgpd_consents.py` | `lgpd_consents`, `lgpd_consent_versions` |
| (novo) | `alembic/versions/xxxx_hitl.py` | `hitl_pending_actions`, `hitl_audit_trail` |
| (novo) | `alembic/versions/xxxx_bias_audit_snapshots.py` | `bias_audit_snapshots` |

**13 guardrail rules default** (seed):
1. `block_explicit_rejection_by_age` — CLT Art. 3º-A
2. `block_explicit_rejection_by_gender` — Lei 9.029
3. `block_explicit_rejection_by_race` — CF Art. 5º
4. `block_rejection_by_religion` — Lei 9.029 Art. 1
5. `block_rejection_by_marital_status` — Lei 9.029
6. `block_rejection_by_maternity` — Lei 9.029 Art. 2
7. `block_rejection_by_disability` — LBI Art. 34
8. `block_system_prompt_leak` — Security
9. `block_credential_extraction` — Security (senha, API key)
10. `warn_salary_benchmark_exact` — Fairness (oferta subdimensionada)
11. `warn_generic_bias_terms` — Fairness proxies (idade/classe/raça indiretas)
12. `warn_pii_request_from_llm` — LGPD (pedir CPF/RG/endereço completo)
13. `block_bulk_reject_without_reason` — Process (ação em bulk requer justificativa)

---

### O. Feature Flags

#### O.1 `SupremacyFlags`

- **Origem:** `recruiter_agent_v5/src/config/supremacy_flags.py`
- **Destino no lia:** `app/config/supremacy_flags.py`.
- **Valores:**
  ```python
  @dataclass(frozen=True)
  class SupremacyFlags:
      pii_pre_llm_intercept: bool           # B.2
      tenant_strict_mode: bool              # E.1
      tool_scope_enforcement: bool          # F.1
      lgpd_purpose_binding: bool            # C.2
      semantic_cache_enabled: bool          # (ADR-013)
      response_cache_per_domain_ttl: bool   # (ADR-014)
      working_memory_enabled: bool          # (ADR-015)
      prompt_builder_v2: bool               # L
      lite_eval_enabled: bool               # M.1
      enhanced_agent_mixin: bool            # base class
  ```
- **Env var:** `SUPREMACY_<UPPER_SNAKE>=true|false`. Defaults: dev/staging=True, prod=False (canário por domínio).
- **Getter cacheado + reload para testes:**
  ```python
  def get_supremacy_flags() -> SupremacyFlags: ...
  def reload_supremacy_flags() -> SupremacyFlags: ...
  ```

#### O.2 `ComplianceFlags`

- **Origem:** `recruiter_agent_v5/src/config/compliance_config.py`
- **Destino no lia:** `app/config/compliance_config.py`.
- **Env:** `RUN_WITH_COMPLIANCE_ENABLED`, `RUN_WITH_COMPLIANCE_DOMAINS=applies,jobs,scheduling`.
- **Uso:** `run_with_compliance()` só aplica o pipeline pesado aos domínios listados (canário).

---

## 5. Diagrama de Integração — Fluxo End-to-End Desejado no `lia-agent-system`

```
┌──────────────────────────────────────────────────────────────────────┐
│ FastAPI request → app/middleware/auth_enforcement.py                 │
│   └─ valida JWT, extrai tenant_id, user_scopes, user_id              │
│      └─ set_tenant_context(tenant_id)      [E.1]                     │
│      └─ set_user_scopes(user_scopes)        [F.1]                    │
│      └─ set_tenant_for_connection(conn, tenant_id)  [E.2 RLS]        │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Input guard node (LangGraph)                                         │
│   ├─ PromptInjectionGuard.safe_process(user_text)  [A.1]            │
│   ├─ FairnessGuard.check(user_text)                [G.1]            │
│   ├─ PIIMasker.mask_for_llm(user_text)             [B.1]            │
│   └─ DomainScopeGuard.classify(user_text)          [A.2]            │
│      └─ se OUT_OF_SCOPE → curto-circuito                             │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Planner → LLM call                                                    │
│   ├─ CompositionalPromptBuilder (8 layers)         [L]              │
│   │   └─ ToolScopeLayer já filtrado por F.2                         │
│   ├─ PIISafeChatModel wraps provider (Claude 4.5)  [B.2]            │
│   │   └─ sanitize_messages + PlaceholderMap                         │
│   └─ Callbacks: AuditCallbackHandler               [D.2]            │
│       + LangSmithGuard                             [J.1]            │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tool execution (each tool wrapped)                                    │
│   ├─ @strict_tenant_safe                           [E.1]            │
│   ├─ @requires_scope(tool.scope)                   [F.1]            │
│   ├─ emit_purpose_audit(...)                       [C.5]            │
│   ├─ enforce_consent_for_purpose(...)              [C.2]            │
│   ├─ FairnessGuard.check_filters(params.where)     [G.1]            │
│   ├─ check_hitl_approval(...)                      [H.2]            │
│   │   └─ se PENDING, retorna envelope p/ frontend                   │
│   ├─ CircuitBreaker.call(provider)                 [K.1]            │
│   │   └─ CostLadder fallback                       [K.2]            │
│   └─ executor real (ats_api proxy / DB / vector)                    │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Output sanitization                                                   │
│   ├─ sanitize_outbound(content, domain)            [I.1]            │
│   │   ├─ FairnessGuard.check on output                              │
│   │   └─ PIIMasker.mask_for_llm on output                           │
│   ├─ ensure_outbound_disclosure(content, metadata) [I.2]            │
│   └─ filter_response_tone(content)                 [I.3] (opcional) │
└───────────────┬──────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Persist trace & respond                                               │
│   ├─ AuditTrail.append(PIPELINE_COMMIT, line_hash) [D.1]            │
│   ├─ Response envelope para frontend (plataforma-lia)                │
│   └─ Async job: AuditTrail → GCS (anonymized)      [D.3]            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Plano de Execução (sugerido, 6 fases)

### Fase 1 — Fundação (0–2 semanas)
- [ ] `SupremacyFlags` + `ComplianceFlags` (O)
- [ ] Enriquecer `tenant_guard.py` com `strict_tenant_safe` + `TenantContextMissing` (E.1)
- [ ] Middleware FastAPI de tenant context (usa JWT já validado)
- [ ] `ToolScope` enum + `@requires_scope` + contextvar (F.1)
- [ ] Migration Alembic: RLS em 8 tabelas (E.2)
- [ ] Testes: `test_strict_tenant_safe`, `test_tool_scopes`

### Fase 2 — Input Safety (2–4 semanas)
- [ ] Enriquecer `prompt_injection.py` com 23 padrões + NFKC (A.1)
- [ ] Criar `domain_scope_guard.py` (A.2)
- [ ] Enriquecer `pii_masking.py` com 4 layers + `PIIMaskingFilter` global (B.1)
- [ ] `PIISafeChatModel` wrapper + plug no `llm_bootstrap.py` (B.2)
- [ ] `PlaceholderMap` (B.3)
- [ ] Testes adversariais property-based (Hypothesis)

### Fase 3 — LGPD + Audit (4–7 semanas)
- [ ] `LgpdPurpose` enum + anexar a toda tool (C.1)
- [ ] `GranularConsentService` + migration + endpoints (C.3)
- [ ] `enforce_consent_for_purpose` (C.2)
- [ ] `emit_purpose_audit` em `app/shared/observability/` (C.5)
- [ ] `AuditTrail` hash-chained + migration (D.1)
- [ ] `AuditCallbackHandler` plug no orchestrator (D.2)
- [ ] DSR erasure orchestrator + worker Celery (C.4)
- [ ] Testes: `test_audit_chain` (property-based integrity), `test_lgpd_purposes`

### Fase 4 — Fairness + HITL (7–10 semanas)
- [ ] `FairnessGuard` 3 layers + base legal anexada (G.1)
- [ ] `fairness_probes.py` + CI gate (G.2, M.2)
- [ ] `BiasAuditService` 4/5 rule + χ² + job Celery (G.3)
- [ ] `HITLService` + migration + endpoints (H.1)
- [ ] `check_hitl_approval` gate (H.2)
- [ ] Integração frontend: card de "Requer aprovação humana"

### Fase 5 — Output & Resilience (10–12 semanas)
- [ ] `OutboundGuard` (I.1)
- [ ] `AIDisclosure` (I.2)
- [ ] `ResponseFilter` tom PT-BR (I.3)
- [ ] `LangSmithGuard` (J.1)
- [ ] Callback HMAC + SSRF guard (J.2)
- [ ] Enriquecer `CircuitBreaker` + `CostLadder` (K)

### Fase 6 — Prompts + Evals (12–14 semanas)
- [ ] `CompositionalPromptBuilder` 8 layers (L)
- [ ] `LiteEvalRunner` + golden datasets (M.1)
- [ ] `ModelDriftService` unificado em observability (G.4)
- [ ] Guardrail rules DB-driven (migration 003 equivalente)
- [ ] Dashboard de compliance (drift + bias audits + HITL queue)

---

## 7. Mapa de Arquivos — De/Para

```
recruiter_agent_v5/                                    →  lia-agent-system/
────────────────────────────────────────────────────────────────────────────────
src/shared/compliance/prompt_injection_guard.py        →  app/shared/prompt_injection.py (enrich)
src/services/domain_scope_guard.py                     →  app/shared/compliance/domain_scope_guard.py
src/shared/compliance/pii_masking.py                   →  app/shared/pii_masking.py (enrich)
src/shared/compliance/llm_sanitizer.py                 →  app/shared/llm/pii_safe_chat_model.py
src/shared/compliance/pii_rehydrate.py                 →  app/shared/llm/pii_rehydrate.py
src/shared/compliance/purposes.py                      →  app/shared/compliance/purposes.py
src/shared/compliance/purpose_enforcement.py           →  app/shared/compliance/purpose_enforcement.py
src/shared/compliance/lgpd/consent.py                  →  app/shared/compliance/lgpd/consent.py
src/shared/compliance/lgpd/erasure.py                  →  app/shared/compliance/lgpd/erasure.py
src/shared/compliance/audit_purpose.py                 →  app/shared/observability/purpose_audit.py
src/shared/compliance/audit/trail.py                   →  app/shared/observability/audit_trail.py
src/services/audit/audit_callback.py                   →  app/shared/observability/callbacks/audit_callback.py
src/shared/compliance/audit_anonymizer.py              →  app/shared/observability/audit_anonymizer.py
src/shared/tenant.py                                   →  app/shared/tenant_guard.py (enrich)
src/services/tenant_rls.py                             →  app/shared/database/rls.py
src/shared/security/tool_scopes.py                     →  app/shared/security/tool_scopes.py
src/domains/registry.py (filter_by_scope)              →  app/shared/tools/registry.py (patch)
src/shared/compliance/fairness_guard.py                →  app/shared/compliance/fairness_guard.py
src/evals/fairness_probes.py                           →  lia-agent-system/tests-eval/fairness/probes.py
src/shared/compliance/bias_audit.py                    →  app/shared/compliance/bias_audit.py
src/services/model_drift.py                            →  app/shared/observability/drift/model_drift.py
src/services/hitl.py                                   →  app/shared/compliance/hitl/service.py
src/services/hitl_gate.py                              →  app/shared/compliance/hitl/gate.py
src/shared/compliance/outbound_guard.py                →  app/shared/compliance/outbound_guard.py
src/shared/compliance/ai_disclosure.py                 →  app/shared/compliance/ai_disclosure.py
src/services/response_filter.py                        →  app/shared/compliance/response_filter.py
src/shared/compliance/langsmith_guard.py               →  app/shared/observability/langsmith_guard.py
src/utils/callbacks.py                                 →  app/shared/observability/callbacks/rails_callback.py
src/services/security.py (SSRF/URL validation)         →  app/shared/security/url_validation.py
src/services/circuit_breaker.py                        →  app/shared/resilience/circuit_breaker.py (enrich)
src/services/cost_ladder.py                            →  app/shared/llm/cost_ladder.py
src/shared/prompts/compositional.py                    →  app/shared/prompts/compositional.py
src/evals/golden_datasets.py                           →  lia-agent-system/tests-eval/lite/datasets.py
src/evals/lite_runner.py                               →  lia-agent-system/tests-eval/lite/runner.py
src/config/supremacy_flags.py                          →  app/config/supremacy_flags.py
src/config/compliance_config.py                        →  app/config/compliance_config.py
scripts/migrations/002_compliance_audit_chain.sql      →  alembic/versions/xxxx_audit_chain.py
scripts/migrations/003_compliance_guardrails.sql       →  alembic/versions/xxxx_guardrail_rules.py
scripts/verify_audit_chain.py                          →  scripts/verify_audit_chain.py
tests/supremacy/*                                       →  tests/compliance/*
tests/properties/*                                      →  tests/properties/*
```

---

## 8. Env Vars a Adicionar no `lia-agent-system`

```bash
# Feature flags (Supremacy)
SUPREMACY_PII_PRE_LLM_INTERCEPT=true
SUPREMACY_TENANT_STRICT_MODE=true
SUPREMACY_TOOL_SCOPE_ENFORCEMENT=true
SUPREMACY_LGPD_PURPOSE_BINDING=true
SUPREMACY_SEMANTIC_CACHE_ENABLED=true
SUPREMACY_RESPONSE_CACHE_PER_DOMAIN_TTL=true
SUPREMACY_WORKING_MEMORY_ENABLED=true
SUPREMACY_PROMPT_BUILDER_V2=true
SUPREMACY_LITE_EVAL_ENABLED=true
SUPREMACY_ENHANCED_AGENT_MIXIN=true

# Compliance routing (canário)
RUN_WITH_COMPLIANCE_ENABLED=true
RUN_WITH_COMPLIANCE_DOMAINS=applies,jobs,scheduling   # empty = all

# Outbound guards
OUTBOUND_PII_MASK_ENABLED=true
OUTBOUND_FAIRNESS_ENABLED=true

# PII Presidio (opcional)
PII_PRESIDIO_ENABLED=false

# Audit
AUDIT_LOG_DIR=/var/log/lia/audit
AUDIT_GCS_BUCKET=lia-audit-prod
AUDIT_GCS_SYNC_ENABLED=true

# LangSmith (atrás de guard)
LANGSMITH_ENABLED=false
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=lia-agent-system

# OTEL (ADR-017)
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=lia-agent-system
OTEL_TRACES_SAMPLER_ARG=1.0

# Callback signing
RAILS_CALLBACK_HMAC_SECRET=<secret>
```

---

## 9. Critérios de Aceite (por fase)

Cada fase **só pode ser declarada completa** quando:

1. Todos os componentes listados foram portados (ou criados) com os testes correspondentes passando.
2. CI/CD tem pelo menos **um gate** ativo para a fase (ex: fase 2 adiciona `prompt-injection-adversarial-test` como required check).
3. Flag da fase está ligada em **staging**, com telemetria de 7 dias sem regressão.
4. ADR escrito e referenciado em `lia-agent-system/docs/adr/` (mesmos números do v5 quando aplicável: 0009, 0010, 0011, 0012, 0016, 0017, 0018).

---

## 10. Riscos e Notas

- **Performance:** `PIIMasker.mask_for_llm` + `FairnessGuard` 3-layer + `PromptInjectionGuard` em toda entrada adiciona ~5–15ms. Aceitável; mas cachear regex compilados em módulo top-level é mandatório.
- **False positives de fairness:** Layer 2 (implicit) é o mais ruidoso. Começar com `action=WARN` em produção, só promover para `BLOCK` depois de baseline de 30 dias.
- **Hash chain em cluster:** o singleton `AuditTrail` assume single-process. Em multi-worker, delegar o encadeamento para o DB (`SELECT line_hash FROM audit_decisions WHERE tenant_id = $1 ORDER BY id DESC LIMIT 1 FOR UPDATE`) — ADR dedicada antes de prod.
- **RLS bypass:** migrations precisam rodar com superuser. O user de aplicação **não** pode ter `BYPASSRLS`. Verificar no `pg_roles` antes de cada deploy.
- **LGPD DSR prazo:** LGPD exige cumprimento em **15 dias**. A fila de erasure precisa SLA dashboard.
- **Consentimento pré-existente:** para candidatos já na base, migrar consentimento legado via script one-off (legal_basis=`pre_lgpd_grandfathered`) — sempre auditado.

---

## 11. Referências

**ADRs principais do `recruiter_agent_v5`:**
- ADR-0009: Pre-LLM PII Interceptor
- ADR-0010: Mandatory Tenant ContextVars
- ADR-0011: Tool Scope Runtime Enforcement
- ADR-0012: LGPD Purpose Binding
- ADR-0016: Compositional Prompt Builder
- ADR-0017: Lite Eval Runner
- ADR-0018: Enhanced Agent Mixin
- ADR-0023: Error Taxonomy

**ADR do `lia-agent-system` a respeitar:**
- ADR-017 (observabilidade canônica em `app/shared/observability/`) — **crítico**, o pre-commit G5 + CI quebram o build se violado.

**Documentos de apoio no monorepo:**
- `docs/GUIA_IMPLEMENTACAO_COMPLIANCE_INFRA.md`
- `docs/LIA_AGENT_AUDIT.md`
- `lia-agent-system/docs/CANONICAL_SOURCES_SPEC.md`
- `lia-agent-system/HARDENING_PLAN.md`

**Bases legais brasileiras cobertas:**
- LGPD — Lei 13.709/2018 (art. 6º, 7º, 16, 17, 37)
- Lei 9.029/1995 — práticas discriminatórias em relações de trabalho
- Lei 7.716/1989 — crimes de preconceito
- CF/88 art. 3º IV e art. 5º
- CLT art. 3º-A
- LBI — Lei 13.146/2015 (Estatuto da Pessoa com Deficiência) art. 34
- EEOC 4/5 Rule (referência internacional de disparate impact)

---

**Fim do documento.** Este plano é o ponto de partida — cada fase deve gerar sua própria ADR e seu próprio plano detalhado em `docs/superpowers/plans/` antes da execução.
