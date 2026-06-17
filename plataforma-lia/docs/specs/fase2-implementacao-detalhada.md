# Fase 2 — Implementação Detalhada: Agentes Consultam Policies

**Versão:** 1.0  
**Data:** 21/02/2026  
**Status:** Planejamento aprovado  
**Dependência:** Fase 1 Completa (CompanyHiringPolicy model + API + Settings UI)

---

## Visão Geral

A Fase 2 conecta o `CompanyHiringPolicy` (criado na Fase 1) aos serviços existentes. Após esta fase, a LIA deixa de usar defaults fixos e passa a respeitar as regras configuradas por cada empresa.

**Princípio:** Todos os serviços continuam funcionando normalmente sem policy (usam defaults). Quando a empresa tem policy, os valores customizados são aplicados automaticamente.

---

## Arquitetura de Integração

```
CompanyHiringPolicy (DB)
        │
        ▼
  PolicyHelper.get_company_policy(company_id)  ← cache em memória
        │
        ├──▶ PolicyMiddleware (injeta no request context)
        │
        ├──▶ SchedulingService (allowed_days, hours, duration)
        ├──▶ CommunicationDispatcher (channel, tone, feedback)
        ├──▶ ScreeningAgent (salary filter, questions)
        ├──▶ FeatureFlagService (automation_rules → flags)
        ├──▶ PolicySyncService (max_days → sla_hours)
        └──▶ UniversalTransitionModal (min_interviews, approval)
```

---

## Sprint 1 (Semana 1-2): Infraestrutura + Scheduling + Communication

### Tarefa 2.1 — PolicyMiddleware

**Arquivo:** `lia-agent-system/app/shared/policy_middleware.py`  
**Tipo:** NOVO  
**Esforço:** P (2h)

**O que faz:**
- FastAPI middleware/dependency que extrai `company_id` do request (header, query param, ou body)
- Chama `get_company_policy(company_id)` e injeta no `request.state.company_policy`
- Serviços downstream podem acessar via `request.state.company_policy` ou via Depends

**Implementação:**

```python
from fastapi import Request, Depends
from app.shared.policy_helper import get_company_policy

async def get_policy_from_request(request: Request) -> dict:
    company_id = (
        request.headers.get("x-company-id") or
        request.query_params.get("company_id") or
        getattr(request.state, "company_id", None)
    )
    if not company_id:
        return get_defaults()
    return await get_company_policy(company_id)
```

**Testes:**
- Request com header → retorna policy da empresa
- Request sem header → retorna defaults
- Policy não existe no DB → retorna defaults (sem erro)

---

### Tarefa 2.2 — Scheduling respeita `scheduling_rules`

**Arquivo:** `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py` (1020 linhas)  
**Tipo:** ADAPTAR  
**Esforço:** M (4h)

**Estado atual:** Serviço usa valores fixos ou parâmetros passados diretamente sem consultar policies.

**Mudanças necessárias:**

1. Importar `get_company_policy` e `get_policy_rule`
2. Nas funções que geram slots de entrevista, consultar:
   - `scheduling_rules.allowed_days` → filtrar dias permitidos
   - `scheduling_rules.allowed_hours` → filtrar janela de horário
   - `scheduling_rules.default_duration_minutes` → duração padrão
   - `scheduling_rules.self_scheduling_enabled` → habilitar auto-agendamento
3. Manter parâmetros explícitos como override (se recrutador especificou, ganha da policy)

**Padrão de integração:**

```python
async def suggest_interview_slots(
    company_id: str,
    ...,
    allowed_days: list = None,      # override explícito
    allowed_hours: dict = None,     # override explícito
    duration_minutes: int = None,   # override explícito
    db: AsyncSession = Depends(get_db)
):
    policy = await get_company_policy(company_id, db)
    
    effective_days = allowed_days or get_policy_rule(
        policy, "scheduling_rules", "allowed_days", ["mon","tue","wed","thu","fri"]
    )
    effective_hours = allowed_hours or get_policy_rule(
        policy, "scheduling_rules", "allowed_hours", {"start": "09:00", "end": "18:00"}
    )
    effective_duration = duration_minutes or get_policy_rule(
        policy, "scheduling_rules", "default_duration_minutes", 60
    )
    # ... rest of logic uses effective_* values
```

**Testes:**
- Empresa sem policy → usa defaults (seg-sex, 09-18, 60min)
- Empresa com policy `allowed_days=["mon","wed","fri"]` → slots apenas nesses dias
- Override explícito `duration_minutes=30` → ignora policy, usa 30
- `self_scheduling_enabled=true` → habilita fluxo de auto-agendamento

**Também adaptar:** `lia-agent-system/app/domains/interview_scheduling/services/calendar_service.py`

