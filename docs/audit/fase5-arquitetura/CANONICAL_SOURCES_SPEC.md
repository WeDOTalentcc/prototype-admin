# CANONICAL_SOURCES_SPEC.md — Fontes Canonicas (Single Source of Truth)
**Protocolo:** P22  
**Data:** 2026-04-14  
**Arquiteto:** Claude Opus 4.6  
**Baseado em:** P13 (DUPLICATION_DIVERGENCE_MAP), P14 (PROPORTIONALITY), P21 (TARGET_ARCHITECTURE)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. Integracao via RabbitMQ.

**Depende de:** P13, P14, P21  
**Alimenta:** P27, P35

---

## VISAO GERAL

**Metricas de duplicacao no codebase:**
- 962 referencias a FairnessGuard — 1 SSOT (`fairness_guard.py`) ja funciona como canonico
- 1688 referencias a system_prompt/persona — multiplos patterns, precisa consolidar
- 1109 referencias a audit/logging — 5+ classes diferentes
- 113 instantiacoes diretas de LLM — maioria ja via factory, ~15 bypasses
- 419 referencias a tool registries — 1 SSOT (`ToolRegistry`) + 12 registries de dominio
- 556 referencias a retry/circuit breaker — 1 SSOT (`CircuitBreaker`) + patterns locais
- 3475 referencias a error handling — sem padrao unificado

---

## CONCERN 1: FAIRNESS SERVICE

**Estado atual:** 1 implementacao principal. **JA E SSOT.**

**Fonte canonica:** `app/shared/compliance/fairness_guard.py`
- **Responsabilidade:** Pre/post check de bias em texto. Atributos protegidos. Educational messages. Metricas.
- **Interface:** `FairnessGuard().check(text) -> FairnessResult(is_blocked, soft_warnings, educational_message)`
- **Configuracao:** `IMPLICIT_BIAS_TERMS` dict inline + `PROTECTED_ATTRIBUTES` (hardcoded)
- **Enforcement:** Via `ComplianceDomainPrompt` (heranca obrigatoria, LIA-C01 blocking)
- **Consumidores confirmados:** MainOrchestrator, CustomAgentRuntime (Studio), ML salary prediction, interview_notes, RAG search, fairness_reports

**O que falta (nao e duplicacao — e gap):**
- Post-check em TODOS os agentes (hoje apenas Studio e interview_notes fazem)
- Atributos protegidos em YAML externo (hoje hardcoded no .py)

**Plano de consolidacao:**
1. Mover `IMPLICIT_BIAS_TERMS` e `PROTECTED_ATTRIBUTES` para `config/fairness.yaml` (configuravel por jurisdicao)
2. Adicionar post-check no `ComplianceDomainPrompt.execute_action()` (P21 ja especificou)
3. Verificar: `grep -r "bias\|viés\|discrimin" --include="*.py" | grep -v fairness_guard` — zero logica fora do SSOT

**Status: 90% SSOT** — falta extrair config para YAML e post-check universal.

---

## CONCERN 2: LGPD/PRIVACY SERVICE

**Estado atual:** 4 componentes complementares (NAO duplicados — funcoes diferentes).

| Componente | Arquivo | Funcao |
|-----------|---------|--------|
| **PII Masking** | `app/shared/pii_masking.py` | Strip PII antes do LLM (LIA-C04) |
| **Consent Management** | `app/api/v1/consent_management.py` + `granular_consent.py` | CRUD consentimento |
| **Data Subject Requests** | `app/api/v1/data_subject_requests.py` | LGPD Art. 18 (acesso, exclusao) |
| **LGPD Compliance API** | `app/api/v1/lgpd_compliance.py` | Dashboard compliance |

**Fonte canonica proposta:** Nao e duplicacao — sao camadas complementares. Manter como esta.

**SSOT por subconcern:**
- PII strip: `app/shared/pii_masking.py` (unico) + `PIIMaskingFilter` em logging handler
- Consentimento: `app/api/v1/consent_management.py` (unico)
- DSR: `app/api/v1/data_subject_requests.py` (unico)

**O que falta:** `candidates.account_id` no Rails (BLK-01 do PX07) — sem isso, LGPD e violado em toda query de candidato.

**Status: 85% SSOT** — falta tenant isolation no Rails.

---

## CONCERN 3: AUDIT SERVICE

**Estado atual:** 5 implementacoes que PRECISAM consolidar.

