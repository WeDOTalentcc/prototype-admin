# Production Readiness Domains — LIA Platform

**Version:** 1.0  
**Date:** 2026-04-20  
**Task:** #691 — Padronizar domínios em evolução para production-ready  
**Status:** Living document — atualizar ao promover domínio entre estágios  
**CI Guard:** `python production_readiness_audit.py --strict` (raiz do repo)

---

## 1. Checklist Canônico de Production Readiness

Derivado das 14 dimensões do AUDIT_MODULES_GOVERNANCE_T163.md + 18 PR criteria do WeDO Talent Guide v3.3. Cada critério tem peso (1.0 = padrão, 2.0 = crítico).

| ID | Critério | Dimensão | Peso | Critério Objetivo |
|----|----------|----------|------|-------------------|
| **PR-01** | Tenant Isolation em Queries | D13 Security | 2.0 | `company_id` filtra 100% das queries; sem acesso cross-tenant possível |
| **PR-02** | Fail-Closed em Exceções | D13 Security | 2.0 | Exceções retornam `allowed: False`; nunca permitem por padrão |
| **PR-03** | PII Masking 3 Camadas | D12 AI Governance | 2.0 | `strip_pii_for_llm_prompt()` + `PIIMaskingFilter` + regex; verificável em `pii_masking.py` |
| **PR-04** | FairnessGuard Aplicado | D12 AI Governance | 1.5 | FairnessGuard L1/L2 em queries de busca; L3 feature-flagged |
| **PR-05** | Audit Trail Estruturado | D13 Security | 1.5 | `AuditService.log_decision()` em decisões críticas; retenção 730d |
| **PR-06** | Sem Ghost Actions | D4 Tool Orchestration | 2.0 | Tools retornam `is_mock=True` se não dispatcham; nunca retornam `success=True` sem ação real |
| **PR-07** | WebSocket Multi-Worker Safe | D2 Orquestração | 2.0 | `WSManager` usa Redis pub/sub; fallback documentado (sticky sessions) |
| **PR-08** | Tenant Isolation em Prompt LLM | D3 Intelligence Depth | 2.0 | `SystemPromptBuilder` injeta bloco `_TENANT_ISOLATION_BLOCK` com `company_id` |
| **PR-09** | Rate Limiting por User/Empresa | D14 Performance | 1.0 | Sliding window Redis ZSET; 600/min por user, 3000/min por empresa |
| **PR-10** | Circuit Breakers em Dependências | D6 Resiliência | 1.0 | `CircuitBreaker` em LLMs, email, ATS, voz; 18 circuitos gerenciados |
| **PR-11** | Health Check Endpoint | D6 Resiliência | 1.0 | `/health` reporta DB, Redis, LLMs, circuitos, Celery |
| **PR-12** | Logging Estruturado | D5 Cross-cutting | 1.0 | Logs incluem `company_id`, `agent_name`, `session_id` nos eventos críticos |
| **PR-13** | LGPD Consent Gate | D5 Cross-cutting | 1.5 | `ConsentCheckerService` verificado antes de processar dados de candidatos |
| **PR-14** | HITL em Decisões Estratégicas | D1 Agência | 1.5 | `interrupt_before` LangGraph em triagem/pipeline; override auditado |
| **PR-15** | Timeout por Tool e LLM | D6 Resiliência | 1.0 | `TimedToolNode` (15s/tool) + `LLM_TIMEOUT_SECONDS` (120s global) |
| **PR-16** | Sem SQL Injection (ORM) | D13 Security | 2.0 | 100% queries via SQLAlchemy ORM; zero f-string SQL |
| **PR-17** | Cobertura de Testes E2E/Eval | D15 Testes | 1.0 | Tests E2E ou eval suite cobrindo fluxo principal do domínio |
| **PR-18** | Documentação e ADR | D8 Documentação | 0.5 | Documento de domínio em `docs/` ou ADR em `docs/adr/` |

**Score mínimo para promoção a `production`:** 100% nos critérios de peso 2.0 + score total ≥ 80%.

---

## 2. Schema Unificado de Status de Módulos