---

### Tarefa 2.3 — Communication respeita `communication_rules`

**Arquivo:** `lia-agent-system/app/domains/communication/services/communication_dispatcher.py` (359 linhas)  
**Tipo:** ADAPTAR  
**Esforço:** M (4h)

**Estado atual:** Dispatcher tem métodos `send_email`, `send_whatsapp`, `send_sms`. Canal é sempre especificado pelo chamador.

**Mudanças necessárias:**

1. Novo método `dispatch_message(company_id, candidate_id, message, channel=None)`:
   - Se `channel` não especificado → consulta `communication_rules.preferred_channel`
   - Fallback: whatsapp → email → sms
2. Injetar `lia_tone` nos templates de mensagem e system prompts:
   - "professional" → Tom formal, tratamento por "Sr./Sra."
   - "friendly" → Tom informal, primeiro nome
   - "formal" → Tom institucional, linguagem jurídica
   - **Arquivos de prompt a adaptar:** system prompts do `CommunicationDispatcher`, templates de email/WhatsApp em `app/domains/communication/`, e qualquer prompt builder que gere mensagens ao candidato. Mapear `lia_tone` para um modifier de prompt que é concatenado ao system prompt base.
3. `auto_rejection_feedback`:
   - Se `true` → envia feedback automaticamente ao rejeitar
   - Se `false` → apenas notifica recrutador que feedback está pendente
4. `rejection_feedback_deadline_hours`:
   - Registra deadline para envio de feedback
   - Usado pela Fase 3 (PipelineMonitor) para gerar alertas

**Testes:**
- Canal não especificado + policy `preferred_channel="email"` → envia email
- Canal explícito "whatsapp" → ignora policy, envia whatsapp
- `lia_tone="friendly"` → template usa primeiro nome
- `auto_rejection_feedback=true` → ao rejeitar, feedback é enviado automaticamente

---

## Sprint 2 (Semana 2-3): Screening + Feature Flags + Sync

### Tarefa 2.4 — Screening respeita `screening_rules`

**Arquivos:**
- `lia-agent-system/app/domains/cv_screening/agents/screening_agent.py`
- `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`
- `lia-agent-system/app/domains/cv_screening/services/screening_question_set_service.py`  
**Tipo:** ADAPTAR  
**Esforço:** M (4h)

**Mudanças necessárias:**

1. **Filtro de pretensão salarial:**
   - Consultar `screening_rules.salary_expectation_filter`
   - Se `true` e candidato tem pretensão > vaga + `salary_tolerance_percent` → flag no score WSI
   - Não elimina automaticamente, apenas adiciona sinal negativo ao score

2. **Experiência mínima:**
   - `experience_policy="per_job"` → usa experiência definida na vaga (comportamento atual)
   - `experience_policy="global"` → empresa define mínimo global (ex: 2 anos para todas as vagas)

3. **Perguntas padrão:**
   - `default_screening_questions` → ao criar nova vaga, essas perguntas são adicionadas automaticamente ao `ScreeningQuestionSet`
   - Recrutador pode remover/editar depois

**Testes:**
- Sem policy → triagem funciona normalmente (sem filtro salarial)
- Com `salary_expectation_filter=true, tolerance=15%` → candidato com pretensão 20% acima recebe flag
- `default_screening_questions=["Qual sua disponibilidade?"]` → nova vaga criada com essa pergunta

---

### Tarefa 2.5 — PolicySyncService

**Arquivo:** `lia-agent-system/app/shared/policy_sync_service.py`  
**Tipo:** NOVO  
**Esforço:** P (3h)

**O que faz:**
- Quando uma policy é salva (via API ou chat), sincroniza dados derivados:
  1. `pipeline_rules.max_days_in_stage` (dias) → `RecruitmentStage.sla_hours` (horas × 24)
  2. `automation_rules.*` → Feature flags da empresa

**Implementação:**

```python
async def sync_policy_to_models(company_id: str, policy: dict, db: AsyncSession):
    max_days = policy.get("pipeline_rules", {}).get("max_days_in_stage")
    if max_days:
        if isinstance(max_days, dict):
            for stage_name, days in max_days.items():
                await _update_stage_sla(company_id, stage_name, days * 24, db)
        elif isinstance(max_days, (int, float)):
            await _update_all_stages_sla(company_id, int(max_days) * 24, db)
    
    await _sync_feature_flags(company_id, policy.get("automation_rules", {}))
```

**Trigger:** Chamado no endpoint `PUT` e `PATCH` do `hiring_policy.py` após salvar.