| Implementacao | Arquivo | O que faz | Consumers |
|--------------|---------|-----------|-----------|
| **AuditCallback** | `app/shared/compliance/audit_callback.py` | LangGraph callback — registra tool calls, tokens | Todos ReAct agents |
| **AuditService** | `app/shared/compliance/audit_service.py` | CRUD generico de audit logs | API endpoints |
| **AuditWriter** | `app/shared/compliance/audit_writer.py` | Storage (file/S3) | AuditService |
| **AuditLogRepository** | `app/domains/admin/repositories/audit_log_repository.py` | DB audit logs | LLM config, Auth |
| **JobAuditService** | `app/domains/job_management/services/job_audit_service.py` | Audit de vagas | Job management |
| **SSOAuditLog** | `app/auth/workos_models.py` | Audit de SSO | WorkOS auth |
| **AUDIT_TRAIL** structured log | `app/orchestrator/action_handlers/_handler_hooks.py` | Log JSON de acoes | Orchestrator |

**Problema:** 7 formas diferentes de registrar auditoria. Consumidores nao sabem qual usar.

**Fonte canonica proposta:** `app/shared/compliance/audit_service.py`
- **Responsabilidade:** Unico ponto de entrada para QUALQUER registro de auditoria
- **Interface proposta:**
```python
class AuditService:
    async def record(self, event: AuditEvent) -> None:
        """Registra evento de auditoria. Persiste em DB + storage externo."""

    async def record_agent_action(self, agent_id, action, result, context) -> None:
        """Atalho para acoes de agentes (usa AuditCallback internamente)."""

    async def record_user_action(self, user_id, action, resource, context) -> None:
        """Atalho para acoes de usuarios."""

    async def query(self, filters: AuditFilter) -> list[AuditEvent]:
        """Busca eventos de auditoria."""
```

**Plano de consolidacao:**
1. Expandir `AuditService` com metodos `record_agent_action` e `record_user_action`
2. `AuditCallback` permanece como adapter LangGraph → `AuditService.record_agent_action()`
3. `AuditLogRepository` se torna a camada de persistencia do `AuditService`
4. `JobAuditService` e `SSOAuditLog` migram para `AuditService.record_user_action()`
5. `AUDIT_TRAIL` structured log migra para `AuditService.record_agent_action()`
6. Teste: `grep -r "create_log\|write_audit\|audit_trail\|AUDIT_TRAIL" --include="*.py"` — todos devem apontar para AuditService

**Status: 50% SSOT** — precisa consolidacao significativa. Esforco: M (3-5 dias).

---

## CONCERN 4: PERSONA/IDENTITY SERVICE

**Estado atual:** Prompts de persona espalhados em multiplos locais.

| Local | Tipo | Conteudo |
|-------|------|---------|
| `app/prompts/domains/*.yaml` | 10+ YAML files | Prompts por dominio |
| `app/prompts/` (PromptLoader) | Python loader | Carrega YAMLs |
| `app/core/prompt_version_loader.py` | Versionamento | A/B testing de prompts |
| `app/domains/*/agents/*_system_prompt.py` | Constants inline | DOMAIN_INSTRUCTIONS por agente |
| `app/services/onboarding_prompts.py` | Prompts de onboarding | Hardcoded |
| `app/shared/prompts/system_prompt_builder.py` | Builder central | Monta prompts compostos |

**Problema:** 2 patterns coexistem — YAML (via PromptLoader) e constants inline (DOMAIN_INSTRUCTIONS). Persona da LIA nao e unificada.

**Fonte canonica proposta:** `app/shared/prompts/system_prompt_builder.py` + `app/prompts/domains/*.yaml`
- **Responsabilidade:** SystemPromptBuilder monta prompt final. YAMLs sao a fonte de texto.
- **Interface:**
```python
class SystemPromptBuilder:
    @staticmethod
    def build(domain: str, context: dict) -> str:
        """Monta system prompt completo: persona base + domain-specific + context."""

    @staticmethod
    def get_persona_base() -> str:
        """Retorna persona base da LIA (tom, estilo, limites). UM UNICO LUGAR."""
```

**Plano de consolidacao:**
1. Criar `app/prompts/persona_base.yaml` — persona unificada da LIA
2. Migrar DOMAIN_INSTRUCTIONS inline para `app/prompts/domains/{domain}.yaml`
3. Migrar `onboarding_prompts.py` hardcoded para YAML
4. `SystemPromptBuilder.build()` compoe: persona_base + domain_yaml + tenant_context + calibration_weights
5. Teste: `grep -r "DOMAIN_INSTRUCTIONS\|SYSTEM_PROMPT.*=" --include="*.py" app/domains/` — zero constants inline

