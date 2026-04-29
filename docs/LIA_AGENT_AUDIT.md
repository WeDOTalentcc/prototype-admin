# LIA — Agente de IA de Recrutamento · Capacidades, Segurança, Compliance e Fairness

> Auditoria dos sistemas de agentes de IA do monorepo WeDOTalent.
> Escopo: `lia-agent-system/` (FastAPI + LangGraph, Python 3.11) como orquestrador, `ats_api/` (Rails 7.1) como backend de dados, `plataforma-lia/` (Next.js 15) como frontend, e o sistema paralelo `recruiter_agent_v5/`.
> LLM primário: **Claude Sonnet 4.5** (com fallback multi-provider em `recruiter_agent_v5`).
> Data da auditoria: 2026-04-20.

Legenda:
- ✅ **Implementado e verificado no código**
- 🟡 **Parcial** — existe mas com gaps ou limitações
- ❌ **Gap / não identificado** — não existe ou não foi encontrado

---

## Sumário

- [1. O que a LIA faz (capacidades funcionais)](#1-o-que-a-lia-faz-capacidades-funcionais)
- [2. Segurança](#2-segurança)
- [3. Compliance — LGPD / GDPR](#3-compliance--lgpd--gdpr)
- [4. Fairness — proteção contra vieses](#4-fairness--proteção-contra-vieses)
- [5. Observabilidade e guardrails operacionais](#5-observabilidade-e-guardrails-operacionais)
- [6. Gaps conhecidos e recomendações](#6-gaps-conhecidos-e-recomendações)

---

## 1. O que a LIA faz (capacidades funcionais)

O sistema registra **16 domínios** (agentes ReAct ou micro-actions) via `@register_domain`. Cada domínio expõe um conjunto de tools ao LLM e participa do grafo de orquestração do LangGraph. Arquivos em `lia-agent-system/app/domains/<dominio>/`.

### 1.1 Agentes principais (ReAct, 12 domínios)

| Domínio | Quando é chamado | Principais tarefas |
|---|---|---|
| **cv_screening** | "triar currículos", "avaliar candidatos", "gerar WSI" | Análise de CVs, geração de score WSI (Weighted Skills Index), ranking, shortlist, feedback personalizado |
| **sourcing** | "buscar candidatos", "sourcing de tech" | Busca multi-canal (GitHub, StackOverflow, LinkedIn, referrals), pipeline passivo, diversity sourcing, enrichment |
| **pipeline** (`pipeline_transition`) | "mover para entrevista", "rejeitar candidato" | Movimentação entre estágios, predição de sub-status, sugestão de ações, interpretação de contexto |
| **job_management** | "criar vaga", "editar descrição" | CRUD de jobs, geração de JD, configuração de pipeline, ciclo de vida da vaga |
| **hiring_policy** | "configurar política", "validar compliance" | Policy advisory, fairness guardrails, validação de compliance, níveis de automação |
| **communication** | "enviar email", "notificar candidato" | Orquestração de email, WhatsApp, Teams; feedback de candidato; sequências de outreach |
| **interview_scheduling** | "agendar entrevista" | Integração Google/Outlook, múltiplas rodadas, matching de disponibilidade |
| **analytics** | "qual é o funil?", "relatório" | Dashboards, KPIs, análise de funil, métricas do time |
| **ats_integration** | "sincronizar com Workday" | Sync com ATS externo, integrações, health |
| **automation** | "agendar lembrete", "criar nota" | Task scheduling, reminders, notas, workflow, background jobs |
| **recruiter_assistant** | fallback | Agente genérico para intents não classificados |
| **agent_studio** | "criar agente customizado" | Criação e gestão de agentes user-defined |

### 1.2 Micro-action domains (3 simplificados)

| Domínio | Arquivo | Responsabilidade |
|---|---|---|
| **digital_twin** | `app/domains/digital_twin/domain.py` | Criar e avaliar candidatos-digital-twin (IA twins leves) |
| **recruitment_campaign** | `app/domains/recruitment_campaign/domain.py` | Campanhas de recrutamento multi-estágio |
| **talent_pool** | `app/domains/talent_pool/domain.py` | Ciclo de vida de talent pools |

### 1.3 Exemplos de tools expostas ao LLM

**Sourcing** (`lia-agent-system/app/domains/sourcing/`):
- `search_candidates`, `global_search`, `boolean_search`, `candidate_match`, `compare_candidates`, `search_analytics`, `diversity_sourcing`, `github_sourcing`, `stackoverflow_sourcing`, `referral_sourcing`, `passive_pipeline_sourcing`.

**CV Screening** (`lia-agent-system/app/domains/cv_screening/`):
- `auto_screen` (avaliação WSI automática, 0-100)
- `evaluate_wsi` (Work Sample Interview)
- `calculate_wsi_score` (cálculo com fairness guards)
- `quick_screening` (fast-track para seniores)
- `create_custom_rubric` (rubrica custom)
- `generate_feedback` (feedback personalizado com fairness check)

Todas as tools passam por:
1. **Isolamento de tenant** — validação de `company_id`
2. **Audit logging** — `AuditService.log_decision`
3. **Fairness guard** — `FairnessGuard.check`
4. **Token tracking** — `TokenTrackingService`

### 1.4 Sistema paralelo: `recruiter_agent_v5`

Pasta `/home/victhor/ats_mercado/recruiter_agent_v5/` (codebase independente, integrado via Rails API).

- **10 domínios**: jobs, applies, scheduling, evaluation, autonomous, messaging, background_agent, custom_agent, sourced_profile_sourcing, insights.
- **254 autonomous tools** (`autonomous_tool_registry.py`).
- **Multi-provider LLM (BYOK por conta)**: Gemini, OpenAI, Anthropic, DeepSeek.
- **CostLadder de 13 camadas** para roteamento barato → caro: regex → LRU → embedding → keyword → semantic → LLM.
- **Worker RabbitMQ** + **Celery** para evaluation.
- **Interview AI** em voz: Twilio + Gemini streaming.

---

## 2. Segurança

### 2.1 Autenticação ✅

Arquivo canônico: `lia-agent-system/app/middleware/auth_enforcement.py`.

Fluxo de validação:
1. `Authorization: Bearer <token>`.
2. Decodificação via FastAPI JWT (`app.auth.security.decode_token`).
3. Fallback para Rails JWT (`app.auth.rails_jwt.validate_rails_token_from_env`) — permite compartilhamento de identidade entre Rails e FastAPI.
4. Payload extraído: `sub` (user_id/email), `company_id` (tenant), `role`.
5. Injeção em `request.state` e `ContextVar _current_company_id` para uso downstream.

**Dev mode**: `LIA_DEV_MODE=1` requer `LIA_DEV_API_KEY`. Se faltante → **fail-closed** (401). Synthetic user `dev-user` com `company_id = DEMO_COMPANY_UUID`.

**Validação de tenant cruzado**: se o header `X-Company-ID` diverge do `company_id` no JWT → 403 e log de tentativa de cross-tenant.

### 2.2 Multi-tenancy ✅

Mecanismo: Apartment (Rails) + ContextVar (FastAPI).

```python
# lia-agent-system/app/middleware/auth_enforcement.py
_current_company_id: ContextVar[str] = ContextVar("_current_company_id", default="")
```

- Toda query de `candidate`, `job`, `audit_log` é filtrada por `company_id`.
- Token tracking é **per-company** (limites independentes).

### 2.3 Rotas públicas controladas ✅

Definidas em `auth_enforcement.py`:

```python
PUBLIC_PREFIXES = (
    "/api/v1/teams/",            # Azure Bot (Microsoft Teams) — não remover
    "/api/v1/auth/invitation-info/",
    "/api/v1/wsi/async/",        # callbacks de workers WSI
    "/api/public/",              # marketplace/embed
    "/docs/", "/static/", "/_next/", "/ws/", "/teams-icons/",
)

PUBLIC_PATHS = {
    "/health",
    "/api/v1/auth/{login,dev-login,register,refresh,forgot-password,reset-password}",
    "/api/v1/data-request",      # LGPD — solicitação de dados
    "/api/v1/webhooks/{whatsapp,twilio-voice,mailgun}",
    "/api/v1/calendar/google/callback",
    "/api/v1/calendar/microsoft/callback",
}
```

CSRF para OAuth redirects é via HMAC-signed `state` parameter.

### 2.4 Gestão de secrets ✅

Secrets críticos em `.env` (nunca commitados):

| Secret | Uso |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API |
| `MICROSOFT_APP_ID` / `MICROSOFT_APP_PASSWORD` / `MICROSOFT_TENANT_ID` | Azure Bot Service (Teams) |
| `RAILS_SECRET_KEY` | Assinatura JWT compartilhada com `ats_api` |
| `LIA_DEV_API_KEY` / `LIA_DEV_MODE` | Autenticação em dev |

Nenhum secret hardcoded foi identificado. Produção usa Docker secrets.

### 2.5 Rate limiting / token budget ✅

Arquivo: `lia-agent-system/app/shared/observability/token_tracking_service.py`.

```python
DEFAULT_LIMITS = {
    "daily_tokens_per_user":    500_000,
    "daily_tokens_per_company": 5_000_000,
    "monthly_cost_per_company": 500.00,   # USD
    "hourly_tokens_per_user":   100_000,
    "requests_per_minute_per_user": 60,
}
```

Preços por modelo estão hardcoded (`TOKEN_PRICES`), com entradas para Claude 3/3.5, GPT-4o, GPT-4o-mini, Gemini 1.5 Pro/Flash.

### 2.6 Circuit breaker e timeouts ✅

`recruiter_agent_v5/src/services/circuit_breaker.py`:
- Threshold: 3 falhas consecutivas → abre circuito.
- Cooldown: 30 s.
- Por domínio (cada domínio tem seu próprio breaker).
- Fallback universal: autonomous agent.

Timeouts por node: 30-200 s (`recruiter_agent_v5/src/services/timed_node.py`).

### 2.7 Guarda contra prompt injection ✅

Defesa em 2 camadas:

1. **Middleware global** (`auth_enforcement.py`, linhas 171-219) — inspeciona o body JSON de todas as rotas de agente (`/chat`, `/jobs`, `/candidates`, `/wsi`, `/interview-notes`, etc.) antes de chegar ao agente.
2. **Serviço de segurança** (`app/shared/robustness/security_patterns.py`):

```python
result = _check_input_security(body_text)
if result.is_blocked:
    return JSONResponse(
        {"detail": _get_block_response(result, language="pt")},
        status_code=400,
    )
```

### 2.8 Validação de input ✅

Todos os endpoints validam via **Pydantic** (tipos estritos: UUID, email, enums). Validators custom em domínios específicos (ex.: rubrica de CV screening).

### 2.9 RBAC e políticas ✅

Arquivo: `lia-agent-system/app/domains/hiring_policy/agents/agent.py`.

Token payload carrega `role`. O **Policy Agent** define 5 blocos de política configuráveis por empresa:
- `pipeline_rules` — estágios e transições válidas.
- `scheduling_rules` — restrições de agendamento.
- `communication_rules` — canais permitidos, templates.
- `screening_rules` — critérios de triagem, fairness thresholds.
- `automation_rules` — nível de autonomia (manual, semi-automático, full).

**Thresholds de HITL por estágio**: sourcing 0.65, triagem 0.70, entrevista 0.80.

### 2.10 Auditoria e logging ✅

Arquivo: `lia-agent-system/app/shared/compliance/audit_service.py`.

Cada decisão de agente é persistida em `AuditLog`:

```python
class AuditLog:
    company_id: str
    agent_name: str              # "cv_screening", "sourcing", ...
    decision_type: DecisionType  # SCORE_CANDIDATE, MOVE_STAGE, REJECT, ...
    action: str                  # o que aconteceu
    decision: str                # approved | rejected | pending_review
    reasoning: list[str]         # justificativa textual
    criteria_used: list[str]     # critérios aplicados
    criteria_ignored: list[str]  # atributos protegidos explicitamente ignorados
    candidate_id: str | None
    score: float | None
    confidence: float | None
    human_review_required: bool
    retention_until: datetime    # janela de retenção LGPD
```

### 2.11 Gaps identificados em segurança ❌

- **Rate limiting HTTP (429)** — os limites de token/request existem em código mas não foi encontrado um middleware HTTP explícito de 429. Presume-se aplicado via ingress/proxy.
- **WAF** — não há código; aplicado em camada de infra.
- **Criptografia de audit logs em repouso** — sem evidência de AES-256 específica.
- **Validação SSRF** — tools que fazem requests a GitHub/StackOverflow/LinkedIn não têm validação de SSRF explícita.
- **Política de rotação de secrets** — não documentada; presumivelmente manual.
- **TLS pinning** — não aplicado (HTTPS padrão).

---

## 3. Compliance — LGPD / GDPR

### 3.1 Gestão de consentimento ✅

Arquivo: `lia-agent-system/app/domains/candidates/services/candidate_channel_selector.py`.

```python
CHANNEL_CONSENT_MAP = {
    "email":    "marketing_email",
    "whatsapp": "marketing_whatsapp",
    "sms":      "marketing_sms",
}

TRANSACTIONAL_CHANNELS = {"email"}  # processo seletivo em andamento — dispensa consent
```

Fluxo:
1. Agente decide canal (email / WhatsApp / SMS).
2. Consulta `LGPDConsent` por `candidate_id + company_id + consent_type`.
3. Marketing → exige `consent_given=True`. Transacional (processo seletivo) → permitido sem consent.
4. Se sem consent → canal é ignorado e evento registrado em auditoria.

### 3.2 Retenção de dados 🟡

Arquivo: `audit_service.py` (linhas 56-65).

```python
RETENTION_PERIODS = {
    "score_candidate":    730,   # 2 anos (decisões de triagem)
    "approve_candidate":  730,
    "reject_candidate":   730,
    "move_stage":         730,
    "send_message":       1825,  # ~5 anos (estatuto de limitações)
    "schedule_interview": 365,
    "generate_feedback":  730,
    "job_creation":       730,
}
```

**Gap**: não foi identificado **job automático de deleção** que consuma `retention_until`. Presume-se que é responsabilidade de um worker não rastreado ou que seria adicionado.

### 3.3 Direito ao esquecimento 🟡

Endpoint público: `/api/v1/data-request` (em `PUBLIC_PATHS`).

Modelo esperado:
1. `PATCH /api/v1/data-subject/{candidate_id}/delete-request`.
2. Sistema cria `DataSubjectRequest` (audit trail).
3. Pseudonimização de candidato (nome → hash), CV, feedback, notas, audit logs.
4. Hard delete após retenção.

**Gap**: apenas o endpoint público foi confirmado; a implementação completa de pseudonimização não foi totalmente verificada no código lido.

### 3.4 Trilha de auditoria e explicabilidade ✅

Exemplo de decisão logada (extraído de `audit_service.py`):

```python
await AuditService.log_decision(
    company_id="acme-corp",
    agent_name="cv_screening",
    decision_type="score_candidate",
    action="auto_screen",
    decision="approved",
    reasoning=["WSI score 75/100", "3+ anos de Java", "projetos GitHub"],
    criteria_used=["wsi_score", "years_experience", "github_activity"],
    criteria_ignored=["age", "gender", "birthplace"],  # anti-bias explícito
    candidate_id="cand-123",
    score=75.0,
    confidence=0.92,
    human_review_required=False,
)
```

### 3.5 Feedback personalizado ao candidato ✅

Arquivo: `lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`.

Quando um candidato é rejeitado ou avançado, o sistema gera:
- Motivos objetivos (ex.: "Faltam 2 anos de Python").
- Dicas de desenvolvimento.
- **Nunca inclui** atributos protegidos (raça, gênero, idade).

O feedback passa pelo `FairnessGuard` antes de sair. Se o texto menciona algo como "muito jovem", é bloqueado e regenerado:

```python
message, improvement_tips, fairness_meta = await self._enforce_fairness_on_message(text)
meta["fairness_blocked"] = False
```

### 3.6 Human-in-the-loop (HITL) ✅

Arquivo: `lia-agent-system/app/domains/cv_screening/services/hitl_service.py`.

Gates por estágio:
- Sourcing: `confidence < 0.65` → HITL.
- Screening: `< 0.70` → HITL.
- Interview: `< 0.80` → HITL.
- Communication: `human_review_required=True` → aprovação explícita.

Fluxo:
1. Agente toma decisão → calcula `confidence`.
2. Se abaixo do threshold: cria `ApprovalRequest` (pending), seta `hitl_pending=True`, loga com `human_review_required=True`.
3. Notifica usuário (Bell, Teams, email).
4. Usuário revisa pela UI → aprova ou rejeita.
5. `ApprovalRequest.reviewed_at` atualizado; decisão humana logada; workflow continua.

```python
class ApprovalRequest:
    id: UUID
    company_id: UUID
    decision_type: str           # "cv_screening", "pipeline", "communication"
    entity_id: UUID              # candidate_id / job_id
    requested_by: str            # agent_name
    human_reviewer_id: str | None
    decision: str                # approved | rejected | pending
    reasoning: str
    reviewed_at: datetime | None
    expires_at: datetime         # 7 dias padrão
```

### 3.7 Disclosure de IA ao candidato ❌

**Não foi encontrado disclaimer explícito** do tipo "você está conversando com uma IA" em chat, feedback ou templates de email.

O branding "LIA" aparece, e alguns textos mencionam "análise automática", mas não há disclosure formal e padronizado. **Gap relevante** para conformidade ética e algumas jurisdições.

### 3.8 GDPR 🟡

Foco atual é LGPD (Brasil). Princípios (consent, direito ao esquecimento, trilha de auditoria, retenção) são compatíveis com GDPR, mas **não há código específico** para requisitos europeus (representante na UE, base legal explícita para cada processamento, DPIA registrado). Gap a tratar se houver clientes na EU.

---

## 4. Fairness — proteção contra vieses

### 4.1 FairnessGuard — defesa em camadas ✅

Arquivo: `lia-agent-system/app/shared/compliance/fairness_guard.py` (400+ linhas).

| Camada | O que faz | Onde vive |
|---|---|---|
| Layer 1 — lexical | Termos discriminatórios explícitos | `fairness_guard.py` → `IMPLICIT_BIAS_TERMS` |
| Layer 2 — regex | Padrões discriminatórios (ex.: "apenas homens") | `fairness_guard.py` → `DISCRIMINATORY_CATEGORIES` |
| Layer 3 — semântica | Viés semântico via Claude | `c3b_layer.py` |
| FactChecker | Validação de afirmações extraídas | `fact_checker.py` |

### 4.2 Termos e padrões bloqueados (PT) ✅

Amostra de `IMPLICIT_BIAS_TERMS`:

```python
IMPLICIT_BIAS_TERMS = {
    "boa aparencia":                   "Lei 12.984/14 — discriminação estética",
    "bairros nobres":                  "Discriminação socioeconômica",
    "universidades de primeira linha": "Elitismo acadêmico",
    "energia jovem":                   "Lei 10.741/03 — discriminação etária",
    "sem obrigacoes":                  "Proxy para discriminação por estado civil",
    "disponibilidade total":           "Proxy para discriminação por responsabilidades familiares",
    # ... 200+ termos
}
```

Amostra de `DISCRIMINATORY_CATEGORIES`:

```python
"genero": {
    "terms": [
        r"\b(apenas|somente|só)\s+(\w+\s+)*(homens?|mulheres?)\b",
        r"\bexcluir?\s+(\w+\s+)*(homens?|mulheres?)\b",
    ],
    "message": "A LIA não pode filtrar candidatos por gênero (CLT Art. 5º, LGPD).",
}
```

### 4.3 Layer 3 (semântica) 🟡

Arquivo: `lia-agent-system/app/shared/compliance/c3b_layer.py`.

Per `app/domains/autonomous/__init__.py`:
> "Layer 3 (semantic bias) + FactChecker **are NOT applied at the autonomous level**."

Aplica-se apenas em:
- Decisões do Policy Agent.
- Geração de feedback para candidato.
- Regras de agendamento de entrevista.

**Gap**: agentes autônomos escapam da validação semântica. Recomenda-se ampliar.

### 4.4 Atributos protegidos ✅

Arquivo: `lia-agent-system/app/shared/compliance/protected_attributes.py`.
Config: `app/config/protected_attributes.yaml`.

```python
PROTECTED_ATTRIBUTES = {
    "age", "gender", "ethnicity", "marital_status", "photo",
    "institution", "address", "religion", "disability", "cv_gaps",
}

PROTECTED_DB_FIELDS = {
    "birthdate", "gender", "ethnicity", "marital_status", "photo_url",
    "education_institution", "home_address", "religious_affiliation", "disabilities",
}
```

Garantia operacional: toda `AuditLog` inclui `criteria_ignored` listando os atributos protegidos que **não foram usados** na decisão.

### 4.5 Dimensões de auditoria de viés ✅

```python
BIAS_AUDIT_DIMENSIONS = {
    "age":         "age_discrimination",
    "gender":      "gender_discrimination",
    "ethnicity":   "racial_discrimination",
    "religion":    "religious_discrimination",
    "disability":  "disability_discrimination",
}
```

### 4.6 Disparate impact (regra dos 4/5) 🟡

Arquivo: `lia-agent-system/app/shared/compliance/bias_audit_service.py`.

Analisa taxas de aprovação por grupo. Se `approval_rate[grupo_A] / approval_rate[grupo_B] < 0.80` → sinal de disparate impact.

**Gap**: foi encontrado o serviço, mas **não há evidência de execução periódica automatizada** com thresholds firmes. O dashboard `/fairness-report/*` existe no backend proxy mas a frequência e o canal de alerta não foram confirmados.

### 4.7 Monitoramento de drift de modelo ✅

Arquivo: `lia-agent-system/app/shared/observability/model_drift_service.py`.

4 triggers comparam janela recente (7 d) vs baseline (7 d anteriores):

| Trigger | Métrica | Threshold |
|---|---|---|
| `score_drift` | Score médio WSI | > 0.5 pontos |
| `approval_drift` | Taxa de aprovação | > 10 p.p. |
| `cost_drift` | Custo em tokens | > 20% variação |
| `latency_drift` | Latência P95 | > 50% variação |

Níveis de alerta:
- `>= 2` triggers → **critical** (notifica imediatamente via Bell + Teams).
- `1` trigger → **warning** (log).

### 4.8 Gaps em fairness ❌

- Layer 3 semântica não aplicada em agentes autônomos.
- Relatório de disparate impact não confirmado como rotina automatizada.
- Não há rastreamento de "**por que** o humano discordou do agente" em HITL (apenas a decisão, não o delta).
- Pipeline de retreinamento/calibração de modelos com benchmark de fairness não identificado (Claude é consumido como serviço, calibração é via prompt e rubrica).

---

## 5. Observabilidade e guardrails operacionais

### 5.1 Tracing — LangSmith ✅

Arquivo: `lia-agent-system/app/shared/observability/langsmith.py`.

```python
LANGSMITH_ENABLED = os.environ.get("LANGSMITH_ENABLED", "true").lower() == "true"
LANGSMITH_PROJECT = os.environ.get("LANGSMITH_PROJECT", "lia-recruitment")
```

Traçado: transições de estado no LangGraph (intent → action → response), calls ao LLM (tokens I/O, modelo, latência), tools (input/output/latência), exceções. Dashboard em https://smith.langchain.com/ sob o projeto `lia-recruitment`.

### 5.2 Token tracking e custo ✅

`TokenTrackingService` grava cada consumo:

```python
await record_token_usage(
    company_id, user_id, model,
    input_tokens, output_tokens, cost, agent_name,
)
```

Enforcement em runtime via `check_limit(company_id, user_id)`.

### 5.3 WSI observability ✅

Arquivo: `lia-agent-system/app/shared/observability/wsi_observability.py`.

Métricas:
- Latência da avaliação WSI (P50, P95, P99).
- Distribuição de scores (mean, stddev, percentis).
- Taxa de conclusão da entrevista (completou vs. abandonou).
- Dificuldade por pergunta (score médio).
- Engajamento (tempo de fala, pausas, confiança).

Alertas:

```python
WSI_ALERTS = {
    "low_completion_rate": 0.60,   # menos de 60% completam
    "high_avg_latency":    30.0,   # > 30 s por questão
    "high_rejection_rate": 0.80,   # > 80% rejeitados pós-WSI
    "score_mean_shift":    15.0,   # shift > 15 pts vs baseline
}
```

### 5.4 Saúde dos agentes ✅

Arquivo: `lia-agent-system/app/shared/observability/agent_health_alert_service.py`.

Janela de 30 dias. Alerta quando:
- `error_rate > 0.10` → critical.
- `latency_p95 > 60 s` → warning.
- `hitl_rate > 0.50` → warning (agente pouco confiável).

### 5.5 Versionamento de prompts ✅

- Prompts por domínio em `lia-agent-system/app/prompts/domain_<id>.yaml`.
- Loader: `PromptLoader.get_domain_prompt(domain_id)`.
- Histórico de versão = git history.
- Sem config dinâmica: mudanças só por deploy (rastreável).

### 5.6 ADR-017 — observabilidade canônica ✅

Conforme `lia-agent-system/docs/ARCHITECTURE.md` (ADR-017) e `docs/CANONICAL_SOURCES_SPEC.md` §1:

> Tracing, structured logging, LLM callbacks, agent monitoring, drift detection, token tracking/budget, WSI observability e LangSmith configuration vivem **exclusivamente** em `app/shared/observability/`.

Enforcement: `lia-agent-system/scripts/check_forbidden_imports.py` (pre-commit + CI `G5`) bloqueia imports dos 11 caminhos antigos descontinuados.

---

## 6. Gaps conhecidos e recomendações

### 6.1 Gaps em ordem de prioridade

| # | Gap | Severidade | Recomendação |
|---|---|---|---|
| 1 | AI disclosure explícito ao candidato | Alta (ética + algumas jurisdições) | Disclaimer padronizado em chat, feedback e emails |
| 2 | Job automático de deleção pós-retenção | Alta (LGPD) | Worker que consuma `retention_until` e pseudonimize/delete |
| 3 | Layer 3 semântica em agentes autônomos | Média | Ampliar `c3b_layer.py` para rodar também em `autonomous/` |
| 4 | Relatório periódico de disparate impact | Média | Scheduled job semanal com regra dos 4/5 + alerta |
| 5 | Delta humano↔agente em HITL | Média | Registrar motivo da divergência humana para calibração futura |
| 6 | Rate limiting HTTP visível (429) | Média | Middleware FastAPI formalizado, não só budget de token |
| 7 | Validação SSRF em tools externas | Média | Allowlist de hosts para GitHub/StackOverflow/LinkedIn |
| 8 | Criptografia em repouso de audit logs | Baixa/média | AES-256 em coluna sensível (motivos, reasoning) |
| 9 | Rotação de secrets documentada | Baixa | Política + vault (ex.: Doppler, AWS Secrets Manager) |
| 10 | DPIA + base legal GDPR | Condicional | Se houver clientes EU, formalizar |

### 6.2 Garantias verificadas (resumo executivo)

- ✅ Autenticação multi-tenant com fail-closed em dev.
- ✅ Isolamento de dados via Apartment + ContextVar `_current_company_id`.
- ✅ Guarda contra prompt injection em 2 níveis.
- ✅ FairnessGuard com 200+ termos bloqueados (PT) e regex para padrões discriminatórios.
- ✅ Atributos protegidos definidos e registrados como `criteria_ignored` em cada decisão.
- ✅ HITL gates com thresholds de confiança por estágio (0.65 / 0.70 / 0.80).
- ✅ Audit trail por decisão com reasoning, critérios usados, critérios ignorados e janela de retenção.
- ✅ Token budget per-user e per-company com preços por modelo.
- ✅ Drift monitoring com 4 triggers (score, aprovação, custo, latência).
- ✅ Tracing LangSmith end-to-end e WSI observability dedicada.
- ✅ Consent LGPD por canal (transacional vs. marketing).

### 6.3 Fontes verificadas

- `lia-agent-system/app/middleware/auth_enforcement.py`
- `lia-agent-system/app/shared/compliance/audit_service.py`
- `lia-agent-system/app/shared/compliance/fairness_guard.py`
- `lia-agent-system/app/shared/compliance/c3b_layer.py`
- `lia-agent-system/app/shared/compliance/protected_attributes.py`
- `lia-agent-system/app/shared/compliance/bias_audit_service.py`
- `lia-agent-system/app/shared/observability/token_tracking_service.py`
- `lia-agent-system/app/shared/observability/model_drift_service.py`
- `lia-agent-system/app/shared/observability/wsi_observability.py`
- `lia-agent-system/app/shared/observability/agent_health_alert_service.py`
- `lia-agent-system/app/shared/observability/langsmith.py`
- `lia-agent-system/app/domains/cv_screening/services/{personalized_feedback_service,hitl_service}.py`
- `lia-agent-system/app/domains/candidates/services/candidate_channel_selector.py`
- `lia-agent-system/app/domains/hiring_policy/agents/agent.py`
- `lia-agent-system/app/shared/robustness/security_patterns.py`
- `lia-agent-system/scripts/check_forbidden_imports.py`
- `lia-agent-system/docs/ARCHITECTURE.md` (ADR-017)
- `lia-agent-system/DOMAIN_CATALOG.md`
- `recruiter_agent_v5/src/services/circuit_breaker.py`
- `recruiter_agent_v5/src/services/timed_node.py`

---

**Última atualização**: 2026-04-20.
**Responsável**: auditoria automatizada baseada em leitura de código (não substitui review humano).