Fonte da verdade: `lia-agent-system/libs/models/lia_models/billing.py → ModuleStatus`.  
Frontend espelha: `plataforma-lia/src/components/pages/modules-page.tsx → ModuleStatusType`.

| Status | Valor DB | Significado | Acessível ao Usuário | Gating |
|--------|----------|-------------|---------------------|--------|
| `experimental` | `experimental` | Protótipo interno; pode mudar sem aviso | Sim (como beta) | Liberado com badge |
| `beta` | `beta` | Disponível gratuitamente no período beta | Sim | Liberado com badge BETA |
| `trial` | `trial` | Período de avaliação pago ativo | Sim | Liberado com expiração |
| `active` | `active` | Módulo pago e ativo (production) | Sim | Liberado sem badge |
| `expired` | `expired` | Período expirado | Não | Bloqueado com CTA upgrade |
| `disabled` | `disabled` | Desativado pelo admin | Não | Bloqueado |
| `deprecated` | `deprecated` | Módulo descontinuado; migrar para substituto | Não | Bloqueado com aviso de migração |
| `coming_soon` | `coming_soon` | Em desenvolvimento; data não confirmada | Não | Bloqueado com card informativo |

### Regra de Transição

```
experimental → beta         (quando estabilizado, sem breaking changes)
beta         → trial        (quando pricing definido, módulo ativado via plano)
trial        → active       (após confirmação de pagamento)
active       → expired      (por vencimento automático via trial_enforcement.py)
*            → deprecated   (nunca para active diretamente; passa por disabled primeiro)
*            → coming_soon  (apenas ao criar módulo novo antes do desenvolvimento)
```

---

## 3. Score por Domínio (Auditoria 2026-04-20)

Execute `python production_readiness_audit.py --verbose --json` para dados atualizados.

### Domínios em Produção

| Domínio | PR Status | Score | Critical Pass | Observações |
|---------|-----------|-------|---------------|-------------|
| Core Sourcing & Search | `production` | 100% | ✅ | FairnessGuard aplicado no input; sourcing fora de `_FAIRNESS_DOMAINS` no C3b layer (gap aberto) |
| CV Screening + WSI | `production` | 100% | ✅ | Melhor fluxo de integração cross-cutting; HITL funcional |
| Pipeline & Kanban | `production` | 100% | ✅ | `AuditService` integrado em decisões de stage transition |
| Job Management + Wizard | `production` | 100% | ✅ | Wizard Graph com HITL e prompt score 27/33 (melhor do sistema) |
| Analytics & Reporting | `production` | 100% | ✅ | 5/5 eval AÇÃO EXECUTADA; domínio mais performático |

### Domínios em Beta