**Status: 40% SSOT** — pattern existe (PromptLoader + YAML) mas muitos dominios ainda usam inline. Esforco: M (3-5 dias).

---

## CONCERN 5: LLM CONFIGURATION SERVICE

**Estado atual:** Factory sofisticada, mas com bypasses.

| Componente | Arquivo | Status |
|-----------|---------|--------|
| **LLMProviderFactory** (deprecated) | `app/shared/providers/llm_factory.py` | DEPRECATED — global state |
| **ProviderContainer** (per-tenant) | `app/shared/providers/llm_factory.py` | SSOT — per-tenant DI |
| **TenantProviderRegistry** | `app/shared/providers/llm_factory.py` | Registry per-tenant |
| **get_provider_for_tenant()** | `app/shared/providers/llm_factory.py` | Entry point canonico |
| **tenant_llm_context.py** | `app/shared/tenant_llm_context.py` | Config loader per-tenant |
| **LLM config API** | `app/api/v1/llm_config.py` | Admin UI para config |
| **Bypasses diretos** | ~15 instantiacoes (genai.Client, ChatAnthropic) | VIOLACAO |

**Fonte canonica:** `get_provider_for_tenant(company_id)` — ja funciona.

**Plano de consolidacao:**
1. Remover `LLMProviderFactory` class-level methods (deprecated)
2. Script: `scripts/check_llm_factory_enforcement.py` ja existe — rodar no CI
3. Migrar 15 bypasses diretos para usar factory
4. Teste: `grep -r "ChatAnthropic(\|genai.Client(\|ChatOpenAI(" --include="*.py" | grep -v factory | grep -v test` — zero

**Status: 85% SSOT** — factory existe e funciona. Faltam remocao de bypasses. Esforco: S (1-2 dias).

---

## CONCERN 6: MEMORY/CONTEXT SERVICE

**Estado atual:** 4 camadas complementares (NAO duplicadas).

| Camada | Arquivo | Funcao |
|--------|---------|--------|
| WorkingMemoryService | `libs/agents-core/.../working_memory.py` | Memoria de sessao |
| LongTermMemoryService | `libs/agents-core/.../long_term_memory.py` | Memoria cross-sessao |
| ConversationMemory | `app/domains/recruiter_assistant/services/conversation_memory.py` | Historico de chat |
| MemoryIntegration | `libs/agents-core/.../memory_integration.py` | Combina working + long-term |

**Status: 80% SSOT** — MemoryIntegration ja e o ponto de entrada. ConversationMemory e separado (per-domain).

**O que falta:** Unificar ConversationMemory como consumer de MemoryIntegration (nao independente).

---

## CONCERN 7: ORCHESTRATION SERVICE

**Estado atual:** JA E SSOT.

**Fonte canonica:** `app/orchestrator/main_orchestrator.py` + `app/orchestrator/cascaded_router.py`
- MainOrchestrator e o UNICO entry point
- CascadedRouter e o UNICO router
- DomainRegistry e o UNICO registry de dominios

**Status: 95% SSOT** — nenhuma duplicacao.

---

## CONCERN 8: TOOL REGISTRY

**Estado atual:** 1 registry central + 12 registries de dominio.

| Registry | Tipo | Tools |
|----------|------|-------|
| `app/tools/registry.py` + `tool_registry_metadata.yaml` | Central | Schema + metadata |
| `app/domains/sourcing/agents/sourcing_tool_registry.py` | Dominio | get_sourcing_tools() |
| `app/domains/pipeline/agents/pipeline_tool_registry.py` | Dominio | get_pipeline_tools() |
| `app/domains/automation/agents/automation_tool_registry.py` | Dominio | get_automation_tools() |
| ... (9 outros) | Dominio | get_{domain}_tools() |

**NAO e duplicacao** — e pattern intencional (registry central + registries de dominio que filtram subset).

**Fonte canonica:** `app/tools/tool_registry_metadata.yaml` e o SSOT para schemas. Registries de dominio sao views filtradas.

**Status: 90% SSOT.**

---

## CONCERN 9: ERROR HANDLING

**Estado atual:** 3475 referencias, sem padrao unificado.

