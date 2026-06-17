# Auditoria Técnica LIA — Plano de Execução

> **Documento vivo** — atualizado a cada ciclo de planejamento e implementação.
> Serve como guia de referência para o time sobre o que foi identificado, planejado e tratado.

**Fonte:** Relatório de Auditoria Completa WeDOTalent LIA — Fevereiro 2026
**Responsável técnico:** Time WeDOTalent
**Última atualização:** 2026-02-28

---

## Índice

- [Contexto e Metodologia](#contexto-e-metodologia)
- [Mapa Geral de Itens](#mapa-geral-de-itens)
- [Semana 1 — Quick Wins Críticos](#semana-1--quick-wins-críticos)
- [Sprint N — Comunicações via Modal de Transição](#sprint-n--comunicações-via-modal-de-transição)
- [Sprint 1-2 — Fundação e Compliance](#sprint-12--fundação-e-compliance)
- [Sprint 3-5 — Qualidade e Produto](#sprint-35--qualidade-e-produto)
- [Longo Prazo — Evolução Estratégica](#longo-prazo--evolução-estratégica)
- [Log de Implementações](#log-de-implementações)

---

## Contexto e Metodologia

A auditoria foi realizada em fevereiro de 2026 cobrindo todas as camadas da plataforma LIA:

- **Camada L (Legal/Compliance):** LGPD, EU AI Act, privacidade de dados
- **Camada B (Bias/Fairness):** Viés algorítmico, discriminação, FairnessGuard
- **Camada A (Arquitetura/Estabilidade):** Resiliência, timeouts, tratamento de erros
- **Camada F (Frontend):** Dados reais vs. mocks, UX, componentes
- **Camada M (Monetização):** Billing, controle de custos de IA, planos
- **Camada N (Notificações):** Comunicações, canais, agendamentos
- **Camada T (Testes):** Cobertura, qualidade, edge cases

**Critérios de priorização:**
- `CRÍTICO` — Risco legal, segurança ou estabilidade em produção
- `ALTO` — Impacto direto na qualidade do produto ou compliance
- `MÉDIO` — Melhoria significativa mas não bloqueante
- `BAIXO` — Refinamento e otimização

> **Nota importante:** A exploração do código revelou que vários itens listados na auditoria já possuem infraestrutura implementada, mas com gaps específicos. O status "⚠️ Gap" indica "implementado parcialmente / lacuna identificada", diferente de "🔲 Não implementado".

---

## Mapa Geral de Itens

### Camada L — Legal / LGPD / Compliance

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| L1 | Desligar LangSmith por padrão (tracing envia PII para EUA) | CRÍTICO | 1h | ✅ Implementado |
| L2 | Criptografar chaves ATS em repouso (Gupy/Pandapé) | ALTO | 1 dia | ✅ Já implementado — verificado 2026-02-28 |
| L3 | Human review gate antes de rejeição automatizada | CRÍTICO | 2 dias | ✅ Implementado 2026-02-28 |
| L4 | Job de deleção de dados (30/90/180 dias conforme política) | ALTO | 2 dias | ✅ Implementado 2026-02-28 |
| L5 | Granularidade no consentimento de dados por finalidade | MÉDIO | 3 dias | ✅ Implementado 2026-02-28 |
| L6 | Auditoria de retenção de logs de IA | MÉDIO | 1 dia | 🔲 Backlog |
| L7 | Mascaramento de PII em logs estruturados | ALTO | 1 dia | ✅ Implementado 2026-02-28 |
| L8 | Remover token webhook WhatsApp hardcoded | CRÍTICO | 30min | ✅ Implementado |

### Camada B — Bias / Fairness

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| B1 | Remover nome do candidato do payload LLM (viés de gênero/etnia) | CRÍTICO | 1h | ✅ Implementado |
| B2 | Remover GEOGRAPHIC_ADJUSTMENTS discriminatório (JP/KR/IN +15%) | CRÍTICO | 2h | ✅ Implementado |
| B3 | FairnessGuard verificar outputs do LLM (hoje só verifica inputs) | ALTO | 2 dias | ✅ Implementado 2026-02-28 |
| B4 | Auditoria dos system prompts para linguagem tendenciosa | MÉDIO | 1 dia | ✅ Implementado 2026-02-28 |
| B4.1 | Adicionar `FAIRNESS_AND_COMPLIANCE` ao `cv_screening/pipeline_system_prompt.py` (gap identificado em B4) | MÉDIO | ½ dia | ✅ Implementado 2026-02-28 |
| B5 | Testes de disparate impact nos scores WSI | ALTO | 3 dias | ✅ Implementado 2026-02-28 |
| B6 | Documentação de limitações do modelo para usuários finais | BAIXO | 1 dia | 🔲 Backlog |

### Camada A — Arquitetura / Estabilidade

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| A1 | Timeout no loop LangGraph (Job Wizard pode travar indefinidamente) | CRÍTICO | 2h | ✅ Implementado |
| A2 | Retry/fallback Gemini resposta vazia (silencioso, sem log) | ALTO | 3h | ✅ Implementado |
| A3 | Persistência de estado LangGraph via checkpoints nativos | ALTO | 2 dias | ✅ Implementado 2026-02-28 |
| A4 | Notas de entrevista — verificar gaps de persistência | MÉDIO | 1 dia | ✅ Implementado 2026-02-28 |
| A5 | Circuit breaker para chamadas externas (Pearch, Deepgram, OpenMic) | MÉDIO | 2 dias | ✅ Implementado 2026-02-28 |
| A6 | Pooling de conexões DB otimizado para carga de produção | MÉDIO | 1 dia | 🔲 Backlog |

### Camada F — Frontend

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| F1 | Substituir mock data no Kanban por dados reais | ALTO | 3 dias | ✅ Reavaliado 2026-02-28 — `mockCandidates` é código morto (importado mas nunca referenciado); Kanban já usa API real via `liaApi.listCandidates()`. Limpeza da importação é 1 linha. Não é problema real. |
| F2 | Gráficos e charts conectados à API real (hoje: geração aleatória) | ALTO | 2 dias | 🔲 Reavaliado 2026-02-28 — Páginas com `generateTimeSeriesData()` são código arquivado (nunca renderizado no MVP). Sidebar tem apenas 3 itens. Tratar quando Analytics entrar no roadmap do MVP. |
| F3 | KPIs e métricas do Painel de Controle com dados reais | MÉDIO | 2 dias | 🔲 Reavaliado 2026-02-28 — Telas com KPIs hardcoded (`executive-dashboard-page`, `indicators-page`, etc.) são componentes órfãos — nenhum `page.tsx` ou case no switch as renderiza para o usuário. MVP usa dados reais. Tratar quando essas telas entrarem no roadmap. |
| F4 | Estados de loading/error/empty em todas as listagens | MÉDIO | 1 dia | 🔲 Backlog |

### Camada M — Monetização

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| M1 | Billing ativo com enforcing de limites por plano | ALTO | 2 dias | ✅ Implementado 2026-02-28 |
| M2 | Trial com expiração real e bloqueio de acesso | ALTO | 1 dia | ✅ Implementado 2026-02-28 |
| M3 | Onboarding de billing no sign-up | MÉDIO | 1 dia | 🔲 Backlog |
| M4 | Dashboard de custos de IA para admins (AI Credits) | MÉDIO | 2 dias | ✅ Implementado 2026-02-28 |
| M5 | Alertas de consumo próximo ao limite do plano | MÉDIO | 1 dia | ✅ Implementado 2026-02-28 |
| M6 | Alertas de billing (falha de pagamento, renovação) | MÉDIO | 1 dia | 🔲 Backlog |
| M7 | Modelo RPO (pagamento por contratação) | BAIXO | 5 dias | 🔲 Backlog |
| M8 | BYOK — Bring Your Own Key (chave Anthropic do cliente) | BAIXO | 3 dias | 🔲 Backlog |

### Camada N — Notificações / Comunicações

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| N-T1 | LIA descreve comunicação no chat do modal antes de confirmar | ALTO | ½ dia | ✅ Implementado 2026-02-28 |
| N-T2 | Badge "Status da Vaga" → interativo (pausar/fechar a partir do Kanban) | ALTO | ½ dia | ✅ Implementado 2026-02-28 |
| N-T3 | Badge "Screening Status" → interativo (pausar/encerrar triagem) | ALTO | ½ dia | ✅ Implementado 2026-02-28 |
| N-T4 | Conectar `CloseVacancyModal` ao Kanban (modal pronto, não integrado) | ALTO | ½ dia | ✅ Implementado 2026-02-28 |
| N-T5 | Expor `JobStatusModal` no Kanban individual (hoje só na listagem) | MÉDIO | ½ dia | ✅ Implementado 2026-02-28 |
| N-T6 | Google Calendar — integração completa (nenhum código Google existe hoje) | ALTO | 5-7 dias | ⏸️ Adiado — requer alinhamento com time de desenvolvimento |
| N2 | Verificar se triggers da communication matrix disparam nas transições | MÉDIO | ½ dia | ✅ Implementado 2026-02-28 |
| N3 | Preferências de canal por candidato end-to-end | MÉDIO | 4-5 dias | ✅ Implementado 2026-02-28 |

### Camada T — Testes

| ID | Descrição | Severidade | Esforço | Status |
|----|-----------|------------|---------|--------|
| T1 | Testes unitários para rubric_evaluation_service | ALTO | 2 dias | ✅ Implementado 2026-02-28 |
| T2 | Testes de integração para pipeline de triagem completo | ALTO | 3 dias | ✅ Implementado 2026-02-28 |
| T3 | Testes E2E para fluxo de criação de vaga | MÉDIO | 2 dias | ✅ Implementado 2026-02-28 |
| T4 | Testes de carga para endpoints críticos | MÉDIO | 2 dias | ✅ Implementado 2026-02-28 |

---

## Semana 1 — Quick Wins Críticos

**Período:** 2026-02-28
**Escopo:** 6 correções de alta severidade, baixo risco de regressão, impacto direto em LGPD, bias, segurança e estabilidade.

### L1 — Desligar LangSmith por padrão

**Problema:** `LANGCHAIN_TRACING_V2: bool = True` envia dados de conversas (CVs, nomes, CPFs, conteúdo de entrevistas) para servidores da LangChain nos EUA por padrão. Viola o princípio de minimização do LGPD (art. 46).

**Arquivo:** `lia-agent-system/app/core/config.py:58`

**Mudança:**
```python
# Antes
LANGCHAIN_TRACING_V2: bool = True

# Depois
LANGCHAIN_TRACING_V2: bool = False  # LGPD: opt-in only, nunca por padrão
```

**Impacto:** Zero risco de regressão. O tracing só funciona se `LANGCHAIN_API_KEY` estiver definido. **Status: ✅ Implementado em 2026-02-28**

---

### L8 — Remover token webhook WhatsApp hardcoded

**Problema:** `os.getenv("WHATSAPP_VERIFY_TOKEN", "lia_whatsapp_verify")` — o fallback `"lia_whatsapp_verify"` é um segredo hardcoded no repositório. Qualquer pessoa com acesso ao código pode forjar requisições ao webhook.

**Arquivo:** `lia-agent-system/app/domains/communication/services/whatsapp_meta_service.py:55`

**Mudança:**
```python
# Antes
self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "lia_whatsapp_verify")

# Depois
self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
if not self.verify_token:
    raise ValueError("WHATSAPP_VERIFY_TOKEN não configurado — defina a variável de ambiente")
```

**Impacto:** Falha explícita na inicialização se a variável não estiver configurada — melhor do que aceitar requisições inválidas silenciosamente. **Status: ✅ Implementado em 2026-02-28**

---

### B2 — Remover GEOGRAPHIC_ADJUSTMENTS discriminatório

**Problema:** `GEOGRAPHIC_ADJUSTMENTS` aplica multiplicador `1.15` (exige 15% mais anos de experiência) para candidatos do Japão, Coreia do Sul e Índia. Discriminação por origem nacional — viola EU AI Act art. 5 e representa risco legal e reputacional grave.

**Arquivo:** `lia-agent-system/app/domains/cv_screening/services/calibration_profiles.py:813-867`

**Mudança:** Remoção do bloco `"slow_progression"` com JP/KR/IN. O dict completo foi revisado — a lógica de ajuste por país de origem é removida; critérios de avaliação passam a ser neutros.

**Impacto:** Correção de discriminação algorítmica confirmada. Nenhum impacto em fluxos de negócio. **Status: ✅ Implementado em 2026-02-28**

---

### B1 — Remover nome do candidato do payload LLM

**Problema:** `_extract_cv_content()` inclui `Name: {candidate_data['name']}` no contexto enviado ao LLM para avaliação. Nome é PII e introduz viés de gênero e etnia na avaliação automatizada. Viola LGPD (art. 11) e o princípio de avaliação cega do FairnessGuard.

**Arquivo:** `lia-agent-system/app/domains/cv_screening/services/rubric_evaluation_service.py:441-445`

**Mudança:** Remoção de todos os campos de identidade pessoal (nome, email, telefone) do contexto enviado ao LLM. O modelo avalia apenas competências, experiências e qualificações.

**Impacto:** Melhora a qualidade da avaliação além de corrigir o compliance. **Status: ✅ Implementado em 2026-02-28**

---

### A1 — Timeout no loop LangGraph (Job Wizard)

**Problema:** O loop `while current_node != END_NODE and iteration < MAX_ITERATIONS` não tem timeout de wall-clock. Se um nó LLM travar (rede lenta, rate limit, hang da API), a execução fica bloqueada indefinidamente, consumindo conexões do pool FastAPI e causando cascata de timeouts no frontend.

**Arquivo:** `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py:240-270`

**Mudança:**
```python
import asyncio

try:
    async with asyncio.timeout(120):  # 2 minutos wall-clock máximo
        while current_node != self.END_NODE and iteration < self.MAX_ITERATIONS:
            iteration += 1
            state, duration = await self._execute_node(current_node, state)
except asyncio.TimeoutError:
    logger.error("JobWizardGraph timeout após 120s", extra={"iteration": iteration})
    raise
```

**Impacto:** O timeout só dispara em casos patológicos. Sessões normais completam em menos de 30 segundos. **Status: ✅ Implementado em 2026-02-28**

---

### A2 — Retry/fallback Gemini resposta vazia

**Problema:** Os três métodos de `llm_gemini.py` retornam silenciosamente `""` ou `"{}"` quando `response.text` é `None`. Nenhum retry, nenhum log — o caller recebe dados vazios sem saber que houve falha.

**Arquivo:** `lia-agent-system/app/shared/providers/llm_gemini.py:41, 50, 108`

**Mudança:** Adição de retry com backoff exponencial (até 3 tentativas) e raise explícito com log estruturado na terceira falha.

**Impacto:** Elimina perda silenciosa de dados. Erros do Gemini passam a ser visíveis em logs e alertas. **Status: ✅ Implementado em 2026-02-28**

---

## Sprint N — Comunicações via Modal de Transição

**Período:** A partir de 2026-02-28
**Escopo:** Fechar o ciclo de comunicação com candidatos dentro do modal de transição existente — sem construir do zero, tudo baseado em infraestrutura já implementada. Inclui badges interativos no header do Kanban, conexão dos modais de vaga já prontos, e comportamento conversacional da LIA descrevendo comunicações antes de confirmar. Google Calendar entra como último item deste sprint (sprint futuro isolado).

**Contexto técnico importante levantado durante planejamento:**
- `UniversalTransitionModal` é o modal oficial de transições — todo fluxo passa por ele
- `StageTransitionActionsModal` é o modal de envio manual já implementado (email, WhatsApp, WSI, agendar entrevista, apenas mover) — deve ser reutilizado, não recriado
- `CloseVacancyModal` está 100% implementado mas não conectado a nenhuma página
- `JobStatusModal` está implementado e integrado na listagem de vagas, mas não no Kanban individual
- Badge "sugestões da LIA" já é interativo — padrão estabelecido para badges clicáveis
- Comunicação é sempre conversacional no chat — sem chips ou quick-reply buttons

---

### N-T1 — LIA descreve comunicação no chat do modal de transição

**Problema:** Quando o recrutador usa `lia_auto` no `UniversalTransitionModal`, a comunicação disparada para o candidato é invisível — o recrutador não sabe o que será enviado antes de confirmar.

**Arquivo:** `lia-agent-system/app/domains/pipeline/agents/system_prompt.py`

**O que fazer:**
Ajustar o system prompt do `PipelineTransitionAgent` para incluir, nas respostas de confirmação de transição, uma descrição clara do que será enviado ao candidato.

Comportamento esperado — transição individual:
```
"Vou mover João Silva para Reprovado com substatus
'Competências técnicas insuficientes'. Um email de feedback
personalizado será enviado automaticamente. Confirma?"
```

Comportamento esperado — transição em lote:
```
"5 candidatos serão movidos para Reprovado. Cada um receberá
um email personalizado com base no substatus inferido:
• João Silva — Competências técnicas insuficientes
• Maria Santos — Fit cultural incompatível
• Pedro Costa — Experiência abaixo do requerido
• Ana Lima — Pretensão salarial fora do budget
• Carlos Rocha — Indisponibilidade imediata
Confirma o envio?"
```

Se o recrutador quiser editar: digita "quero editar" ou "manual" → `StageTransitionActionsModal` abre com template pré-selecionado. Sem chips, sem novos componentes.

**Risco:** Baixo — ajuste de prompt, sem mudança de infraestrutura.

**Status:** ✅ Implementado 2026-02-28 — `COMMUNICATION_TRANSPARENCY_RULES` adicionado ao `pipeline_system_prompt.py` com 27 few-shot examples.

---

### N-T2 — Badge "Status da Vaga" → interativo

**Problema:** Não há forma de pausar ou fechar uma vaga dentro do Kanban — o recrutador precisa sair para a listagem de vagas para fazer isso.

**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx` (~linha 4793)

**O que fazer:**
Transformar o `<Badge>` estático de status da vaga em elemento interativo seguindo o padrão do badge "sugestões da LIA" (já usa `cursor-pointer hover:bg-wedo-cyan-dark`):

| Estado | Comportamento ao clicar |
|--------|------------------------|
| `Ativa` | Abre Popover: ⏸ Pausar Vaga / ✕ Fechar Vaga |
| `Paralisada` | Abre `JobStatusModal` direto em modo reativação |

Visual: `cursor-pointer hover:bg-[#c8d4c7]` — tom escuro do `#DCE4DB` existente, sem shadow, sem outline extra. DS v4.2.1 compliant.

**Risco:** Baixo — mudança visual e de state management, sem impacto em lógica de negócio.

**Status:** ✅ Implementado 2026-02-28 — Popover com Pausar/Fechar/Reativar integrado ao header do Kanban.

---

### N-T3 — Badge "Screening Status" → interativo

**Problema:** O badge de status da triagem é informativo mas não permite ação — recrutador não consegue pausar ou encerrar a triagem diretamente do Kanban.

**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx` (~linha 4808)

**O que fazer:**

| Estado | Comportamento ao clicar |
|--------|------------------------|
| `active` | Popover: ⏸ Pausar Triagem / ✕ Encerrar Triagem |
| `paused` | Abre confirmação: retomar triagem |
| `not_started` | Abre configuração de triagem |
| `not_configured` | Abre configuração de triagem |
| `completed` | Badge inerte — sem ação |

Visual: mesma abordagem do N-T2, cor de hover contextual por estado (amber para paused, emerald para active).

**Risco:** Baixo.

**Status:** ✅ Implementado 2026-02-28 — Popover interativo com Iniciar/Pausar/Retomar/Configurar por estado da triagem.

---

### N-T4 — Conectar `CloseVacancyModal` ao Kanban

**Problema:** `CloseVacancyModal` está 100% implementado (2 steps: notifica contratado + lista demais candidatos com checkbox, canal e template) mas não é chamado em nenhuma página.

**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
**Modal existente:** `plataforma-lia/src/components/modals/close-vacancy-modal.tsx`

**O que fazer:**
1. Adicionar estado `showCloseVacancyModal` no `job-kanban-page.tsx`
2. Identificar `hiredCandidate` (stage `Contratado`) e `otherCandidates` (demais em processo) a partir dos dados já carregados no Kanban
3. Renderizar `<CloseVacancyModal>` com esses dados — acionado pelo popover do N-T2
4. Callback `onConfirm(payload: CloseVacancyPayload)`:
   - Chama API de fechamento da vaga
   - Dispara comunicação para contratado (hired_notification)
   - Dispara comunicação em lote para demais (other_notifications)

**Risco:** Baixo — modal pronto, trabalho é wiring.

**Status:** ✅ Implementado 2026-02-28 — `CloseVacancyModal` integrado ao Kanban com `hiredCandidate` + `otherCandidates` derivados do `candidatesData`.

---

### N-T5 — Expor `JobStatusModal` (pausar/reativar) no Kanban

**Problema:** `JobStatusModal` funciona em `jobs-page.tsx` para ações em lote, mas não está acessível dentro do Kanban de uma vaga específica.

**Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
**Modal existente:** `plataforma-lia/src/components/modals/job-status-modal.tsx`

**O que fazer:**
1. Adicionar estado `showJobStatusModal`
2. Passar `jobIds={[currentJob.id]}` — sempre array de 1 no contexto do Kanban individual
3. Reutilizar callbacks `onPause()` e `onActivate()` já implementados em `jobs-page.tsx`
4. Acionado pelo popover do N-T2 (opção "Pausar Vaga") e pelo badge "Paralisada" (reativação)

**Risco:** Baixo — reutilização direta de modal e lógica existentes.

**Status:** ✅ Implementado 2026-02-28 — `JobStatusModal` integrado ao Kanban individual com `jobIds={[currentJob.id]}`.

---

### N-T6 — Google Calendar Integration

**Problema:** Microsoft Graph + Outlook Calendar estão 100% implementados. Google Calendar não tem nenhuma linha de código — `meeting_platform: "google_meet"` existe no model mas nunca é usado. Empresas que usam Google Workspace não conseguem sincronizar entrevistas.

**Esforço:** 5-7 dias | **Sprint dedicado**

> **⏸️ Adiado — 2026-02-28**
> Análise revelou que a integração é mais complexa do que aparenta: requer decisão de produto sobre como o cliente escolhe o provider (Microsoft vs. Google), uma tela de Configurações de Integrações no frontend (ainda não existe), e um modelo de autenticação diferente (Service Account com Domain-Wide Delegation no Google Workspace). A plataforma já possui área de admin, mas os próximos passos precisam ser alinhados com o time de desenvolvimento antes de iniciar a implementação. Retomar quando houver demanda concreta de clientes ou quando a tela de Configurações de Integrações estiver planejada.

**Contexto do código atual:**
- `app/services/graph_client.py` — cliente Microsoft completo (276 linhas), referência para o Google
- `app/domains/interview_scheduling/services/calendar_service.py` — usa apenas `GraphAPIClient`
- `app/api/v1/calendar.py` — endpoints todos dependem de `check_graph_configured()`
- `app/models/interview.py` — tem `graph_event_id`, não tem `google_event_id`
- `app/core/config.py` — tem `GOOGLE_APPLICATION_CREDENTIALS` e `GOOGLE_CLOUD_PROJECT` declarados mas nunca usados

**Tarefa 6.1 — Criar `GoogleCalendarClient`** (2 dias)

Arquivo: `lia-agent-system/app/services/google_calendar_client.py`

Métodos necessários (espelho do `GraphAPIClient`):
```python
class GoogleCalendarClient:
    async def create_calendar_event(
        attendees, start_time, duration_minutes,
        summary, description, create_meet_link=True
    ) -> Dict   # retorna event_id + meet_link

    async def get_user_busy_times(
        user_email, start_date, end_date
    ) -> List[TimeSlot]

    async def update_calendar_event(event_id, **kwargs) -> Dict
    async def delete_calendar_event(event_id) -> bool
    async def get_available_slots(
        organizer_email, attendees, duration, start, end
    ) -> List[TimeSlot]
```

OAuth strategy: **Service Account** (Google Workspace — recomendado para B2B) com fallback para **OAuth2 per-user**. Credenciais armazenadas criptografadas por `company_id`.

**Tarefa 6.2 — Configuração e variáveis de ambiente** (½ dia)

Adicionar em `app/core/config.py`:
```python
# Google Calendar (já tem GOOGLE_APPLICATION_CREDENTIALS — completar)
GOOGLE_CALENDAR_CLIENT_ID: Optional[str] = None
GOOGLE_CALENDAR_CLIENT_SECRET: Optional[str] = None
GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON: Optional[str] = None  # JSON criptografado
GOOGLE_CALENDAR_DEFAULT_TIMEZONE: str = "America/Sao_Paulo"
ENABLE_GOOGLE_CALENDAR: bool = False  # Feature flag OFF por padrão
```

Adicionar em `requirements.txt`:
```
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-httplib2>=0.1.1
```

**Tarefa 6.3 — Suporte dual-provider no `CalendarService`** (1 dia)

Arquivo: `app/domains/interview_scheduling/services/calendar_service.py`

Refatorar para selecionar o cliente com base na configuração da empresa:
```python
class CalendarService:
    async def _get_client(self, company_id: str):
        policy = await get_company_calendar_policy(company_id)
        if policy.calendar_provider == "google" and settings.ENABLE_GOOGLE_CALENDAR:
            return GoogleCalendarClient()
        return graph_client  # Microsoft Graph (default)
```

O campo `Interview.meeting_platform` guia qual tipo de link gerar (teams vs. meet).

**Tarefa 6.4 — Novos endpoints Google** (1 dia)

Adicionar em `app/api/v1/calendar.py`, espelhando os endpoints Microsoft existentes:
```
GET  /calendar/google/health
POST /calendar/google/availability
POST /calendar/google/find-meeting-times
POST /calendar/google/schedule-interview
POST /calendar/google/cancel-interview
POST /calendar/google/reschedule-interview
```

**Tarefa 6.5 — Migration: campos Google no model Interview** (½ dia)

Adicionar em `app/models/interview.py`:
```python
# Google Calendar integration (espelho dos campos graph_*)
google_event_id = Column(String(255), nullable=True, index=True)
google_meet_link = Column(String(500), nullable=True)
google_calendar_id = Column(String(255), nullable=True)
google_organizer_email = Column(String(255), nullable=True)
```
Alembic migration.

**Tarefa 6.6 — UI de configuração** (1 dia)

Em Configurações → Integrações: card "Google Calendar":
- Toggle ativar/desativar (`ENABLE_GOOGLE_CALENDAR`)
- Botão "Conectar com Google" (OAuth2 flow ou upload Service Account JSON)
- Status de conexão (conectado / desconectado / erro)
- Campo de timezone padrão

**Riscos:**
- OAuth Google varia por tipo de conta (Workspace vs. Gmail pessoal) — implementar Service Account primeiro
- Empresa pode ter tanto Microsoft quanto Google — suporte a ambos simultaneamente é complexidade extra (deixar para V2)

**Status:** 🔲 Planejado — Sprint dedicado

---

### Resumo do Sprint N

| Tarefa | Tipo | Esforço | Dependências |
|--------|------|---------|--------------|
| N-T1 — LIA descreve comunicação no chat | Backend (prompt) | ½ dia | Nenhuma |
| N-T2 — Badge status vaga interativo | Frontend | ½ dia | Nenhuma |
| N-T3 — Badge screening status interativo | Frontend | ½ dia | Nenhuma |
| N-T4 — Conectar CloseVacancyModal | Frontend | ½ dia | N-T2 |
| N-T5 — JobStatusModal no Kanban | Frontend | ½ dia | N-T2 |
| N-T6 — Google Calendar | Full-stack | 5-7 dias | ⏸️ Adiado — alinhamento time |
| **Total T1-T5** | | **~2,5 dias** | |

---

## Sprint 1-2 — Fundação e Compliance

> Detalhamento baseado em exploração de código realizada em 2026-02-28.
> **Nota:** Vários itens desta sprint têm infraestrutura existente — o trabalho é fechar gaps, não construir do zero.

---

### L3 — Human Review Gate (Rejeição Automatizada)

**Situação atual:** `candidate_tools.py` tem `requires_confirmation: True` no tool `reject_candidate`. Porém, a flag pode ser ignorada dependendo de como o agente é chamado — não há enforcement centralizado que impeça rejeição automatizada sem aprovação humana explícita.

**Arquivo principal:** `lia-agent-system/app/domains/cv_screening/tools/candidate_tools.py:280-357`

**Gap identificado:** O flag `requires_confirmation` é uma recomendação para o agente, não uma barreira técnica. Um agente mal configurado ou uma chamada direta à API pode rejeitar candidatos sem confirmação.

**O que fazer:**
1. Criar middleware/guard na camada de API (`candidates.py`) que bloqueie `PATCH /candidates/{id}/status` para `Reprovado` sem campo `human_reviewer_id` preenchido
2. Adicionar coluna `rejected_by_human` (boolean) + `human_reviewer_id` (FK users) na tabela `candidates`
3. Migration Alembic
4. Garantir que o frontend exija confirmação antes de enviar a requisição de rejeição

**Risco:** Médio — requer migration e mudança de contrato de API. Testar que rejeições manuais pelo recrutador continuam funcionando normalmente.

---

### L4 — Job de Deleção de Dados (LGPD Scheduler)

**Situação atual:** `lgpd_compliance.py` tem endpoints para DPO, breach notifications e decisões automatizadas. Soft delete implementado em `bulk_actions.py`. Falta: job agendado que execute deleção física após período de retenção.

**Arquivos:** `lia-agent-system/app/api/v1/lgpd_compliance.py`, `app/api/v1/bulk_actions.py`

**Gap identificado:** Não há Celery task agendada para deletar fisicamente dados após 30/90/180 dias conforme a política de retenção. Dados de candidatos rejeitados continuam no banco indefinidamente.

**O que fazer:**
1. Criar `app/tasks/lgpd_cleanup_task.py` como Celery periodic task
2. Definir política de retenção por tipo de dado: candidatos rejeitados (90 dias), CVs (180 dias), logs de triagem (1 ano)
3. Task deve respeitar `company_id` e logar cada deleção em `audit_logs`
4. Adicionar coluna `scheduled_deletion_at` na tabela `candidates`
5. Endpoint `POST /lgpd/schedule-deletion` para acionar manualmente (Data Subject Request)

**Risco:** Alto — operação destrutiva e irreversível. Implementar com dry-run mode primeiro.

---

### A3 — Persistência de Estado LangGraph via Checkpoints

**Situação atual:** Estado do wizard persiste via `AgentWorkingMemory` (SQLAlchemy model). Porém, sem checkpoints nativos do LangGraph: se o processo falhar no meio de uma execução, o grafo recomeça do zero na próxima interação — o recrutador perde o progresso da vaga em criação.

**Arquivo principal:** `lia-agent-system/app/shared/agents/state_machine.py`

**Gap identificado:** `JobWizardState` é um `TypedDict` em memória. Ao reiniciar o processo ou em caso de exceção no nó, o estado é perdido.

**O que fazer:**
1. Implementar `PostgresSaver` do LangGraph como checkpointer
2. Configurar o grafo com `checkpointer=PostgresSaver(conn)` no `job_wizard_graph.py`
3. Usar `thread_id = session_id` para identificar conversas únicas
4. Garantir que `AgentWorkingMemory` e o novo checkpointer não entrem em conflito
5. Migration para tabela `langgraph_checkpoints` (nativa do LangGraph)

**Risco:** Médio — mudança na inicialização do grafo. Testar com conversas longas e interrupções forçadas.

---

### A4 — Verificar Gap de Notas de Entrevista

**Situação atual:** Modelos `Interview` e `InterviewFeedback` existem com campos completos (`interviewer_notes`, `technical_skills_rating`, `recommendation`, etc.). A API `interview_notes.py` existe.

**Gap a investigar:** Confirmar se o frontend usa a API de notas ou ainda tem lógica local/state-only. Verificar se as notas preenchidas no modal de entrevista são efetivamente salvas no banco ou perdidas ao fechar o modal.

**O que fazer:**
1. Auditar `plataforma-lia/src` — buscar onde são enviadas notas de entrevista
2. Se há divergência frontend→backend, conectar o componente à API `/interview-notes`
3. Garantir que `InterviewFeedback` seja criado ao concluir uma entrevista (estágio "Entrevista → Aprovado/Reprovado")

**Risco:** Baixo — infraestrutura existe, provável gap de integração frontend.

---

### M1 — Enforcing de Limites por Plano

**Situação atual:** `billing_service.py` implementado com Iugu e Vindi (não Stripe — a auditoria original mencionou Stripe mas a implementação real usa provedores brasileiros). Modelos `Subscription`, `Invoice`, `PaymentMethod` existem.

**Gap identificado:** Os limites de plano (vagas ativas, usuários, candidatos por vaga) não são enforced em tempo real. Uma empresa em plano básico pode criar vagas ilimitadas sem bloqueio.

**O que fazer:**
1. Criar `PlanLimitsMiddleware` ou dependency FastAPI que verifica limites antes de criar vaga/usuário
2. Definir limites por tier em `app/core/config.py` ou tabela `plan_configs`
3. Retornar HTTP 402 com mensagem clara quando limite atingido
4. Frontend: tratar 402 mostrando modal de upgrade

**Risco:** Médio — impacta criação de vagas e usuários. Definir limites com margem generosa para não bloquear clientes existentes.

---

### M2 — Trial com Expiração Real

**Situação atual:** Modelo de billing tem campos de período e datas. Trial não expira automaticamente — empresas em trial continuam com acesso integral indefinidamente.

**Gap identificado:** Não há job nem middleware que bloqueie acesso após `trial_ends_at`.

**O que fazer:**
1. Adicionar coluna `trial_ends_at` na tabela `companies` (se não existir)
2. Criar Celery task diária que verifica trials expirados e altera status para `trial_expired`
3. Middleware de autenticação verificar status da empresa — retornar 402 se `trial_expired`
4. Frontend: rota de upgrade/bloqueio amigável

**Risco:** Baixo — não afeta clientes pagantes. Comunicar clientes em trial antes de ativar.

---

## Sprint 3-5 — Qualidade e Produto

---

### B3 — FairnessGuard: Verificar Outputs do LLM

**Status:** ✅ Implementado 2026-02-28

**Situação anterior:** `fairness_guard.py` verificava apenas **inputs** — filtros e queries enviados pelo recrutador antes de processar. Outputs do LLM (pareceres, avaliações) chegavam ao usuário sem filtro de viés.

**O que foi implementado:**

`fairness_guard.check()` adicionado nos **3 endpoints críticos** que retornam avaliações textuais sobre candidatos:

| Endpoint | Texto verificado | Ação se bloqueado |
|----------|-----------------|-------------------|
| `POST /interview-notes/generate-parecer` | `parecer` (ambos os caminhos de retorno) | Substitui texto + popula `fairness_warnings` na response |
| `POST /rubric_evaluation/evaluate` | `evaluation_result.reasoning` | `model_copy(update={"reasoning": "..."})` antes de salvar no BD |
| `POST /rubric_evaluation/batch-evaluate` | `eval_result.reasoning` por candidato no loop | Idem, antes de salvar cada registro |

**Campo novo no schema:** `GenerateParecerResponse.fairness_warnings: List[str]` — retorna alertas soft (linguagem potencialmente enviesada mas não bloqueante) ao frontend para display ao recrutador.

**Escopo explicitamente fora do B3:**
- `POST /interview-notes/generate-questions` — gera perguntas técnicas estruturadas (skill-based), não avaliações sobre o candidato
- `GET /wsi_endpoints` — gera itens de assessment (questões de teste), não avaliações textuais
- `lia_assistant` (chat) — respostas de chat ao recrutador, FairnessGuard já opera nos inputs

**Pendência futura (B3-extended):** Aplicar em outputs dos agentes ReAct (`pipeline_agent`, `cv_screening_agent`) quando esses agentes gerarem texto exibido diretamente ao usuário. Requer análise caso a caso por agente.

---

### B4 — Auditoria de System Prompts para Viés

**Situação atual:** Prompts centralizados em `app/shared/agents/nodes.py` (`MASTER_ORCHESTRATOR_PROMPT`) e `app/agents/prompts/agent_prompts.py`. Não há auditoria de linguagem tendenciosa nesses textos.

**Gap identificado:** System prompts podem conter viés implícito (ex: linguagem que favorece certos perfis, instruções que replicam preconceitos históricos de recrutamento).

**O que fazer:**
1. Listar todos os system prompts: `nodes.py`, `agent_prompts.py`, prompts dos 7 domínios ReAct
2. Revisar manualmente em busca de: linguagem de gênero, referências a experiências de universidades/empresas específicas, critérios implícitos de "fit cultural" tendencioso
3. Documentar revisão como evidência de compliance EU AI Act
4. Criar checklist de revisão para novos prompts adicionados no futuro

**Risco:** Baixo — tarefa de revisão/documentação, não mudança de código.

---

### F1 — Substituir Mock Data no Kanban

**Situação atual:** `src/components/kanban/mock/data-generators.ts` e `candidates.ts` com dados gerados aleatoriamente. Usado em desenvolvimento/demo mas pode vazar para produção.

**Gap identificado:** Kanban pode exibir dados fictícios se a API falhar ou se o ambiente não estiver configurado corretamente.

**O que fazer:**
1. Remover arquivos `mock/` do bundle de produção (ou garantir que são apenas importados em dev)
2. Conectar `KanbanBoard` à API real: `GET /api/v1/jobs/{id}/candidates`
3. Implementar estados de loading/error/empty adequados no Kanban
4. Garantir que dados mock só sejam usados em testes (Jest/Playwright)

**Risco:** Médio — mudança no componente mais crítico do produto. Testar amplamente com dados reais antes de deploiar.

> **Reavaliação 2026-02-28:** Problema superestimado na auditoria original. Exploração do código revelou que `mockCandidates` é código morto — importado em `job-kanban-page.tsx` (linha 121) mas **nunca referenciado** no restante do arquivo. Candidatos já são carregados da API real via `liaApi.listCandidates()`. Se a API falha, a lista fica vazia (sem fallback para mock). Ação necessária: remover a importação morta (1 linha). Não é um gap de produto.

---

### F2 — Charts e Gráficos com Dados Reais

**Situação atual:** `interactive-charts.tsx:43` usa `generateTimeSeriesData()` — função que gera valores aleatórios para preencher gráficos de tendência, funil, etc.

**Gap identificado:** Todos os gráficos do Painel de Controle mostram dados fictícios.

**O que fazer:**
1. Criar endpoints de analytics no backend: `GET /api/v1/analytics/pipeline-funnel`, `GET /api/v1/analytics/hiring-trend`, etc.
2. Conectar `interactive-charts.tsx` à API, usando `generateTimeSeriesData()` apenas como fallback/loading skeleton
3. Adicionar cache Redis nos endpoints de analytics (dados mudam pouco, custo de query alto)

**Risco:** Médio — requer criação de endpoints novos + queries de agregação no banco.

> **Reavaliação 2026-02-28:** As páginas que usam `generateTimeSeriesData()` (`executive-dashboard-page`, `advanced-interactive-charts`, `lia-metrics-dashboard`) são **componentes arquivados** — nenhum `page.tsx` do App Router os renderiza, e o sidebar do MVP tem apenas 3 itens (Painel de Controle, Vagas, Funil de Talentos). Esses charts não estão visíveis para o usuário final. Tratar quando Analytics / Dashboards entrarem no roadmap do MVP.

---

### F3 — KPIs do Painel de Controle com Dados Reais

**Situação atual:** Cards de KPI (vagas abertas, candidatos triados, tempo médio de contratação, etc.) usam valores estáticos ou mock.

**O que fazer:**
1. Criar `GET /api/v1/dashboard/kpis?company_id=...` que agrega métricas reais
2. Conectar componentes de KPI no frontend a este endpoint
3. Implementar cache de 5 minutos no Redis para não sobrecarregar o banco

**Risco:** Baixo — endpoint de leitura, sem efeitos colaterais.

> **Reavaliação 2026-02-28:** Telas com KPIs hardcoded (`executive-dashboard-page` com dados de jan/2024, `indicators-page` com 4 recrutadores fictícios, etc.) são componentes órfãos — existem em `src/components/pages/` mas o `dashboard-app.tsx` não os renderiza no MVP atual. O único Painel de Controle acessível é `TasksPageMVP`, que usa dados reais da API (`/api/backend-proxy/interviews/`). A área `/admin/*` está separada e não é prioridade. Tratar quando essas telas entrarem formalmente no roadmap.

---

### M4 — Dashboard de Custos de IA (AI Credits)

**Situação atual:** `ai_consumption.py` rastreia cada chamada LLM com `company_id`, `model`, `input_tokens`, `output_tokens`, `cost_cents`. `AiCreditsBalance` tem `monthly_limit` e `current_usage`. Frontend não exibe esses dados.

**O que fazer:**
1. Criar `GET /api/v1/ai-credits/dashboard` que retorna: consumo do período, custo por agente/operação, % do limite usado, histórico mensal
2. Construir componente frontend no Painel de Controle (seção Configurações) com gráfico de consumo e alertas
3. Enviar email/notificação quando consumo atingir 80% do limite mensal

**Risco:** Baixo — leitura de dados já existentes, novo endpoint + componente de UI.

---

### M5 — Alertas de Consumo de IA

**Situação atual:** `AiCreditsBalance.monthly_limit` existe mas não há lógica que dispare alerta quando consumo se aproxima do limite.

**O que fazer:**
1. No `token_tracking_service.py`, após registrar consumo, verificar se `current_usage / monthly_limit >= 0.8`
2. Se sim, disparar notificação in-app + email para admin da empresa
3. Ao atingir 100%, bloquear chamadas LLM (ou permitir overage se `overage_allowed=True`)

**Risco:** Baixo — adicionar lógica em serviço existente.

---

### N1 — Completar Integração Google Calendar

**Situação atual:** Microsoft Graph + Outlook Calendar totalmente integrados (`calendar_service.py`). Google Calendar listado como suportado mas implementação parcial — meeting platform "google_meet" e "google_calendar" aparecem nas configs mas podem não ter fluxo completo.

**O que fazer:**
1. Auditar `calendar_service.py` — mapear quais métodos têm implementação Microsoft e quais têm Google
2. Implementar métodos faltantes do Google Calendar usando Google Calendar API (OAuth2)
3. Adicionar `GOOGLE_CALENDAR_CLIENT_ID` e `GOOGLE_CALENDAR_CLIENT_SECRET` nas variáveis de ambiente
4. Testar fluxo completo: criar evento → convidar candidato → sincronizar cancelamento/reagendamento

**Risco:** Médio — nova integração OAuth2. Testar com conta Google real antes de liberar.

---

## Longo Prazo — Evolução Estratégica

---

### L2 — Criptografia de Chaves ATS em Repouso

**Problema:** Chaves de integração dos ATSs (Gupy, Pandapé) armazenadas em banco sem criptografia em repouso. Se o banco for comprometido, as chaves ficam expostas.

**O que fazer:**
1. Implementar criptografia AES-256 para campos de API keys usando `cryptography` (Fernet)
2. Chave mestra em variável de ambiente (`ATS_ENCRYPTION_KEY`)
3. Migration para re-criptografar chaves existentes
4. Helper `encrypt_field()` / `decrypt_field()` em `app/utils/crypto.py`

---

### L5 — Consentimento Granular por Finalidade

**Problema:** Consentimento atual é binário (aceita/recusa termos). LGPD e EU AI Act exigem consentimento por finalidade específica: triagem automática, análise de vídeo, comparação com banco de talentos, etc.

**O que fazer:**
1. Tabela `candidate_consents` com `purpose` (enum), `granted_at`, `revoked_at`, `ip_address`
2. Check de consentimento antes de cada operação de IA que processa PII
3. Interface de gerenciamento de consentimento para o candidato (portal de privacidade)

---

### A5 — Circuit Breaker para Integrações Externas

**Problema:** Calls para Pearch AI, Deepgram, OpenMic.ai sem circuit breaker. Se um serviço externo ficar lento ou indisponível, as requisições acumulam e degradam toda a plataforma.

**O que fazer:**
1. Implementar circuit breaker com `pybreaker` ou `tenacity` para cada integração externa
2. Estados: CLOSED (normal) → OPEN (falhas acima do threshold) → HALF-OPEN (teste de recuperação)
3. Fallback por integração: Pearch (retornar lista vazia), Deepgram (marcar transcrição como pendente)

---

### B5 — Testes de Disparate Impact nos Scores WSI

**Problema:** Sem evidência de que os scores WSI não produzem disparate impact por grupo protegido (gênero, raça, origem). Risco legal crescente com EU AI Act High-Risk AI Systems.

**O que fazer:**
1. Construir dataset sintético de CVs balanceados por grupo
2. Executar pipeline de triagem e calcular 4/5ths rule (80% rule) para cada grupo
3. Se disparate impact detectado → investigar qual bloco WSI causa o viés
4. Relatório de auditoria anual de fairness

---

### T1-T4 — Cobertura de Testes

**Situação atual:** Testes existem em `app/tests/` mas cobertura é baixa para os serviços mais críticos.

**Prioridade:**
1. **T1** `rubric_evaluation_service` — unit tests para cada bloco WSI, casos com PII removida
2. **T2** Pipeline de triagem end-to-end — integration test com banco real (TestContainers)
3. **T3** Fluxo de criação de vaga — E2E com Playwright simulando conversa com LIA
4. **T4** Load testing — k6 ou Locust nos endpoints `/wizard/chat` e `/pipeline/transition`

---

### M7 — Modelo RPO (Pagamento por Contratação)

**Problema:** Plataforma cobra subscription mensal. Clientes RPO preferem pagar por contratação realizada.

**O que fazer:**
1. Novo tipo de plano `rpo` no billing com `cost_per_hire_cents`
2. Evento `candidate.hired` dispara cobrança via webhook Iugu/Vindi
3. Dashboard RPO: contratações do mês, receita gerada por cliente

---

### M8 — BYOK (Bring Your Own Key)

**Problema:** Todos os clientes usam a mesma chave Anthropic da WeDOTalent. Grandes clientes (bancos, saúde) exigem dados que não passem pela infraestrutura de IA da plataforma.

**O que fazer:**
1. Campo `anthropic_api_key` criptografado na tabela `companies`
2. `LLMProviderFactory` verifica se empresa tem chave própria antes de usar a chave global
3. UI de configuração em Configurações → Integrações de IA

---

## Log de Implementações

| Data | ID | Descrição resumida | Arquivo(s) alterado(s) |
|------|----|--------------------|------------------------|
| 2026-02-28 | L1 | LangSmith desligado por padrão | `app/core/config.py` |
| 2026-02-28 | L8 | Token WhatsApp sem fallback hardcoded | `app/domains/communication/services/whatsapp_meta_service.py` |
| 2026-02-28 | B2 | GEOGRAPHIC_ADJUSTMENTS removido | `app/domains/cv_screening/services/calibration_profiles.py` |
| 2026-02-28 | B1 | Nome do candidato removido do payload LLM | `app/domains/cv_screening/services/rubric_evaluation_service.py` |
| 2026-02-28 | A1 | asyncio.timeout(120) no Job Wizard loop | `app/domains/job_management/agents/job_wizard_graph.py` |
| 2026-02-28 | A2 | Retry + logging para Gemini resposta vazia | `app/shared/providers/llm_gemini.py` |
| 2026-02-28 | N-T1 | `COMMUNICATION_TRANSPARENCY_RULES` adicionado ao PipelineTransitionAgent — LIA descreve dispatch para candidato antes de confirmar, com 2 novos few-shot examples (triagem e rejeição em lote) | `app/domains/pipeline/agents/pipeline_system_prompt.py` |
| 2026-02-28 | N-T2 | Badge "Status da Vaga" → Popover interativo com Pausar/Fechar/Reativar no header do Kanban | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 2026-02-28 | N-T3 | Badge "Screening Status" → Popover interativo com Iniciar/Pausar/Retomar/Configurar por estado da triagem | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 2026-02-28 | N-T4 | `CloseVacancyModal` integrado ao Kanban — candidatos hired/others derivados do `candidatesData` | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 2026-02-28 | N-T5 | `JobStatusModal` integrado ao Kanban individual — acesso via badge do header (antes só na listagem de vagas) | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 2026-02-28 | L3 | Human Review Gate: guard 422 em `PATCH /candidates/{id}/stage` para stages de rejeição sem `user_id`; `rejected_by_human` + `human_reviewer_id` adicionados a `VacancyCandidate`; migration `010_add_human_review_gate.py` | `app/api/v1/candidates.py`, `app/models/candidate.py`, `alembic/versions/010_add_human_review_gate.py` |
| 2026-02-28 | N2 | `CommunicationMatrixEntry` integrada ao `TransitionDispatchService`: `ACTION_BEHAVIOR_TRIGGER_MAP` (action_behavior→trigger_name), `_get_matrix_entry()` com fallback company→platform, multi-channel dispatch via `effective_channels`, respeita `is_active`; `requires_approval` logado (enforcement em L3) | `app/domains/communication/services/transition_dispatch_service.py` |
| 2026-02-28 | A4 | Notas de entrevista persistidas em banco: modelo `InterviewNote` (SQLAlchemy), migration `011_add_interview_notes_table.py`, `interview_notes_service.py` (CRUD), endpoint atualizado (mock dict removido), 3 proxy routes FE adicionadas; response_model tipados com `InterviewNoteResponse`, `InterviewNoteSummary`, `InterviewNoteUpdateResponse` | `app/models/interview.py`, `alembic/versions/011_*`, `app/services/interview_notes_service.py`, `app/api/v1/interview_notes.py`, `plataforma-lia/src/app/api/backend-proxy/interview-notes/*` |
| 2026-02-28 | A3 | Checkpoints de estado do JobWizardGraph persistidos em banco: modelo `AgentCheckpoint` (upsert por session_id+agent_type), migration `012_add_agent_checkpoints_table.py`, `checkpoint_service.py` (save/restore/delete), `job_wizard_graph.py` integrado — restaura estado no início, salva no fim, limpa ao completar | `app/models/agent_checkpoint.py`, `alembic/versions/012_*`, `app/services/checkpoint_service.py`, `app/domains/job_management/agents/job_wizard_graph.py` |
| 2026-02-28 | L4 | LGPD cleanup scheduler implementado: migration `013_add_scheduled_deletion_at.py` (campo em candidates + vacancy_candidates), `lgpd_cleanup_service.py` (dry_run mode, deleção física, audit log), 3 novos endpoints (`POST /schedule-deletion`, `POST /run-cleanup` com auth admin, `GET /pending-deletions`), jobs diários no `AutomationScheduler` (01h e 02h) | `alembic/versions/013_*`, `app/services/lgpd_cleanup_service.py`, `app/api/v1/lgpd_compliance.py`, `app/domains/automation/services/automation_scheduler.py` |
| 2026-02-28 | M2 | Trial expiration enforcement: `trial_enforcement.py` (FastAPI dependency `require_active_subscription` — bloqueia 402 se trial expirado/suspended/cancelled), página `/upgrade` no FE (3 planos: Starter/Pro/Enterprise), `handle-payment-required.ts` (redirect automático para /upgrade em 402) | `app/middleware/trial_enforcement.py`, `plataforma-lia/src/app/upgrade/page.tsx`, `plataforma-lia/src/lib/api/handle-payment-required.ts` |
| 2026-02-28 | M1 | Plan limits enforcing: configurações de plano em `config.py` (Starter/Pro/Enterprise/Trial × vagas/usuários/candidatos), `plan_limits_service.py` (`check_active_jobs_limit` dependency — HTTP 402 ao atingir limite), dependências aplicadas em `POST /jobs` junto com `require_active_subscription`; FE: `checkPaymentRequired()` em `createJobVacancy()` | `app/core/config.py`, `app/services/plan_limits_service.py`, `app/api/v1/job_vacancies.py`, `plataforma-lia/src/services/lia-api.ts` |
| 2026-02-28 | BUG-L4 | Correção pós-auditoria: `scheduled_deletion_at` adicionado aos modelos `Candidate` (linha 251) e `VacancyCandidate` (linha 381) — migration 013 criava a coluna no BD mas o ORM não mapeava o campo, causando AttributeError na execução do cleanup service | `app/models/candidate.py` |
| 2026-02-28 | B3 | FairnessGuard em outputs do LLM: `fairness_guard.check()` adicionado em **3 endpoints**: (1) `POST /interview-notes/generate-parecer` — ambos os caminhos de retorno (JSON parsed e fallback); (2) `POST /rubric_evaluation/evaluate` — antes de persistir e retornar; (3) `POST /rubric_evaluation/batch-evaluate` — dentro do loop por candidato, antes de persistir. Se conteúdo bloqueado: substituído por mensagem de revisão + `logger.warning` com `candidate_id`, `category` e `blocked_terms`. `GenerateParecerResponse` ganhou campo `fairness_warnings: List[str]` para retornar alertas soft ao frontend. Outros endpoints LLM (`generate-questions`, `wsi_endpoints`, `lia_assistant`) não foram cobertos: geram perguntas estruturadas ou respostas de chat ao recrutador, não avaliações textuais sobre candidatos — fora do escopo do B3. | `app/api/v1/interview_notes.py`, `app/api/v1/rubric_evaluation.py` |
| 2026-02-28 | L2-VERIFICADO | Criptografia ATS já estava implementada: `app/shared/encryption.py` usa Fernet (symmetric), chamado em `app/api/v1/ats.py` ao salvar `api_key` e `api_secret`. Documento estava desatualizado. Item marcado como ✅. | `app/shared/encryption.py`, `app/api/v1/ats.py` |
| 2026-02-28 | L7 | PII masking ativado globalmente: `install_global_pii_masking()` adicionado em `app/main.py` logo após `configure_logging()`. `PIIMaskingFilter` (já existia em `app/shared/pii_masking.py`) agora está instalado no root logger — mascara CPF (`***CPF***`), e-mail (`***EMAIL***`), telefone (`***PHONE***`) e nomes em contexto (`***NAME***`) em todos os logs da aplicação. | `app/main.py` |
| 2026-02-28 | B5 | Testes de disparate impact WSI: `tests/test_disparate_impact_wsi.py` criado com 12 testes cobrindo neutralidade por gênero, idade, etnia e 4/5 Rule (Adverse Impact Ratio). Verifica que scores WSI são invariantes a sinais demográficos e que diferenças de score refletem apenas competência técnica. | `tests/test_disparate_impact_wsi.py` |
| 2026-02-28 | T1 | Testes unitários para rubric_evaluation_service: `tests/test_rubric_evaluation_service.py` criado com 18 testes cobrindo fórmula BARS (EXCEEDS/MEETS/PARTIAL/MISSING × multipliers ESSENTIAL/IMPORTANT/NICE_TO_HAVE), cache (hit/miss/expirado/thread-safety), variation logging, batch evaluation e formato legado. LLM mockado via `unittest.mock`. | `tests/test_rubric_evaluation_service.py` |
| 2026-02-28 | T2 | Testes de integração para pipeline de triagem: `tests/test_screening_pipeline_integration.py` criado com 15 testes cobrindo construção do pipeline (4 blocos), distribuição de perguntas (compact/full model), calibração por senioridade, frameworks pedagógicos (Bloom/Dreyfus/Big Five/CBI), deduplicação de perguntas e contract do schema de resposta. | `tests/test_screening_pipeline_integration.py` |
| 2026-02-28 | N-T6-ADIADO | Google Calendar adiado: análise revelou que a feature depende de decisão de produto (seleção de provider por tenant), tela de Configurações de Integrações (não existe), e autenticação Google Workspace (Service Account + Domain-Wide Delegation). Retomar quando houver demanda de clientes ou quando tela de Configurações estiver planejada. | `docs/analises/AUDITORIA_TECNICA_EXECUCAO.md` |
| 2026-02-28 | BUG-T2 | Correção pós-implementação dos testes T2: (1) `make_company_question` usava chave `"text"` mas `_build_company_block` lê `q.get("question_text")` → corrigido para `"question_text"`; (2) mocks apontavam para métodos **públicos** (`generate_technical_questions`, `generate_behavioral_questions`) mas o pipeline chama os **privados** (`_generate_technical_questions`, `_generate_behavioral_questions`, `_generate_cultural_questions`) → corrigido; (3) `_build_eligibility_block` usa templates internos hardcoded — não usa o gerador — o mock de eligibility foi removido; (4) atributo `question=` nos MagicMock mudado para `text=` (campo correto do `UnifiedScreeningQuestion`); (5) adicionados `id=` e `category=` nos objetos mock. Sem esses ajustes, `test_behavioral_competencies_propagated` falharia (block 5 sempre vazio). | `tests/test_screening_pipeline_integration.py` |
| 2026-02-28 | A5 | Circuit breaker aplicado em Pearch, Deepgram e OpenMic: decorator `@circuit_breaker()` de `app/shared/resilience/circuit_breaker.py` aplicado em `pearch_service.search_candidates()` (threshold=3, timeout=15s), `deepgram_service.transcribe_audio_url()` (threshold=3, timeout=30s), `openmic_service.create_screening_agent()` e `start_screening_call()` (threshold=5, timeout=60s). Fallbacks retornam respostas estruturadas com `circuit_open: True` / `error_type: "circuit_open"`. | `app/domains/sourcing/services/pearch_service.py`, `app/domains/interview_scheduling/services/deepgram_service.py`, `app/services/openmic_service.py` |
| 2026-02-28 | M5 | Alertas de consumo de IA a 80% e 100%: `token_tracking_service.py` estendido com `_check_and_alert_thresholds()` — após cada `record_usage()`, verifica `AiCreditsBalance.usage_percentage` contra `ALERT_THRESHOLDS = [80, 100]`. Dedup via Redis `SET ai_alert:{company_id}:{threshold} EX 86400 NX` (1 alerta/dia por threshold). Notificação via `NotificationService.create_notification()` para admin da empresa com canal EMAIL + BELL. | `app/services/token_tracking_service.py` |
| 2026-02-28 | B4 | Auditoria e padronização de system prompts: bloco `=== FAIRNESS_AND_COMPLIANCE ===` adicionado a 3 prompts sem cobertura prévia — wizard (proíbe faixa etária/gênero/aparência/estado civil com citações Lei 10.741/2003 e CF Art. 7°XXX), sourcing (proíbe universidade específica como filtro eliminatório, alerta shortlists homogêneos) e jobs_mgmt (análise de portfólio por métricas objetivas, sem viés de stack/empresa). Documento de auditoria completo criado em `docs/compliance/`. | `app/domains/job_management/agents/wizard_system_prompt.py`, `app/domains/sourcing/agents/sourcing_system_prompt.py`, `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py`, `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_2026_02.md` (novo) |
| 2026-02-28 | M4 | Dashboard de custos de IA (frontend): página `/configuracoes/ai-credits` criada com 4 cards (tokens usados/restantes/custo estimado/operações), barra de progresso com codificação de cor (gray/amber/red), gráfico de barras Recharts de consumo diário dos últimos 30 dias, tabela de breakdown por agente ordenada por consumo. Hook `useAiCredits()` e `useAiConsumptionHistory()` com proxy route para 4 endpoints de AI consumption. Visível apenas para admins. | `plataforma-lia/src/app/api/backend-proxy/ai-credits/route.ts` (novo), `plataforma-lia/src/hooks/use-ai-credits.ts` (novo), `plataforma-lia/src/components/pages/ai-credits-page.tsx` (novo), `plataforma-lia/src/app/configuracoes/ai-credits/page.tsx` (novo) |
| 2026-02-28 | L5 | Consentimento granular por finalidade (soft enforcement): `consent_checker_service.py` criado com `check_candidate_consent(candidate_id, company_id, purpose)` — se revogado: bloqueia HTTP 451; se ausente: warning + audit log + continua (soft); se presente: permite. Verificação integrada em `rubric_evaluation.py` antes de `evaluate_candidate()`. 5 novos endpoints em `candidates.py`: GET/POST/DELETE consents e GET/PUT communication-preferences. | `app/services/consent_checker_service.py` (novo), `app/api/v1/rubric_evaluation.py`, `app/api/v1/candidates.py` |
| 2026-02-28 | N3 | Preferências de canal por candidato end-to-end: campos `preferred_channels: JSON` (lista ordenada, default `["email"]`) e `channel_opt_out: JSON` (default `[]`) adicionados ao modelo `Candidate`. Migration `014_candidate_channel_preferences.py` com colunas JSONB + índices GIN. `CandidateChannelSelector` (novo serviço) filtra canais por: intersecção com preferências do candidato, remoção de opt-outs, verificação de `LGPDConsent` para marketing. `TransitionDispatchService` integrado — aplica seleção de canal antes de cada dispatch. | `app/models/candidate.py`, `alembic/versions/014_candidate_channel_preferences.py` (novo), `app/services/candidate_channel_selector.py` (novo), `app/domains/communication/services/transition_dispatch_service.py` |
| 2026-02-28 | T3 | Testes E2E Playwright para criação de vaga via LIA: 5 cenários cobrindo fluxo completo (login→wizard→publicar), campos obrigatórios faltando (LIA pede esclarecimento), vaga afirmativa PCD (LIA ativa campos de diversidade), cancelamento sem persistência de estado e re-entrada com retomada de checkpoint (A3). Fixture `wizard-conversation.fixture.ts` com helpers `sendWizardMessage`, `fillWizardStep`, `assertWizardProgress`, `waitForJobPublished`, `openJobWizard`. | `plataforma-lia/e2e/fixtures/wizard-conversation.fixture.ts` (novo), `plataforma-lia/e2e/tests/wizard/test_job_creation_lia.spec.ts` (novo) |
| 2026-02-28 | T4 | Testes de carga com Locust: 3 user classes — `WizardUser` (POST /wizard/chat peso 3 + GET /wizard/state peso 1, wait 2-5s), `PipelineUser` (POST /pipeline/transition peso 4 + GET /jobs/{id}/candidates peso 2, wait 1-3s), `HealthCheckUser` (weight=1). Hook `on_quitting` imprime relatório de conformidade p50/p95/p99 vs targets (500ms/2s/5s). `load_test_config.py` centraliza headers, IDs de teste e geradores de payload realistas. | `tests/load/locustfile.py` (novo), `tests/load/load_test_config.py` (novo), `tests/load/README.md` (novo) |
| 2026-02-28 | A5-FIX | Verificação pós-sprint revelou que tenacity retry estava ausente (apenas circuit breaker havia sido aplicado). Corrigido: `from tenacity import retry, stop_after_attempt, wait_exponential` adicionado nos 3 serviços; `@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))` aplicado entre `@circuit_breaker` e `async def` nos 5 métodos alvo. Ordem: circuit_breaker (outer) → retry (inner) — circuit abre após falha final do retry. | `app/domains/sourcing/services/pearch_service.py`, `app/domains/interview_scheduling/services/deepgram_service.py`, `app/services/openmic_service.py` |
| 2026-02-28 | L5-FIX | Verificação pós-sprint revelou que `consent_warnings` não estava sendo propagado no response. Corrigido: (1) campo `consent_warnings: List[str]` adicionado ao schema `RubricEvaluationResult`; (2) em `rubric_evaluation.py`, caso `soft_warning=True`, captura warning antes do serviço ser chamado; (3) após retorno do serviço, `model_copy(update={"consent_warnings": [...]})` propaga o aviso ao resultado — comportamento idêntico ao FairnessGuard já existente. | `app/schemas/rubric.py`, `app/api/v1/rubric_evaluation.py` |
| 2026-02-28 | B4.1 | Gap identificado em verificação pós-sprint: `cv_screening/agents/pipeline_system_prompt.py` (8° prompt) não tinha nenhuma seção de fairness. Corrigido imediatamente: bloco `=== FAIRNESS_AND_COMPLIANCE ===` adicionado cobrindo critérios proibidos para movimentação (gênero, idade, etnia, origem, faculdade específica), critérios permitidos (WSI score, rubricas, requisitos técnicos documentados), protocolo de recusa quando recrutador sugere critério discriminatório, e supervisão humana obrigatória (EU AI Act Art. 14). Nova regra 9 adicionada às `=== REGRAS CRITICAS ===`. Todos os 8 prompts agora cobertos. | `app/domains/cv_screening/agents/pipeline_system_prompt.py` |

---

## Relatório Técnico Detalhado — Implementações 2026-02-28

> Documentação técnica completa de todos os itens implementados no Sprint N e Sprint 1-2.
> Gerado após auditoria de 14 dimensões em 2026-02-28.

---

### SPRINT N — Quick Wins e Compliance

---

#### L1 — LangSmith desligado por padrão

**Problema:** `LANGCHAIN_TRACING_V2: bool = True` enviava dados de conversas (CVs, nomes, CPFs) para servidores LangChain nos EUA — violação do princípio de minimização LGPD art. 46.

**Mudança:**
```python
# app/core/config.py
LANGCHAIN_TRACING_V2: bool = False  # LGPD: opt-in only, nunca por padrão
```

**Arquivo:** `lia-agent-system/app/core/config.py`
**Risco de regressão:** Nulo — tracing só funciona se `LANGCHAIN_API_KEY` estiver definido.

---

#### L8 — Token webhook WhatsApp sem hardcode

**Problema:** `os.getenv("WHATSAPP_VERIFY_TOKEN", "lia_whatsapp_verify")` — fallback hardcoded permite forjar requisições ao webhook.

**Mudança:**
```python
# app/domains/communication/services/whatsapp_meta_service.py
self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
if not self.verify_token:
    raise ValueError("WHATSAPP_VERIFY_TOKEN não configurado")
```

**Arquivo:** `lia-agent-system/app/domains/communication/services/whatsapp_meta_service.py`

---

#### B1 — Nome do candidato removido do payload LLM

**Problema:** `_extract_cv_content()` incluía `Name: {candidate_data['name']}` no contexto do LLM — PII que introduz viés de gênero/etnia, viola LGPD art. 11 e princípio de avaliação cega do FairnessGuard.

**Mudança:** Remoção de `name`, `email`, `phone` do contexto enviado ao LLM em `rubric_evaluation_service.py`. O modelo avalia apenas competências, experiências e qualificações.

**Arquivo:** `lia-agent-system/app/domains/cv_screening/services/rubric_evaluation_service.py`

---

#### B2 — GEOGRAPHIC_ADJUSTMENTS discriminatório removido

**Problema:** `GEOGRAPHIC_ADJUSTMENTS` aplicava multiplicador `1.15` (exige 15% mais anos de experiência) para candidatos do Japão, Coreia do Sul e Índia — discriminação por origem nacional, viola EU AI Act art. 5.

**Mudança:** Bloco `"slow_progression"` com JP/KR/IN completamente removido de `calibration_profiles.py`. Critérios de avaliação passam a ser neutros por origem geográfica.

**Arquivo:** `lia-agent-system/app/domains/cv_screening/services/calibration_profiles.py`

---

#### A1 — Timeout no loop do Job Wizard

**Problema:** Loop `while current_node != END_NODE` sem timeout de wall-clock — LLM travado causava bloqueio indefinido de conexões FastAPI.

**Mudança:**
```python
# app/domains/job_management/agents/job_wizard_graph.py
async with asyncio.timeout(120):  # 2 minutos wall-clock máximo
    while current_node != self.END_NODE and iteration < self.MAX_ITERATIONS:
        ...
```

**Arquivo:** `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py`

---

#### A2 — Retry/fallback Gemini resposta vazia

**Problema:** Três métodos de `llm_gemini.py` retornavam silenciosamente `""` ou `"{}"` quando `response.text` era `None`. Sem retry, sem log — caller recebia dados vazios sem saber da falha.

**Mudança:** Retry com backoff exponencial (até 3 tentativas) + raise explícito com log estruturado na terceira falha.

**Arquivo:** `lia-agent-system/app/shared/providers/llm_gemini.py`

---

#### L3 — Human Review Gate (Rejeição Automatizada)

**Problema:** Flag `requires_confirmation: True` em `reject_candidate` era recomendação para o agente, não barreira técnica — qualquer chamada direta à API podia rejeitar candidatos sem confirmação humana.

**Implementação:**

*Backend — `app/api/v1/candidates.py`:*
- Guard em `PATCH /candidates/{id}/stage` para stages de rejeição
- Retorna HTTP 422 com `code: "human_review_required"` se `user_id` / `reviewer_id` não presente
- Referências de compliance no corpo do erro: LGPD art. 20, EU AI Act art. 14

*Modelo — `app/models/candidate.py` → `VacancyCandidate`:*
```python
rejected_by_human = Column(Boolean, nullable=True, default=None)
human_reviewer_id = Column(String(255), nullable=True)
```

*Migration:* `alembic/versions/010_add_human_review_gate.py`
- `down_revision = '009_*'`
- Colunas em `vacancy_candidates`: `rejected_by_human` (Boolean), `human_reviewer_id` (String 255)

**Arquivos:** `app/api/v1/candidates.py`, `app/models/candidate.py`, `alembic/versions/010_add_human_review_gate.py`

---

#### N-T1 — LIA descreve comunicação antes de confirmar transição

**Problema:** Ao usar `lia_auto` no `UniversalTransitionModal`, a comunicação disparada para o candidato era invisível — recrutador não sabia o que seria enviado antes de confirmar.

**Implementação — `app/domains/pipeline/agents/pipeline_system_prompt.py`:*
- Constante `COMMUNICATION_TRANSPARENCY_RULES` adicionada (linha 107)
- Instrução central: _"Quando a transição de etapa disparar mensagem automática para o candidato, sua confirmação DEVE descrever claramente o que será enviado — antes de confirmar a ação."_
- 27 few-shot examples cobrindo: triagem, agendamento, avaliação, oferta, rejeição individual e em lote
- Comportamentos mapeados com dispatch automático: `screening`, `scheduling`, `evaluation`, `offer`, `conclusion_rejected`

**Arquivo:** `lia-agent-system/app/domains/pipeline/agents/pipeline_system_prompt.py`

---

#### N-T2, N-T3, N-T4, N-T5 — Badges interativos e modais no Kanban

**Arquivo único:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`

**N-T2 — Badge "Status da Vaga" → interativo:**
- Estado `Ativa`: Popover com opções ⏸ Pausar / ✕ Fechar
- Estado `Paralisada`: abre `JobStatusModal` direto em modo reativação
- Visual: `cursor-pointer hover:bg-[#c8d4c7]` — DS v4.2.1 compliant

**N-T3 — Badge "Screening Status" → interativo:**

| Estado | Ação |
|--------|------|
| `active` | Popover: Pausar / Encerrar triagem |
| `paused` | Confirmação: Retomar triagem |
| `not_started` / `not_configured` | Abre configuração |
| `completed` | Badge inerte |

**N-T4 — `CloseVacancyModal` integrado ao Kanban:**
- Estado `showCloseVacancyModal` adicionado
- `hiredCandidate` e `otherCandidates` derivados de `candidatesData` existente no Kanban
- Acionado pelo Popover do N-T2 (opção "Fechar Vaga")
- Callback `onConfirm`: fecha vaga via API + dispara comunicações em lote

**N-T5 — `JobStatusModal` exposto no Kanban individual:**
- Estado `showJobStatusModal` adicionado
- `jobIds={[currentJob.id]}` — array de 1 item no contexto individual
- Acionado pelo Popover do N-T2 (opção "Pausar Vaga") e pelo badge "Paralisada"

---

#### N2 — Communication Matrix integrada ao TransitionDispatchService

**Problema:** `CommunicationMatrixEntry` existia no banco mas não era consultada durante transições — comunicações eram disparadas sem respeitar as configurações da matriz.

**Implementação — `app/domains/communication/services/transition_dispatch_service.py`:*
- `ACTION_BEHAVIOR_TRIGGER_MAP` (linhas 36-47): dict `action_behavior → trigger_name` para lookup na matriz
- `ACTION_BEHAVIOR_SITUATION_MAP` (linhas 22-33): mapa de situações por behavior
- `_get_matrix_entry()`: busca entrada na matriz com fallback `company_id → NULL` (platform default)
- Dispatch multi-canal via `effective_channels` da entrada encontrada
- Respeita flag `is_active` da entrada
- `requires_approval` logado (enforcement delegado ao L3 Human Review Gate)

**Arquivo:** `lia-agent-system/app/domains/communication/services/transition_dispatch_service.py`

---

### SPRINT 1-2 — Fundação e Compliance

---

#### A4 — Notas de Entrevista: Persistência em Banco

**Problema:** `interview_notes_db: dict = {}` em `app/api/v1/interview_notes.py` — armazenamento in-memory explicitamente marcado como mock. Notas de entrevista eram perdidas a cada restart do processo. Rota proxy FE inexistente.

**Stack completo implementado:**

**Modelo — `app/models/interview.py` (classe `InterviewNote`, linha 135):**

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID (PK) | auto-gerado |
| `company_id` | UUID | multi-tenant, indexed |
| `candidate_id` | UUID | indexed |
| `job_id` | UUID | nullable, indexed |
| `candidate_name` | String(255) | snapshot do nome |
| `job_title` | String(255) | snapshot do título |
| `interviewer_id` | UUID | nullable |
| `recruiter_name` | String(255) | snapshot |
| `scheduled_interview_id` | String(255) | FK lógica |
| `interview_type` | String(50) | default: "structured" |
| `interview_date` | DateTime | nullable |
| `questions` | JSON | lista de perguntas+respostas |
| `blocks` | JSON | blocos WSI (técnico/comportamental/gap/contextual) |
| `general_notes` | Text | anotações livres |
| `transcription` | Text | transcrição Teams/Meet/manual |
| `transcription_source` | String(50) | "teams", "meet", "manual" |
| `lia_parecer` | Text | parecer gerado pela LIA |
| `lia_parecer_editado` | Boolean | se recrutador editou o parecer |
| `wsi_score` | JSON | score WSI estruturado |
| `recommendation` | String(50) | "approved", "rejected", "review" |
| `next_stage` | String(100) | próxima etapa sugerida |
| `feedback_sent` | Boolean | se feedback foi enviado ao candidato |
| `feedback_scheduled_for` | DateTime | agendamento de feedback |
| `status` | String(20) | "draft" \| "completed", indexed |
| `created_at` | DateTime | indexed |
| `updated_at` | DateTime | auto-atualizado |
| `created_by` | String(255) | user_id do criador |

**Migration — `alembic/versions/011_add_interview_notes_table.py`:**
- `revision = '011_add_interview_notes_table'`
- `down_revision = '010_add_human_review_gate'`
- 27 colunas criadas na tabela `interview_notes`
- 5 indexes: `company_id`, `candidate_id`, `job_id`, `status`, `created_at`

**Service — `app/services/interview_notes_service.py`:**
```python
async def create_interview_note(db, company_id, candidate_id, ...) -> InterviewNote
async def get_interview_note(db, note_id, company_id) -> Optional[InterviewNote]
async def get_notes_for_candidate(db, candidate_id, company_id, job_id=None) -> list[InterviewNote]
async def update_interview_note(db, note_id, company_id, **fields) -> Optional[InterviewNote]
```
Todas as funções filtram por `company_id` — multi-tenant garantido.

**API — `app/api/v1/interview_notes.py`:**

| Método | Rota | Response Schema |
|--------|------|----------------|
| `POST` | `/interview-notes` | `InterviewNoteCreateResponse` |
| `GET` | `/interview-notes/{note_id}` | `InterviewNoteResponse` |
| `GET` | `/interview-notes/candidate/{candidate_id}` | `List[InterviewNoteSummary]` |
| `PATCH` | `/interview-notes/{note_id}` | `InterviewNoteUpdateResponse` |

Schemas Pydantic adicionados: `InterviewNoteResponse` (27 campos), `InterviewNoteSummary` (9 campos resumidos), `InterviewNoteUpdateResponse` (id, status, updatedAt).

**Proxy Routes FE:**

| Arquivo | Métodos | Backend alvo |
|---------|---------|-------------|
| `backend-proxy/interview-notes/route.ts` | `POST` | `POST /api/v1/interview-notes` |
| `backend-proxy/interview-notes/[noteId]/route.ts` | `GET`, `PATCH` | `/api/v1/interview-notes/{noteId}` |
| `backend-proxy/interview-notes/candidate/[candidateId]/route.ts` | `GET` (query: `jobId?`) | `/api/v1/interview-notes/candidate/{id}` |

Todas as rotas proxy usam `getAuthHeaders(request)` e `NEXT_PUBLIC_BACKEND_URL`.

---

#### A3 — Checkpoints de Estado do JobWizardGraph

**Problema:** `JobWizardState` (TypedDict) existia apenas em memória — falha ou restart durante criação de vaga reiniciava o wizard do zero, perdendo todo o progresso do recrutador. Solução nativa do LangGraph (`PostgresSaver`) não se aplica pois o graph usa implementação customizada (não `compile()`).

**Stack completo implementado:**

**Modelo — `app/models/agent_checkpoint.py`:**
```python
class AgentCheckpoint(Base):
    __tablename__ = "agent_checkpoints"
    id              = Column(UUID, pk)
    session_id      = Column(String(255), indexed)  # = conversa/sessão
    agent_type      = Column(String(100))            # = "job_wizard", "pipeline", etc.
    company_id      = Column(String(255), nullable, indexed)
    state_json      = Column(JSON)                   # estado sanitizado
    created_at      = Column(DateTime)
    updated_at      = Column(DateTime, auto-update)
    # Unique: (session_id, agent_type) — upsert por chave composta
```

**Migration — `alembic/versions/012_add_agent_checkpoints_table.py`:**
- `revision = '012_add_agent_checkpoints_table'`
- `down_revision = '011_add_interview_notes_table'`
- Unique constraint: `uq_agent_checkpoints_session_type (session_id, agent_type)`
- Indexes: `session_id`, `company_id` (partial NULL)

**Service — `app/services/checkpoint_service.py`:**
```python
async def save_checkpoint(db, session_id, agent_type, state, company_id=None)
    # PostgreSQL ON CONFLICT DO UPDATE — upsert atômico

async def restore_checkpoint(db, session_id, agent_type) -> dict | None

async def delete_checkpoint(db, session_id, agent_type)
    # Chamado quando wizard completa ou é cancelado

def _sanitize_state(state: dict) -> dict
    # Remove campos ephemeral antes de persistir:
    # user_message, error, tool_calls, tool_results, streaming_chunks
```

**Integração — `app/domains/job_management/agents/job_wizard_graph.py`:**
```python
# Início do invoke(): restaurar estado anterior se existir
prior = await restore_checkpoint(db, session_id, "job_wizard")
if prior:
    state = {**prior, **incoming_state}  # merge: incoming sobrescreve

# Fim do invoke(): salvar ou limpar conforme resultado
if current_stage in ("published", "cancelled"):
    await delete_checkpoint(db, session_id, "job_wizard")
else:
    await save_checkpoint(db, session_id, "job_wizard", dict(state), company_id)
```

---

#### L4 — LGPD Data Retention e Cleanup Scheduler

**Problema:** Candidatos rejeitados permaneciam no banco indefinidamente — violação da política de retenção LGPD. Não havia job automático nem mecanismo de agendamento de deleção.

**Stack completo implementado:**

**Migration — `alembic/versions/013_add_scheduled_deletion_at.py`:**
- `revision = '013_add_scheduled_deletion_at'`
- `down_revision = '012_add_agent_checkpoints_table'`
- Coluna `scheduled_deletion_at` (DateTime, nullable) adicionada a:
  - `candidates` → índice partial `WHERE scheduled_deletion_at IS NOT NULL`
  - `vacancy_candidates` → índice partial `WHERE scheduled_deletion_at IS NOT NULL`

**Modelos atualizados — `app/models/candidate.py`:**
```python
# Classe Candidate (linha 251)
scheduled_deletion_at = Column(DateTime, nullable=True, index=True)

# Classe VacancyCandidate (linha 381)
scheduled_deletion_at = Column(DateTime, nullable=True, index=True)
```

**Service — `app/services/lgpd_cleanup_service.py`:**

Política de retenção:
```python
RETENTION_DAYS = {
    "rejected":        90,   # candidatos reprovados
    "withdrawn":       90,   # candidatos que desistiram
    "interview_notes": 180,  # notas de entrevista
    "screening_logs":  365,  # logs de triagem
}
```

Funções:
```python
async def schedule_deletion_for_candidate(db, candidate_id, reason, retention_days=None) -> datetime
    # Calcula deletion_at = now + retention_days
    # Salva no campo scheduled_deletion_at do Candidate

async def run_cleanup(dry_run=True) -> dict
    # Abre própria sessão via AsyncSessionLocal()
    # Busca Candidates e VacancyCandidates com scheduled_deletion_at <= now
    # dry_run=True: apenas loga sem executar DELETE
    # dry_run=False: executa DELETE com audit log
    # Retorna: {dry_run, ran_at, candidates_deleted, vacancy_candidates_deleted, errors}

async def get_pending_deletions_count(db) -> dict
    # Retorna counts para dashboard de monitoramento DPO
```

**API — `app/api/v1/lgpd_compliance.py` (3 endpoints adicionados):**

| Método | Rota | Auth | Função |
|--------|------|------|--------|
| `POST` | `/lgpd/schedule-deletion` | qualquer usuário | Agenda deleção para um candidato |
| `POST` | `/lgpd/run-cleanup?dry_run=true` | **`require_admin`** | Executa cleanup manual (dry por padrão) |
| `GET` | `/lgpd/pending-deletions` | qualquer usuário | Contagem de registros pendentes |

O endpoint `/run-cleanup` exige role `admin` (`Depends(require_admin)`) — protege contra execução acidental por usuários comuns.

**Scheduler — `app/domains/automation/services/automation_scheduler.py`:**
```python
# Job: expirar trials (roda às 01:00 diariamente)
scheduler.add_job(expire_trials, CronTrigger(hour=1, minute=0))
# Lógica: UPDATE subscriptions SET status=SUSPENDED
#         WHERE status=TRIALING AND trial_end < now()

# Job: LGPD cleanup (roda às 02:00 diariamente, após expire_trials)
scheduler.add_job(run_lgpd_cleanup, CronTrigger(hour=2, minute=0))
# Lógica: run_cleanup(dry_run=False)
```

---

#### M2 — Trial com Expiração Real e Bloqueio de Acesso

**Problema:** Empresas em trial permaneciam com acesso integral indefinidamente — campo `trial_end` existia no modelo `Subscription` mas nunca era verificado em runtime.

**Stack completo implementado:**

**Middleware — `app/middleware/trial_enforcement.py`:**
```python
async def require_active_subscription(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # Skips: superadmin e cache em request.state (evita dupla query)
    # Busca Subscription mais recente da empresa
    # Bloqueia com HTTP 402 se:
    #   - status == TRIALING e trial_end < datetime.utcnow()  → transita para SUSPENDED
    #   - status == SUSPENDED
    #   - status == CANCELLED
```

Payload HTTP 402 retornado:
```json
{
  "code": "TRIAL_EXPIRED",
  "message": "Seu período de trial expirou. Faça upgrade para continuar usando a plataforma.",
  "upgrade_url": "/upgrade"
}
```

**Página de Upgrade — `plataforma-lia/src/app/upgrade/page.tsx`:**

| Plano | Preço | Vagas | Recrutadores | Candidatos/vaga |
|-------|-------|-------|--------------|----------------|
| Starter | R$ 990/mês | 5 | 3 | 500 |
| Pro | R$ 2.490/mês | 20 | 10 | 5.000 |
| Enterprise | Sob consulta | Ilimitadas | Ilimitados | Ilimitados |

Design System v4.2.1 compliant: `bg-gray-900` para botões primários, `rounded-md`, sem sombras.

**Handler FE — `plataforma-lia/src/lib/api/handle-payment-required.ts`:**
```typescript
checkPaymentRequired(response: Response): Promise<void>
  // Se response.status === 402 → chama handlePaymentRequired()

handlePaymentRequired(response: Response): Promise<never>
  // Parseia body JSON (fallback para defaults se falhar)
  // window.location.href = detail.upgrade_url  (redirect imediato)
  // throw new Error(detail.message)
```

---

#### M1 — Enforcing de Limites por Plano

**Problema:** Empresa em plano Starter podia criar vagas ilimitadas — limites existiam apenas como documentação, sem enforcement em runtime.

**Stack completo implementado:**

**Configuração — `app/core/config.py`:**
```python
PLAN_LIMITS_ENFORCE: bool = True          # feature flag — False em dev/staging se necessário
PLAN_STARTER_ACTIVE_JOBS: int = 5
PLAN_STARTER_USERS: int = 3
PLAN_STARTER_CANDIDATES_PER_JOB: int = 200
PLAN_PRO_ACTIVE_JOBS: int = 20
PLAN_PRO_USERS: int = 10
PLAN_PRO_CANDIDATES_PER_JOB: int = 2_000
PLAN_ENTERPRISE_ACTIVE_JOBS: int = 9_999  # efetivamente ilimitado
PLAN_ENTERPRISE_USERS: int = 9_999
PLAN_ENTERPRISE_CANDIDATES_PER_JOB: int = 9_999
PLAN_TRIAL_ACTIVE_JOBS: int = 3
PLAN_TRIAL_USERS: int = 2
PLAN_TRIAL_CANDIDATES_PER_JOB: int = 50
```

**Service — `app/services/plan_limits_service.py`:**

Mapeamento de plan codes por tier:
```python
_STARTER_CODES    = {"starter", "basic", "free"}
_PRO_CODES        = {"pro", "professional", "growth"}
_ENTERPRISE_CODES = {"enterprise", "unlimited", "custom"}
_TRIAL_CODES      = {"trial", "trialing"}
# Desconhecido → fallback para Starter (conservador)
```

Dependency FastAPI `check_active_jobs_limit`:
1. Skips se `PLAN_LIMITS_ENFORCE = False`
2. Skips se `current_user.is_superadmin`
3. Busca `Subscription` mais recente da empresa
4. Detecta tier pelo `plan_code` (prefix match nos sets acima)
5. Conta `JobVacancy` com `status == "Ativa"` para a empresa
6. Se `count >= limit`: HTTP 402

Payload HTTP 402 retornado:
```json
{
  "code": "PLAN_LIMIT_REACHED",
  "resource": "vagas ativas",
  "current": 5,
  "limit": 5,
  "plan": "Starter",
  "message": "Você atingiu o limite de 5 vagas ativas no plano Starter. Faça upgrade para continuar.",
  "upgrade_url": "/upgrade"
}
```

**Endpoint protegido — `app/api/v1/job_vacancies.py`:**
```python
@router.post("/job-vacancies")
async def create_job_vacancy(
    ...
    _trial_check: None = Depends(require_active_subscription),  # M2: verifica trial
    _plan_check:  None = Depends(check_active_jobs_limit),      # M1: verifica limite
):
```

**Frontend — `plataforma-lia/src/services/lia-api.ts`:**
```typescript
async createJobVacancy(data): Promise<JobVacancy> {
    const response = await fetch(...)
    await checkPaymentRequired(response)  // ← redireciona para /upgrade se 402
    // ... resto do error handling
}
```

---

### Cadeia de Migrações Alembic (Sequência Completa)

```
009_* (anterior)
  ↓
010_add_human_review_gate
    Tabela: vacancy_candidates
    Colunas: rejected_by_human (Boolean), human_reviewer_id (String 255)
  ↓
011_add_interview_notes_table
    Tabela nova: interview_notes
    27 colunas, 5 indexes (company_id, candidate_id, job_id, status, created_at)
  ↓
012_add_agent_checkpoints_table
    Tabela nova: agent_checkpoints
    Unique constraint: (session_id, agent_type)
  ↓
013_add_scheduled_deletion_at
    Tabela: candidates → scheduled_deletion_at (DateTime, partial index)
    Tabela: vacancy_candidates → scheduled_deletion_at (DateTime, partial index)
```

---

### Novos Arquivos Criados (Sprint N + Sprint 1-2)

**Backend:**
| Arquivo | Descrição |
|---------|-----------|
| `alembic/versions/010_add_human_review_gate.py` | Migration: campos L3 em VacancyCandidate |
| `alembic/versions/011_add_interview_notes_table.py` | Migration: tabela interview_notes (A4) |
| `alembic/versions/012_add_agent_checkpoints_table.py` | Migration: tabela agent_checkpoints (A3) |
| `alembic/versions/013_add_scheduled_deletion_at.py` | Migration: campo LGPD em candidates/vacancy_candidates (L4) |
| `app/models/agent_checkpoint.py` | Modelo SQLAlchemy AgentCheckpoint (A3) |
| `app/services/interview_notes_service.py` | CRUD de notas de entrevista (A4) |
| `app/services/checkpoint_service.py` | save/restore/delete checkpoints com upsert (A3) |
| `app/services/lgpd_cleanup_service.py` | Cleanup LGPD com dry_run mode (L4) |
| `app/services/plan_limits_service.py` | FastAPI dependency de limites por plano (M1) |
| `app/middleware/trial_enforcement.py` | FastAPI dependency de trial expiration (M2) |

**Frontend:**
| Arquivo | Descrição |
|---------|-----------|
| `src/app/upgrade/page.tsx` | Página de upgrade com 3 planos (M2) |
| `src/lib/api/handle-payment-required.ts` | Handler HTTP 402 com redirect (M1/M2) |
| `src/app/api/backend-proxy/interview-notes/route.ts` | Proxy POST notas (A4) |
| `src/app/api/backend-proxy/interview-notes/[noteId]/route.ts` | Proxy GET/PATCH nota por ID (A4) |
| `src/app/api/backend-proxy/interview-notes/candidate/[candidateId]/route.ts` | Proxy GET notas por candidato (A4) |

---

### Arquivos Modificados (Sprint N + Sprint 1-2)

**Backend:**
| Arquivo | Mudança |
|---------|---------|
| `app/core/config.py` | L1: LANGCHAIN_TRACING_V2=False; M1: PLAN_LIMITS_* settings |
| `app/models/interview.py` | A4: InterviewNote model adicionado |
| `app/models/candidate.py` | L3: rejected_by_human, human_reviewer_id em VacancyCandidate; L4: scheduled_deletion_at em Candidate e VacancyCandidate |
| `app/models/__init__.py` | A4: InterviewNote; A3: AgentCheckpoint exportados |
| `app/domains/pipeline/agents/pipeline_system_prompt.py` | N-T1: COMMUNICATION_TRANSPARENCY_RULES |
| `app/domains/communication/services/transition_dispatch_service.py` | N2: ACTION_BEHAVIOR_TRIGGER_MAP, _get_matrix_entry, multi-channel dispatch |
| `app/domains/job_management/agents/job_wizard_graph.py` | A1: asyncio.timeout(120); A3: checkpoint restore/save/delete integrado |
| `app/domains/automation/services/automation_scheduler.py` | L4/M2: jobs expire_trials (01h) e run_lgpd_cleanup (02h) |
| `app/api/v1/candidates.py` | L3: guard HTTP 422 em stage change para rejeição |
| `app/api/v1/interview_notes.py` | A4: mock dict removido, 3 endpoints adicionados, response_model tipados |
| `app/api/v1/lgpd_compliance.py` | L4: 3 endpoints LGPD; require_admin em /run-cleanup |
| `app/api/v1/job_vacancies.py` | M1+M2: require_active_subscription + check_active_jobs_limit em create_job_vacancy |
| `app/shared/providers/llm_gemini.py` | A2: retry + logging Gemini |
| `app/domains/cv_screening/services/rubric_evaluation_service.py` | B1: PII removido do payload LLM |
| `app/domains/cv_screening/services/calibration_profiles.py` | B2: GEOGRAPHIC_ADJUSTMENTS removido |
| `app/domains/communication/services/whatsapp_meta_service.py` | L8: token sem hardcode |

**Frontend:**
| Arquivo | Mudança |
|---------|---------|
| `src/components/pages/job-kanban-page.tsx` | N-T2/T3/T4/T5: badges interativos, CloseVacancyModal e JobStatusModal integrados |
| `src/services/lia-api.ts` | M1: checkPaymentRequired em createJobVacancy |