**Testes:**
- `max_days_in_stage=5` → `sla_hours=120` em todas as stages
- `max_days_in_stage={"screening": 3, "interview": 7}` → SLAs diferentes por etapa
- Sem `max_days_in_stage` → não altera SLAs existentes

---

### Tarefa 2.6 — Feature Flags mapeiam `automation_rules`

**Arquivo:** `lia-agent-system/app/shared/governance/feature_flag_service.py` (315 linhas)  
**Tipo:** ADAPTAR  
**Esforço:** P (2h)

**Mapeamento:**

| Campo automation_rules | Feature Flag | Efeito |
|---|---|---|
| `auto_screening=true` | `ENABLE_AUTO_SCREENING_{company_id}` | Triagem automática sem confirmação |
| `auto_scheduling=true` | `ENABLE_AUTO_SCHEDULING_{company_id}` | Agendamento automático |
| `auto_stage_advance=true` | `ENABLE_AUTO_STAGE_ADVANCE_{company_id}` | Mover candidato automaticamente |
| `autonomy_level="low"` | Todos `false` | LIA sempre pede confirmação |
| `autonomy_level="medium"` | `auto_screening=true` | Apenas triagem automática |
| `autonomy_level="high"` | Todos `true` | Automação completa |

**Implementação:**
- Novo método `apply_policy_flags(company_id, automation_rules)`
- Chamado pelo `PolicySyncService`
- Feature flags são per-company (não globais)

**Testes:**
- `autonomy_level="low"` → todos os flags false
- `autonomy_level="high"` → todos os flags true
- Override individual: `autonomy_level="low"` mas `auto_screening=true` → apenas screening flag true

---

## Sprint 3 (Semana 3-4): Pipeline + Frontend + Testes E2E

### Tarefa 2.7 — Pipeline Templates conectam RecruitmentStage

**Arquivos:**
- Backend: API de criação de vaga (Job Wizard)
- Frontend: Wizard de vagas  
**Tipo:** ADAPTAR  
**Esforço:** M (4h)

**O que faz:**
- Quando empresa tem `pipeline_templates` configurados, ao criar nova vaga, LIA oferece templates:
  - "Processo Técnico" → [Triagem, Teste Técnico, Entrevista Técnica, Entrevista Cultural, Proposta]
  - "Processo Operacional" → [Triagem, Entrevista, Proposta]
  - "Processo Executivo" → [Triagem, Entrevista RH, Case, Entrevista Diretoria, Referências, Proposta]
- Template selecionado → stages pré-criadas com SLAs e configurações do template

**Testes:**
- Empresa sem templates → wizard funciona como hoje (stages padrão)
- Empresa com template "Técnico" → ao selecionar, stages são configuradas automaticamente
- Template pode ser editado após aplicação

---

### Tarefa 2.8 — Validação de proposta respeita `pipeline_rules`

**Arquivo:** `plataforma-lia/src/components/kanban/components/UniversalTransitionModal.tsx`  
**Tipo:** ADAPTAR  
**Esforço:** M (4h)

**Mudanças necessárias:**

1. Ao mover candidato para etapa "Proposta":
   - Consultar `pipeline_rules.min_interviews_before_offer`
   - Contar entrevistas realizadas pelo candidato
   - Se < mínimo → mostrar aviso: "Atenção: política da empresa exige pelo menos X entrevistas. Este candidato teve Y."
   - Aviso é informativo (não bloqueante), com opção de prosseguir
   
2. `manager_approval_for_offer`:
   - Se `true` → ao confirmar proposta, adicionar sub-status "Aguardando aprovação do gestor"
   - Notificação enviada ao gestor para aprovação

**Frontend:**

```tsx
const handleMoveToOffer = async () => {
  const policy = await fetchCompanyPolicy(companyId);
  const minInterviews = policy?.pipeline_rules?.min_interviews_before_offer || 2;
  const interviewCount = candidate.interviews_completed || 0;
  
  if (interviewCount < minInterviews) {
    setWarning(`Política da empresa: mínimo ${minInterviews} entrevistas. Realizadas: ${interviewCount}.`);
    setShowWarningDialog(true);
    return;
  }
  proceedWithTransition();
};
```

**Backend (enforcement server-side):**
- Novo endpoint: `GET /api/v1/pipeline/validate-transition`
  - Recebe `company_id`, `candidate_id`, `target_stage`
  - Retorna `{ allowed: true/false, warnings: [...], blockers: [...] }`
- **CRÍTICO:** Também enforçar no backend de transição (não só UI):
  - O serviço de transição de pipeline (usado por automações, API direta, e bulk actions) deve chamar `validate-transition` antes de executar
  - Previne bypass da validação via API/automação
  - Se `manager_approval_for_offer=true` e stage = "Proposta" → transição fica bloqueada até aprovação do gestor