| Pattern | Uso | Problema |
|---------|-----|---------|
| `raise HTTPException(status_code=X)` | API endpoints | Status codes inconsistentes |
| `try/except Exception` broad | Muitos locais | Silencia erros |
| `CircuitBreaker` | LLM providers | BOM — unico SSOT |
| Domain-specific errors | Nenhum | Nao existem |

**Fonte canonica proposta:** `app/shared/errors.py` (NOVO)
```python
class LIAError(Exception):
    """Base para todos os erros LIA."""
    error_code: str
    status_code: int = 500

class AgentError(LIAError): ...
class ToolError(LIAError): ...
class TenantError(LIAError): ...
class ComplianceError(LIAError): ...
class IntegrationError(LIAError): ...
```

**Plano:** Criar hierarquia de erros, migrar gradualmente. Esforco: L (5-7 dias, incremental).

**Status: 20% SSOT** — CircuitBreaker e SSOT para resiliencia, mas erros nao sao padronizados.

---

## CONCERN 10: VALIDATION SCHEMAS

**Estado atual:** Pydantic models em cada endpoint. Sem schema compartilhado entre Python e frontend.

**Fonte canonica:** Pydantic models JA SAO SSOT no Python. O gap e:
- Frontend usa tipos TypeScript separados (nao gerados do Pydantic)
- Rails usa Strong Parameters (desconectado)

**Plano:** Gerar tipos TypeScript a partir de OpenAPI spec do FastAPI. Esforco: M.

**Status: 70% SSOT** no Python. 0% cross-layer.

---

## CONCERN 11: PROTECTED ATTRIBUTES REGISTRY

**Estado atual:** Hardcoded em `fairness_guard.py` (IMPLICIT_BIAS_TERMS dict + regex patterns).

**Fonte canonica proposta:** `config/protected_attributes.yaml`
```yaml
jurisdictions:
  brazil:
    legal_basis: "CLT Art. 373-A, Lei 9.029/95, Lei 12.984/14, CF Art. 5"
    attributes:
      - category: gender
        terms: ["sexo", "genero", "masculino", "feminino"]
      - category: race
        terms: ["raca", "cor", "etnia", "negro", "branco"]
      - category: age
        terms: ["idade", "jovem", "velho", "senior"]
      # ...
  eu:
    legal_basis: "EU AI Act Art. 13, GDPR"
    attributes: [...]
```

**Consumidores:** FairnessGuard, bias audit, prompt templates, UI labels.

**Status: 60% SSOT** — FairnessGuard e SSOT para enforcement, mas termos hardcoded em .py.

---

## CONCERN 12: CALIBRATION/FEEDBACK SERVICE

**Estado atual:** 6 canais de feedback, maioria desconectada (P19).

| Canal | SSOT | Consumer |
|-------|------|---------|
| CalibrationService | `app/domains/analytics/services/calibration_service.py` | Dashboard (nao agentes) |
| FeedbackLearningService | `app/domains/analytics/services/feedback_learning_service.py` | Wizard (parcial) |
| SuggestionFeedbackRepository | `app/domains/cv_screening/repositories/` | API stats |
| SearchFeedbackRepository | `app/domains/recruitment/repositories/` | Ninguem |
| LearningExtractor | `libs/agents-core/` | Todos agentes (memoria) |
| OutcomeTracker | `app/domains/job_management/services/outcome_tracker.py` | API outcomes |

**Problema:** NAO e duplicacao — sao canais diferentes. O problema e que nao sao CONSUMIDOS.

**Plano de consolidacao:** NAO consolidar em 1 — manter canais separados. Fechar os loops:
1. CalibrationWeight → consumido em `before_process()` de scoring agents
2. SearchFeedback → consumido em `multi_strategy_search.py` para re-ranking
3. FeedbackLearningService.apply_learning() → chamado por wizard automaticamente
4. Outcomes → alimentam OutcomePredictor quando dados suficientes

**Status: 40% SSOT** — dados coletados mas nao consumidos.

---

## CONCERN 13: COMMUNICATION CHANNELS

**Estado atual:** Multi-channel via adapters.

| Canal | SSOT | Arquivo |
|-------|------|---------|
| Email | Mailgun + Resend fallback | `app/shared/channels/adapters/email_adapter.py` |
| WhatsApp | Twilio | `app/shared/channels/adapters/whatsapp_adapter.py` |
| SMS | Twilio | `app/shared/channels/adapters/sms_adapter.py` |
| Teams | Microsoft Graph | `app/shared/channels/adapters/teams_adapter.py` |
| In-app | Bell notifications | `app/shared/channels/adapters/in_app_adapter.py` |
| Router | `app/shared/channels/channel_router.py` | Decide qual canal usar |