| Domínio | PR Status | Score | Gaps Críticos |
|---------|-----------|-------|---------------|
| Talent Intelligence Pro | `beta` | 100% | Nenhum crítico; `sourcing` fora de `_FAIRNESS_DOMAINS` no C3b (herdado) |
| Internal Mobility Suite | `beta` | 100% | Nenhum crítico |
| Interview Intelligence Pro | `beta` | 100% | Nenhum crítico; frontend ainda pendente (AUDIT_MODULES_GOVERNANCE_T163) |
| Candidate Nurture / CRM | `beta` | 100% | Nenhum crítico |
| Communication Tools | `beta` | 100% | PR-06 fechado (Task #693): `send_email`/`send_whatsapp`/`schedule_interview` agora chamam `CommunicationDispatcher` (Mailgun + Resend fallback / Twilio WhatsApp) e persistem `Interview` real via `SchedulingService`. |

### Domínios Experimentais / Coming Soon

| Domínio | PR Status | Gaps Mapeados |
|---------|-----------|---------------|
| Interview Scheduling | `experimental` | Rotas Rails ausentes (`GET /v1/users/scheduling/availability`, `POST /v1/users/calendar_events`); `schedule_interview` é mock (ADR-018) |
| Workforce Planning | `experimental` | Apenas estrutura básica; sem UI; sem testes end-to-end |
| Onboarding Intelligence | `experimental` | Tabelas criadas (migration 061); sem serviços de domínio |
| Predictive Attrition Analytics | `experimental` | Placeholder; sem modelos ML |

---

## 4. Gap Analysis Detalhado — 3 Gaps Críticos Fechados nesta Task

### Gap (a) — Ghost Actions em Communication Tools ✅ FECHADO

**Problema:** `send_email()`, `send_whatsapp()`, e `schedule_interview()` em `communication_tools.py` retornavam `success: True` sem chamar `CommunicationDispatcher` real. O agente acreditava que havia enviado email/WhatsApp quando não havia.

**Solução implementada:**
- Adicionado `is_mock=True` e `dispatch_status: "not_dispatched"` em todos os retornos
- Adicionado `mock_notice` com descrição clara para exibir na UI e nos logs de auditoria
- `send_invite` forçado para `False` em `schedule_interview` (era `True` no campo mas sem dispatch)
- Logger `.warning()` emitido em cada chamada com referência ao ADR-018

**Arquivo:** `lia-agent-system/app/domains/communication/tools/communication_tools.py`

**Próximo passo (fora do escopo desta task):** ADR-018 / Task #673 — conectar ao `CommunicationDispatcher` real com provider de email (Mailgun/Resend via circuit breaker existente).

---

### Gap (b) — WSManager Multi-Worker ✅ JÁ RESOLVIDO (gap C-01 do MATURITY_ASSESSMENT)

**Problema identificado no MATURITY_ASSESSMENT:** WSManager singleton em-processo não entregava mensagens para clientes em outros workers Uvicorn.

**Status:** Este gap já havia sido fechado antes desta task. `ws_manager.py` já implementa Redis pub/sub completo:
- Cada worker publica no canal `ws:session:{session_id}` via `redis.publish()`
- Subscriber loop em background escuta todos os canais subscritos
- Fallback para entrega local (single-worker) quando Redis indisponível

**Melhorias adicionadas nesta task:**
- Docstring atualizada com nota explícita de status multi-worker
- Requisito de sticky sessions documentado para modo degradado (sem Redis)

**Arquivo:** `lia-agent-system/app/shared/websocket/ws_manager.py`

---

### Gap (c) — Tenant Isolation em Prompts LLM ✅ FECHADO

**Problema:** Zero prompts mencionavam `company_id` como restrição obrigatória (MATURITY_ASSESSMENT, PROMPT_AUDIT Gap 1). A LLM podia raciocinar sobre dados cross-tenant sem instrução explícita de rejeição.

**Solução implementada:**
- Novo `_TENANT_ISOLATION_BLOCK_TEMPLATE` em `system_prompt_builder.py`
- Injetado **antes** da persona base quando `company_id` é fornecido
- Bloco lista 5 regras absolutas de isolamento, incluindo recusar dados de outro tenant
- Parâmetro `company_id: str = ""` adicionado ao `SystemPromptBuilder.build()`
- `main_orchestrator.py` atualizado para passar `company_id=_loop_company_id`

**Arquivo:** `lia-agent-system/app/shared/prompts/system_prompt_builder.py`

**Limitação:** Outros callers de `SystemPromptBuilder.build()` (e.g., em `lia_assistant/`, `interview_notes.py`) ainda não passam `company_id`. São 8 callers adicionais — cobrir como follow-up.

---

## 5. Schema Unificado — Mudanças de Código

### Backend — `billing.py` (ModuleStatus)

Adicionados:
- `EXPERIMENTAL = "experimental"` — protótipos internos antes do beta público
- `DEPRECATED = "deprecated"` — módulos descontinuados, aguardando migração de usuários

### Backend — `module_gating.py`

- `experimental` tratado como `beta` (allowed = True, badge exibido)
- `deprecated` tratado como `disabled` (allowed = False)

### Frontend — `modules-page.tsx` (ModuleStatusType)

Adicionados ao tipo TypeScript:
- `"experimental"` — exibido na seção Beta (badge Sparkles)
- `"deprecated"` — exibido na seção Others (badge Lock, muted)

---

## 6. Roadmap Priorizado

### Prioridade 1 — Crítico (< 2 semanas)

| # | Gap | Esforço | Dependência | Arquivo |
|---|-----|---------|-------------|---------|
| R1 | Conectar CommunicationDispatcher real (ADR-018) | 3 dias | Provider de email configurado | `communication_tools.py` |
| R2 | Passar `company_id` nos 8 callers restantes de `SystemPromptBuilder.build()` | 1 dia | Nenhuma | `lia_assistant/`, `interview_notes.py`, etc. |
| R3 | Adicionar `sourcing` em `_FAIRNESS_DOMAINS` no C3b layer | 1 dia | Testes de FairnessGuard L3 | `app/shared/compliance/c3b_layer.py` |
| R4 | Tornar ConsentChecker exception bloqueante (fail-closed) | 1 dia | Testes de consent | `consent_checker_service.py` |

### Prioridade 2 — Alto (2-6 semanas)

| # | Gap | Esforço | Dependência |
|---|-----|---------|-------------|
| R5 | Criar 4 rotas Rails ausentes para Interview Scheduling | 1-2 semanas | Time Rails |
| R6 | Conectar PersonalizationContext ao SystemPromptBuilder | 1-2 dias | Nenhuma (serviço existe) |
| R7 | Injetar `company_id` como critério em todos os 13 prompts de agentes | 1 semana | `agent_prompts.yaml` |
| R8 | Fechar loop RAGAS → ação automática (elevar modelo, criar alerta) | 3-4 semanas | Celery + RAGAS existentes |

### Prioridade 3 — Estrutural (> 6 semanas)

| # | Gap | Esforço |
|---|-----|---------|
| R9 | Habilitar `USE_SUPERVISOR = True` com testes HubPlanner/HubExecutor | 2-3 semanas |
| R10 | Unificar `CascadedRouter` e `CostLadderRouter` em arquitetura única | 4-6 semanas |
| R11 | Implementar feedback loop de tool para agente (delivery webhook) | 3-4 semanas |
| R12 | Eliminar duplicação de 7 agentes com prompts quase duplicados | 4-6 semanas |

---

## 7. Como Adicionar um Novo Domínio Production-Ready

```
1. DEFINA o domínio:
   - Crie pasta em `lia-agent-system/app/domains/<nome_dominio>/`
   - Adicione à `AVAILABLE_MODULES` em `billing.py` com `initial_status: "experimental"`
   - Adicione ao `DOMAIN_REGISTRY` em `production_readiness_audit.py`

2. IMPLEMENTE seguindo o checklist:
   - Todo repository: filtra por company_id (PR-01)
   - Exceções: fail-closed (PR-02)
   - LLM calls: via LLMService (PII masking automático) (PR-03)
   - Ações reais: sem is_mock=True no caminho feliz (PR-06)
   - Audit trail: `AuditService.log_decision()` em decisões críticas (PR-05)

3. VALIDE com o CI:
   python production_readiness_audit.py --domain <nome_dominio> --verbose

4. PROMOVA o status:
   - experimental → beta: quando testes passam e não há is_mock em ações críticas
   - beta → production: quando score 100% em PR critérios de peso 2.0
   - Atualizar status em `AVAILABLE_MODULES` e `DOMAIN_REGISTRY`

5. DOCUMENTE:
   - Adicione seção neste documento com score e gaps
   - Crie ADR em `docs/adr/` se arquitetura não-trivial
```

---

## 8. Execução do CI Guard

```bash
# Verificação rápida (apenas domínios production)
python production_readiness_audit.py --production-only

# Verificação completa com evidências
python production_readiness_audit.py --verbose

# Output JSON para integração com CI/CD
python production_readiness_audit.py --json > pr_audit.json

# Auditoria de domínio específico
python production_readiness_audit.py --domain communication --verbose

# Modo strict: falha se qualquer critério falhar em qualquer domínio
python production_readiness_audit.py --strict
```

**Integração GitHub Actions (exemplo):**
```yaml
- name: Production Readiness Audit
  run: python production_readiness_audit.py --production-only
```

O script retorna exit code `0` quando todos os domínios `production` passam, `1` quando algum falha, e `2` em erro de script.

---

*Última atualização: 2026-04-20 | Task #691 | Próxima revisão: antes de qualquer promoção experimental→beta ou beta→production*