**Testes:**
- Candidato com 3 entrevistas, mínimo 2 → transição liberada
- Candidato com 1 entrevista, mínimo 3 → aviso mostrado (UI) + warning retornado (API)
- `manager_approval_for_offer=true` → proposta fica em sub-status "Aguardando aprovação"
- Transição via API direta sem aprovação → bloqueada server-side

---

## Resumo de Tarefas por Sprint

### Sprint 1 (Semana 1-2)

| # | Tarefa | Tipo | Arquivo Principal | Esforço |
|---|---|---|---|---|
| 2.1 | PolicyMiddleware | NOVO | `app/shared/policy_middleware.py` | P |
| 2.2 | Scheduling + scheduling_rules | ADAPTAR | `app/domains/interview_scheduling/services/scheduling_service.py` | M |
| 2.3 | Communication + communication_rules | ADAPTAR | `app/domains/communication/services/communication_dispatcher.py` | M |

### Sprint 2 (Semana 2-3)

| # | Tarefa | Tipo | Arquivo Principal | Esforço |
|---|---|---|---|---|
| 2.4 | Screening + screening_rules | ADAPTAR | `app/domains/cv_screening/agents/screening_agent.py` | M |
| 2.5 | PolicySyncService | NOVO | `app/shared/policy_sync_service.py` | P |
| 2.6 | Feature flags ↔ automation_rules | ADAPTAR | `app/shared/governance/feature_flag_service.py` | P |

### Sprint 3 (Semana 3-4)

| # | Tarefa | Tipo | Arquivo Principal | Esforço |
|---|---|---|---|---|
| 2.7 | Pipeline templates + RecruitmentStage | ADAPTAR | API de vagas + Wizard frontend | M |
| 2.8 | Validação de proposta | ADAPTAR | `UniversalTransitionModal.tsx` | M |
| 2.9 | Testes de integração E2E | NOVO | `app/tests/test_policy_integration.py` | M |

---

## Ordem de Implementação Recomendada

```
2.1 PolicyMiddleware (base para tudo)
  ↓
2.5 PolicySyncService (sincroniza dados derivados)
  ↓
2.6 Feature flags (automation_rules → flags)
  ↓
2.2 Scheduling (usa middleware + policy)
  ↓
2.3 Communication (usa middleware + policy)
  ↓
2.4 Screening (usa middleware + policy)
  ↓
2.7 Pipeline templates (usa PolicySyncService)
  ↓
2.8 Validação de proposta (frontend + backend)
  ↓
2.9 Testes E2E (valida tudo integrado)
```

---

## Critérios de Sucesso (Checklist)

- [ ] PolicyMiddleware injeta policy no contexto de requests
- [ ] Scheduling sugere horários respeitando `allowed_days` e `allowed_hours`
- [ ] CommunicationDispatcher usa `preferred_channel` como fallback
- [ ] LIA usa `lia_tone` configurado nas comunicações
- [ ] `auto_rejection_feedback=true` → feedback enviado automaticamente
- [ ] Filtro de pretensão salarial funciona quando habilitado
- [ ] Perguntas padrão adicionadas a novas vagas
- [ ] `max_days_in_stage` sincroniza com `sla_hours` das etapas
- [ ] Feature flags refletem `automation_rules`
- [ ] Templates de pipeline pré-configuram stages em novas vagas
- [ ] Modal de proposta avisa quando `min_interviews_before_offer` não atendido
- [ ] `manager_approval_for_offer=true` → proposta em sub-status "Aguardando aprovação"
- [ ] Empresa sem policy → tudo funciona com defaults (zero breaking changes)
- [ ] Testes E2E cobrindo todos os cenários acima

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Serviço sem policy falha | Baixa | Alto | Todos os acessos via `get_policy_rule()` com defaults |
| Cache desatualizado após edição | Baixa | Médio | `invalidate_policy_cache()` já chamado em save |
| Conflito entre override e policy | Média | Baixo | Override explícito sempre ganha (documenta prioridade) |
| Regressão em fluxos existentes | Média | Alto | Testes E2E por serviço, antes/depois com policy |
| Performance (query extra por request) | Baixa | Baixo | Cache em memória com TTL, query rápida (index em company_id) |

---

## Métricas de Acompanhamento

| Métrica | Alvo | Como Medir |
|---|---|---|
| Empresas com policy configurada | > 50% em 30 dias | COUNT WHERE setup_progress > 0 |
| Serviços usando policy | 6/6 | Audit log de chamadas a get_company_policy |
| Tempo médio de resposta com policy | < 5ms adicional | Latency monitoring no middleware |
| Bugs de regressão | 0 críticos | Testes automatizados, QA manual |