**Status: 85% SSOT** — pattern de adapters bem estruturado. BLOQUEADO por config ausente (MAILGUN_API_KEY, TWILIO).

---

## CONCERN 14: TENANT CONFIGURATION

**Estado atual:** Multiplos pontos de config per-tenant.

| Config | SSOT | Arquivo |
|--------|------|---------|
| LLM provider/keys | `llm_config` table | `app/api/v1/llm_config.py` |
| Token budget | Redis | `app/orchestrator/tenant_budget.py` |
| Guardrails | DB | `GuardrailRepository` |
| Autonomy policy | DB | `AutonomyEngine` |
| Pipeline templates | Rails DB | Apartment schemas |
| Company hiring policy | DB | `company_hiring_policies` table |

**Status: 80% SSOT** — cada subconcern tem seu SSOT. Falta unificar em dashboard unico.

---

## DIAGRAMA DE DEPENDENCIA ENTRE FONTES CANONICAS

```
PROTECTED_ATTRIBUTES (config/protected_attributes.yaml)
  |
  v
FAIRNESS_SERVICE (fairness_guard.py)
  |
  v
COMPLIANCE_BASE (compliance_base.py) ← PERSONA (system_prompt_builder.py)
  |                                          |
  v                                          v
DOMAIN_REGISTRY (registry.py)         PROMPT_LOADER (prompts/domains/*.yaml)
  |
  v
ORCHESTRATOR (main_orchestrator.py)
  |       |
  v       v
AUDIT   MEMORY         LLM_FACTORY        TOOL_REGISTRY
  |       |               |                    |
  v       v               v                    v
DB    Redis/pgvector   ProviderContainer   tool_registry_metadata.yaml
```

---

## ORDEM DE CONSOLIDACAO RECOMENDADA

| Ordem | Concern | Esforco | Pre-requisito | ROI |
|-------|---------|---------|---------------|-----|
| 1 | **LLM Factory** (remover bypasses) | S (1-2d) | Nenhum | ALTO — elimina instantiacoes diretas |
| 2 | **Protected Attributes** (YAML externo) | S (1d) | Nenhum | MEDIO — configuravel por jurisdicao |
| 3 | **Fairness post-check universal** | S (1d) | #2 | ALTO — compliance completo |
| 4 | **Persona unificada** (YAML + builder) | M (3-5d) | Nenhum | ALTO — consistencia de voz da LIA |
| 5 | **Calibration loops** (fechar) | M (3-5d) | PX07 Sprint 1 | ALTO — agentes aprendem |
| 6 | **Audit consolidacao** | M (3-5d) | Nenhum | MEDIO — observabilidade |
| 7 | **Error hierarchy** | L (5-7d) | Nenhum | MEDIO — debugging |
| 8 | **Validation cross-layer** (OpenAPI → TypeScript) | M (3-5d) | Nenhum | BAIXO — devex |

**Esforco total estimado: ~25-35 dias de trabalho** (parcialmente paralelizavel).

---

## RESUMO EXECUTIVO

### O que JA e SSOT (manter)
1. **FairnessGuard** — 1 implementacao, enforcement via heranca (90%)
2. **MainOrchestrator** — unico entry point (95%)
3. **CascadedRouter** — unico router (95%)
4. **DomainRegistry** — auto-discovery com decorator (95%)
5. **ToolRegistry** + YAML — central com views de dominio (90%)
6. **LLM Factory** (ProviderContainer) — per-tenant isolation (85%)
7. **Communication adapters** — pattern limpo com router (85%)

### O que precisa consolidar
1. **Audit** — 7 implementacoes → 1 servico com metodos especializados (50%)
2. **Persona/prompts** — inline + YAML coexistem → tudo para YAML + builder (40%)
3. **Calibration loops** — 6 canais desconectados → fechar loops (40%)
4. **Error handling** — sem hierarquia → criar LIAError base (20%)
5. **Protected attributes** — hardcoded → YAML configuravel (60%)

### Metafora
O codebase e como uma cidade que cresceu organicamente — avenidas principais (Orchestrator, FairnessGuard, LLM Factory) sao largas e bem sinalizadas, mas algumas ruas laterais (audit logs, persona, error handling) ainda sao becos sem saida que nao conectam ao mapa central. O trabalho e pavimentar essas ruas e conecta-las ao grid principal.
