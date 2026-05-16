# Handoff — Aba "Configurações de Triagem" da página da vaga

> **Escopo (Task #1136).** Este handoff cobre, **botão por botão**, tudo que está visível nas DUAS screenshots tiradas em 16/05/2026:
>
> - `attached_assets/Screen_Shot_2026-05-16_at_8.39.52_AM_1778931599221.png`
> - `attached_assets/Screen_Shot_2026-05-16_at_8.41.40_AM_1778931702853.png`
>
> Cada seção deste documento é **autossuficiente** o bastante para virar um card de Jira sem que o time precise ler o restante. As seções estão na mesma ordem em que aparecem na UI (top-down, esquerda → direita). Idioma: PT-BR.
>
> **Out of scope:** as abas vizinhas `Gestão da Vaga` e `Triagem (execução)`; as sub-páginas `Descrição do Cargo` e `Perguntas de Triagem` (apenas mencionadas como itens da sidebar); qualquer implementação, migration ou ajuste de código.

---

## 1. Mini-mapa visual das duas screenshots

```
┌───────────────────────────────────────────────────────────────────────────┐
│ HEADER DA PÁGINA DA VAGA (sec. A)                                         │
│  [← Voltar] │ Desenvolvdor Python Senior [Ativa] [Triagem: Configurar]    │
│  [Sênior] [Híbrido] [CLT] [Tecnologia] [São Paulo, São Paulo] | 14 mai…   │
│  [Prazo short: 24 mai] [Encerramento: 4 jun] [Prazo triagem: 21 mai]      │
│                                            [📄 Relatório] [↗ Compartilhar]│
│ TABS (sec. B):  [⎯ Gestão da Vaga (0)]  [⊙ Triagem]  [⚙ Configurações]   │
│                                                     🔗 Herdado da empresa │
├───────────────┬───────────────────────────────────────────────────────────┤
│ SIDEBAR       │ HEADER DA SUB-SEÇÃO (sec. D)                              │
│ CONFIGURAÇÕES │  ≡ Configurações do Roteiro   [Canal: Chat Web] [Cancelar]│
│ DA VAGA (C.1) │     Formato e duração da triagem               [💾 Salvar]│
│  • Informações│                                                           │
│    Gerais   ✓ │ ┌───────────────────────────────────────────────────────┐ │
│  • Pessoas  ✓ │ │ E. Status da Triagem          [Configurar]            │ │
│  • Processo ✓ │ ├───────────────────────────────────────────────────────┤ │
│    Seletivo   │ │ F. Canal de Triagem (fallback chain)                  │ │
│  • Remuneraç.✓│ │   ● Chat Web              [★ Principal]               │ │
│               │ │   ○ WhatsApp              [Fallback 1] [Definir princ.]│ │
│ CONFIGURAÇÕES │ │   ○ Ligação (PSTN)        [Não disponível]            │ │
│ DE TRIAGEM    │ │   ○ Voz no Navegador      [+ Fallback]                │ │
│ (C.2)         │ ├───────────────────────────────────────────────────────┤ │
│  • Config.    │ │ G. Canais Habilitados                  [Master ligado]│ │
│    do Roteiro │ │   • Chat Web                                    [ON]  │ │
│    (ativo)    │ │   • WhatsApp                                    [ON]  │ │
│  • Descrição  │ │     Modo de envio: [Link wa.me|Twilio WA Bus.|Ambos]  │ │
│    do Cargo ✓ │ │   • Ligação (PSTN)  (Integração pendente)       [off] │ │
│  • Perguntas  │ │   • Voz no Navegador                            [off] │ │
│    de Triagem │ ├───────────────────────────────────────────────────────┤ │
│   ◯           │ │ H. Configurações                                      │ │
│               │ │   Score Mínimo Aprovação (WSI): Rigoroso/Recomendado/ │ │
│               │ │     Flexível                                          │ │
│               │ │   Timeout Resposta [48h ▼]  Re-tentativas [2x ▼]      │ │
│               │ ├───────────────────────────────────────────────────────┤ │
│               │ │ I. Controle de Paralização                            │ │
│               │ │   Limite de aprovações automáticas: 5 / 10 / 25       │ │
│               │ ├───────────────────────────────────────────────────────┤ │
│               │ │ J. Prazo da Triagem                                   │ │
│               │ │   Data Limite [22/05/2026]                            │ │
│               │ ├───────────────────────────────────────────────────────┤ │
│               │ │ K. Agendamento Automático             [ON]            │ │
│               │ │   Score Mínimo para Agendamento (WSI): R / Rec / F    │ │
│               │ │   Calendário [Microsoft ▼]                            │ │
│               │ │   Horários   [9h-18h] (Conforme config. da empresa)   │ │
│               │ │   Duração    [60min ▼]                                │ │
│               │ └───────────────────────────────────────────────────────┘ │
└───────────────┴───────────────────────────────────────────────────────────┘
```

A screenshot **8.39** cobre o cabeçalho da página + sidebar + sub-seções **D, E, F, G**.
A screenshot **8.41** cobre as sub-seções **H, I, J, K**.

---

## 2. Tabela-resumo (controle → arquivo canônico → endpoint → agente IA → paridade)

| # | Controle visível | Arquivo canônico (frontend) | Endpoint (Rails / FastAPI) | Agente IA / serviço | Paridade |
|---|---|---|---|---|---|
| A1 | Botão `← Voltar` | `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx:57-60` | — (navegação client-side) | — | ✅ |
| A2 | Título `Desenvolvdor Python Senior` | `KanbanJobHeader.tsx:64-66` | GET `/api/v1/jobs/{id}` | — | ✅ |
| A3 | Chip código da vaga (`jobId`) | `KanbanJobHeader.tsx:67-71` | idem | — | ✅ |
| A4 | Badge de status `Ativa` (popover Pausar / Encerrar / Reativar) | `KanbanJobHeader.tsx:72-115` | PATCH `/api/v1/jobs/{id}` (status) | — | 🟡 Rails: `ats_api/app/controllers/v1/users/jobs_controller.rb` deve receber o mesmo payload |
| A5 | Badge `Triagem: Configurar` (popover por status) | `KanbanJobHeader.tsx:116-205` | PATCH `/api/v1/jobs/{id}` (`screeningStatus`) — `liaApi.updateJobVacancy` | `app/domains/cv_screening/agents/pipeline_react_agent.py` lê `screening_status` ⚠️ confirmar | 🟡 Rails sem coluna `screening_status` (a confirmar via migration audit) |
| A6 | Chips de meta (nível, modelo, contrato, dept., localidade, salário, "publicada") | `KanbanJobHeader.tsx:207-237` | GET `/api/v1/jobs/{id}` | — | ✅ |
| A7 | Datas (`14 de mai. de 2026`, `1d aberta`, `Atualizada: 16 de mai.`) | `KanbanJobHeader.tsx:238-259` | idem | — | ✅ |
| A8 | Chips de prazo (`Prazo triagem`, `Prazo short`, `Encerramento`) | `KanbanJobHeader.tsx:260-277` | idem (`deadlineScreening`, `deadlineShortlist`, `deadlineClosing`) | — | 🟡 Rails só guarda `deadline` único |
| A9 | Chip `Sugestões LIA` (quando há) | `KanbanJobHeader.tsx:278-289` | GET sugestões LIA | `OpinionAgent` / `JDEnrichmentAgent` | ✅ |
| A10 | Botão `📄 Relatório` | `KanbanJobHeader.tsx:294-298` | GET `/api/v1/jobs/{id}/report` | — | 🟡 Rails sem endpoint paritário |
| A11 | Botão `↗ Compartilhar` | `KanbanJobHeader.tsx:299-309` | Modal client; envia via integração de e-mail | — | 🟡 |
| B1 | Tab `Gestão da Vaga (0)` | `KanbanJobHeader.tsx:315-332` | — (state local) | — | ✅ |
| B2 | Tab `Triagem` | **não existe no código canônico atual** — visível na screenshot mas KanbanJobHeader tem só 2 tabs | — | — | 🔴 Mockado apenas |
| B3 | Tab `⚙ Configurações` (ativa) | `KanbanJobHeader.tsx:333-343` | — (alterna `activeTab='edit'` → renderiza `JobEditTab`) | — | ✅ |
| B4 | Indicador `🔗 Herdado da empresa` / `Pipeline customizado` + `Resetar para padrão` | `KanbanJobHeader.tsx:344-373` | POST reset pipeline → `pipelineInheritance.resetToCompanyDefault` | `app/domains/cv_screening/agents/pipeline_react_agent.py` (a confirmar) | ✅ (frontend) / ⚠️ (handler do reset não foi auditado neste handoff) |
| C1.1 | Item sidebar `Informações Gerais` ✓ | `plataforma-lia/src/components/jobs/JobEditTab.tsx:111-145` + `SECTIONS` em `job-edit-tab.constants` | — (state) | — | ✅ |
| C1.2 | Item sidebar `Pessoas` ✓ | `JobEditTab.tsx:119-145` (SECTIONS) | — | — | ✅ |
| C1.3 | Item sidebar `Processo Seletivo` ✓ | `JobEditTab.tsx:119-145` | — | — | ✅ |
| C1.4 | Item sidebar `Remuneração` ✓ | `JobEditTab.tsx:119-145` | — | — | ✅ |
| C2.1 | Item sidebar `Configurações do Roteiro` (ativo) | `JobEditTab.tsx:154-180` + `SCREENING_SECTIONS` em `ScreeningConfigManager.tsx:57-76` | — | — | ✅ |
| C2.2 | Item sidebar `Descrição do Cargo` ✓ | `JobEditTab.tsx:154-180` + `SCREENING_SECTIONS:64-69` | — | `JDEnrichmentAgent` | ✅ |
| C2.3 | Item sidebar `Perguntas de Triagem` ◯ | `JobEditTab.tsx:154-180` + `SCREENING_SECTIONS:70-75` | — | WSI: `app/api/v1/wsi_questions.py` + `app/services/wsi_compact_pipeline.py` (não há `WSIScreeningAgent` único ⚠️) | ✅ |
| D1 | Cabeçalho `≡ Configurações do Roteiro` + descrição | `plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx:124-149` (via `ScreeningConfigManager.tsx:132-141`) | — | — | ✅ |
| D2 | Chip `Canal: Chat Web` (status info) | `ScreeningConfigManager.tsx:143-147` (`getConfigStatusInfo()`) | — | — | ✅ |
| D3 | Botão `Editar Configurações` (entra em modo edição) | `ScreeningConfigManager.tsx:148-157` | — | — | ✅ |
| D4 | Botão `Cancelar` (modo edição) | `ScreeningConfigManager.tsx:160-189` | — (reverte state) | — | ✅ |
| D5 | Botão `💾 Salvar` (modo edição) | `ScreeningConfigManager.tsx:190-260` → `updateScreeningConfig(...)` | PUT `/api/backend-proxy/jobs/{id}/screening-config` → `lia-agent-system/app/api/v1/job_vacancies/screening.py:156-222` | `app/domains/cv_screening/agents/pipeline_react_agent.py`, `app/domains/cv_screening/services/confidence_policy_service.py`, `app/shared/messaging/broker_interface.py` | 🟡 Rails paridade parcial via colunas (`ats_api/app/models/job.rb:572-639`) — não há JSONB agregado |
| E1 | Card `Status da Triagem` + botão `Configurar` | `SCMSectionConfiguracoes.tsx` (status block) | PATCH `/api/v1/jobs/{id}` (`screeningStatus`) | `app/domains/cv_screening/agents/pipeline_react_agent.py` | 🟡 |
| F1 | Card de canal `Chat Web` `[★ Principal]` | `SCMSectionConfiguracoes.tsx:163-205` | PUT `screening-config` (`screening_channels.primary_channel`) | `app/shared/messaging/broker_interface.py` | ✅ |
| F2 | Card `WhatsApp` `[Fallback 1]` + botão `Definir principal` | `SCMSectionConfiguracoes.tsx:206-220` | idem (`screening_channels.fallback_order`) | `app/shared/messaging/broker_interface.py` + WhatsApp BSP | 🟡 |
| F3 | Card `Ligação (PSTN)` `[Não disponível — config. pendente]` | `SCMSectionConfiguracoes.tsx:222-235` | idem | Twilio fallback | 🔴 |
| F4 | Card `Voz no Navegador` `[+ Fallback]` + `Definir principal` | `SCMSectionConfiguracoes.tsx:236-250` | idem | Gemini Live Audio | 🟡 |
| G0 | Switch master `Master ligado` (Canais Habilitados) | `SCMSectionConfiguracoes.tsx:259-272` | PUT `screening-config` (`channels_master_enabled`) | — | ✅ |
| G1 | Toggle `Chat Web` | `SCMSectionConfiguracoes.tsx:275-289` | PUT (`channels.chat_web.enabled`) | — | ✅ |
| G2 | Toggle `WhatsApp` + sub-radio `Link wa.me` / `Twilio WA Business` / `Ambos` | `SCMSectionConfiguracoes.tsx:291-340` | PUT (`channels.whatsapp.enabled`, `channels.whatsapp.mode`) | WhatsApp BSP | 🟡 |
| G3 | Toggle `Ligação (PSTN)` `(Integração pendente)` | `SCMSectionConfiguracoes.tsx:342-358` | PUT (`channels.phone_pstn.enabled`) | Twilio | 🔴 |
| G4 | Toggle `Voz no Navegador` | `SCMSectionConfiguracoes.tsx:360-376` | PUT (`channels.voice_web.enabled`) | Gemini Live Audio | ✅ |
| H1 | Preset `Rigoroso ≥ 8.4/10` (Score Mínimo Aprovação WSI) | `SCMSectionConfiguracoes.tsx:386-417` | PUT (`settings.min_score_preset='rigorous'`) | `app/services/wsi_compact_pipeline.py` + `app/domains/cv_screening/agents/pipeline_react_agent.py`; `app/shared/compliance/fairness_guard.py` L1 | ✅ |
| H2 | Preset `Recomendado ≥ 7.6/10` | idem | PUT (`min_score_preset='recommended'`) | idem | ✅ |
| H3 | Preset `Flexível ≥ 6.0/10` | idem | PUT (`min_score_preset='flexible'`) | idem | ✅ |
| H4 | Select `Timeout Resposta` (default 48h) | `SCMSectionConfiguracoes.tsx:419-440` | PUT (`settings.response_timeout_hours`) | `app/shared/messaging/broker_interface.py` | ✅ |
| H5 | Select `Re-tentativas` (default 2x) | `SCMSectionConfiguracoes.tsx:442-462` | PUT (`settings.max_retries`) | `app/shared/messaging/broker_interface.py` | ✅ |
| I1 | Preset `Conservador 5 aprovações` (Controle de Paralização) | `SCMSectionConfiguracoes.tsx:467-510` | PUT (`settings.auto_approval_preset='conservative'`, `auto_approval_limit=5`) | `app/domains/cv_screening/services/confidence_policy_service.py`; `CompanyHiringPolicy` (⚠️ confirmar path) | ✅ |
| I2 | Preset `Recomendado 10 aprovações` | idem | PUT (`auto_approval_preset='recommended'`, limit=10) | idem | ✅ |
| I3 | Preset `Autônomo 25 aprovações` | idem | PUT (`auto_approval_preset='autonomous'`, limit=25) | idem | ✅ |
| I4 | Aviso `Triagem pausada — limite atingido` + botão `Retomar` | `SCMSectionConfiguracoes.tsx:676-682` | — (handler **vazio** hoje) | `app/domains/cv_screening/services/confidence_policy_service.py` | 🔴 |
| J1 | Date picker `Data Limite` (default 22/05/2026) | `SCMSectionConfiguracoes.tsx:512-528` | PUT (`deadline_screening`) | `app/domains/cv_screening/agents/pipeline_react_agent.py` (gating de prazo) | 🟡 |
| K0 | Switch master `Agendamento Automático` | `SCMSectionConfiguracoes.tsx:534-553` | PUT (`scheduling.auto_enabled`) | `app/domains/interview_intelligence/services/*` (não há ReAct agent dedicado ⚠️) | ✅ |
| K1 | Presets `Score Mínimo para Agendamento (WSI)` (R/Rec/F) | `SCMSectionConfiguracoes.tsx:555-595` | PUT (`scheduling.min_score_for_auto_preset`) | idem | ✅ |
| K2 | Select `Calendário` (default `Microsoft`; opções: `Microsoft`, `Google`, `Outlook`) | `SCMSectionConfiguracoes.tsx:334` (display) + `:744-746` (options em modo edit) | PUT (`scheduling.calendar_provider`) | Microsoft Graph (Google/Outlook ⚠️ não implementados no backend) | 🟡 |
| K3 | Campo `Horários` (`9h-18h`, "Conforme config. da empresa") | `SCMSectionConfiguracoes.tsx:627-668` | PUT (`scheduling.available_hours` + `available_hours_inherited`) | — | ✅ |
| K4 | Select `Duração` (default `60min`) | `SCMSectionConfiguracoes.tsx:670-695` | PUT (`scheduling.interview_duration_min`) | `app/domains/interview_intelligence/services/*` | ✅ |

**Legenda de paridade:** ✅ Implementado · 🟡 Parcial · 🔴 Mockado / sem backend · ⚠️ Divergente entre camadas.

---

## 3. Glossário curto

- **WSI (WeDoTalent Skill Index).** Metodologia LIA de pontuação 0–10 de candidato, com 6 blocos de avaliação. O "Score Mínimo Aprovação (WSI)" e o "Score Mínimo para Agendamento (WSI)" desta tela referenciam esse índice.
- **FairnessGuard.** Camada de compliance que valida toda decisão de aprovação/rejeição por viés (4 dimensões: gênero, raça, idade, deficiência). Aplica L1 antes do classifier, L3 após o agente.
- **HITL (Human-in-the-loop).** Pontos de aprovação humana no fluxo automático. O wizard de criação de vaga tem 4 HITLs; a triagem usa HITL toda vez que o "Controle de Paralização" pausa o pipeline.
- **Master switch.** Switch único que liga/desliga em bloco todo um grupo de toggles (ex.: `Canais Habilitados`, `Agendamento Automático`). Quando OFF, os toggles individuais ficam desabilitados.
- **Fallback de canal.** Ordem de tentativa caso o canal principal falhe (`primary → fallback_order[0] → fallback_order[1] → ...`). Persistido em `screening_channels.fallback_order`.
- **Re-tentativa.** Quantas vezes o canal principal tenta de novo antes de cair no fallback. Default `2x`.
- **Paralização.** Limite de aprovações automáticas seguidas; ao atingir, a triagem pausa e exige revisão humana antes de continuar.
- **Herdado da empresa.** Marcador de que o valor exibido vem da configuração company-wide (`CompanyHiringPolicy`) e não foi sobrescrito por essa vaga. Sobrescrever cria um override no nível da vaga e exibe `Pipeline customizado`.
- **Master ligado.** Texto literal mostrado no switch master do bloco "Canais Habilitados" quando ON.
- **`screeningStatus`.** Coluna calculada da vaga: `not_configured | not_started | active | paused | completed`. Controla o badge "Triagem: Configurar/Ativa/Pausada/Concluída" e a renderização do popover.

---

## 4. Arquivos canônicos referenciados (validados linha a linha)

### Frontend (`plataforma-lia/`)

- `src/components/pages/job-kanban/KanbanJobHeader.tsx:1-380` — header da página (Voltar, título, badges, chips, Relatório, Compartilhar, tabs, indicador "Herdado da empresa").
- `src/components/jobs/JobEditTab.tsx:1-300` — sidebar com os dois grupos `Configurações da Vaga` e `Configurações de Triagem`.
- `src/components/jobs/job-edit-tab/job-edit-tab.constants.ts` — array `SECTIONS` (Informações Gerais, Pessoas, Processo Seletivo, Remuneração).
- `src/components/jobs/job-edit-tab/useJobEditTab.ts` — `jobSectionCompletion`, `screeningCompletion`, `getScreeningImpact`.
- `src/components/jobs/job-edit-tab/ScreeningBadge.tsx` — render do chip `Triagem: …` quando reutilizado.
- `src/components/screening-config/ScreeningConfigManager.tsx:1-426` — sidebar interna (`SCREENING_SECTIONS`), cabeçalho da sub-seção, botões `Editar Configurações`, `Cancelar`, `Salvar`.
- `src/components/screening-config/SCMSectionConfiguracoes.tsx:1-769` — view (`1-358`) e edit (`360-769`) de Status, Canais, Score, Timeout, Re-tentativas, Paralização, Prazo e Agendamento.
- `src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx` — orquestra estado de edição, validação e salvamento.
- `src/hooks/recruitment/useScreeningConfig.ts` — fetch + mutate via proxy `/api/backend-proxy/jobs/{id}/screening-config` (helpers `limitToApprovalPreset` / `approvalPresetToLimit`).
- `src/app/api/backend-proxy/jobs/[id]/screening-config/route.ts` — GET/PUT, valida sessão e propaga `Authorization` para FastAPI.
- `src/services/lia-api/misc-api.ts` — `liaApi.updateJobVacancy(...)` usado pelo badge `Triagem: …`.
- `src/types/screening.ts` — `SCREENING_STATUS_LABELS` (`not_configured | not_started | active | paused | completed`).

### Camada de IA (`lia-agent-system/`) — paths validados via `ls`

- `app/domains/cv_screening/agents/pipeline_react_agent.py` ✅ — ReAct agent canônico do domínio `cv_screening`; consome `screening_config` da vaga para decidir gating de aprovação.
- `app/domains/cv_screening/services/confidence_policy_service.py` ✅ — implementa o `Controle de Paralização` (limite de aprovações automáticas). *(Existe também `app/shared/services/confidence_policy_service.py` como camada compartilhada.)*
- `app/shared/messaging/broker_interface.py` ✅ — abstrai envio por canal (`chat_web`, `whatsapp`, `phone_pstn`, `voice_web`).
- `app/shared/compliance/fairness_guard.py` ✅ — L1 antes da decisão de aprovação automática.
- `app/domains/interview_intelligence/services/` ✅ — serviços que consomem `scheduling.*` (`interview_wsi_service.py`, `comparative_analysis_service.py`, `feedback_generator_service.py`, `strategic_opinion_service.py`, `transcription_service.py`, `bias_detector_service.py`). **Não há um agente "InterviewIntelligenceAgent" único** ⚠️ — agendamento é orquestrado por serviços + endpoints REST, não por ReAct agent dedicado.
- **WSI screening como "agente" único** ⚠️ Pendente — WSI hoje está distribuído entre `app/api/v1/wsi/*.py` (endpoints), `app/services/wsi_*.py` (`wsi_compact_pipeline.py`, `wsi_async_session_service.py`) e o `pipeline_react_agent` do `cv_screening`. Não existe arquivo `wsi_screening_agent.py`.

### Backend Rails (`ats_api/`) — paths verificados via `ls` + `rg` (snapshot 16/05/2026)

- `ats_api/config/routes.rb` ✅ — bloco `resources :jobs` (rotas aninhadas: `kanban`, `analytics`, `gate1/approve|reject`, `gate2/approve|reject`, `applies/*`). **Não há rota `screening_config` ou `screening-config`** ⚠️ — Rails serializa as colunas dentro do payload de `GET /v1/users/jobs/:id`.
- `ats_api/app/controllers/v1/users/jobs_controller.rb` ✅ — controller principal de jobs (autenticado por usuário). *(Também `ats_api/app/controllers/v1/public/jobs_controller.rb` para o portal público.)*
- `ats_api/app/models/job.rb:572-639` ✅ — modelo canônico **com paridade parcial real** para os controles de triagem:
  - `is_screening_active` (linha 572) — equivale ao master switch (E1).
  - `use_whatsapp_channel`, `use_webchat_channel`, `use_voice_channel`, `use_call_channel`, `notification_channels` (linhas 592-596) — equivalem aos toggles **G1–G4 + F1–F4**.
  - `minimum_screening_score` (596) — equivale a **H1–H3**.
  - `screening_timeout` (597) — equivale a **H4**.
  - `screening_max_attempts` (598) — equivale a **H5**.
  - `screening_approve_limit` (599) — equivale a **I1–I3**.
  - `interview_minimum_score` (600), `has_automatic_interview` (601), `interview_calendar_type` (602), `interview_hours_range` (603), `interview_duration` (604) — equivalem a **K0–K4**.
  - **Sem coluna `screening_status` enum** ⚠️ — Rails só tem booleano `is_screening_active`; o status rico (`not_configured | active | paused | completed`) vive só no FastAPI via `derive_screening_status` (ver abaixo).
  - **Sem coluna `deadline_screening`** ⚠️ — apenas `deadline` único (A8 / J1).
  - **Sem coluna `screening_config` JSONB** ⚠️ — Rails guarda como colunas separadas; FastAPI persiste o agregado em `screening_config: jsonb` (a confirmar via migration audit).

### Endpoint FastAPI canônico (snapshot via `rg` em 16/05/2026)

- `lia-agent-system/app/api/v1/job_vacancies/screening.py:106-155` — `GET /vagas/{job_id}/screening-config`.
- `lia-agent-system/app/api/v1/job_vacancies/screening.py:156-222` — `PUT /vagas/{job_id}/screening-config` (handler `update_screening_config`).
- `lia-agent-system/app/api/v1/job_vacancies/screening.py:223+` — `PUT /vagas/{job_id}/screening-status`.
- `lia-agent-system/app/api/v1/job_vacancies/_shared.py:145+` — `derive_screening_status(screening_config: dict) -> str` (única fonte de verdade do status rico).
- `lia-agent-system/app/api/v1/job_vacancies/crud.py` — projeta `screening_status` derivado no payload de listagem/detalhe.

### Governance / flags de runtime

> **Nota de drift:** este handoff foi consolidado em **16/05/2026** com base em `rg`/`ls` no commit corrente. Antes de gerar Jira a partir dele, validar novamente as linhas citadas — o repositório evolui semanalmente.


- **`LIA_WSI_QUESTIONS_TIMEOUT_S`** (default `20`s) — controla o timeout da geração de perguntas WSI. Afeta indiretamente **H1–H3** quando o agente precisa regenerar bateria após mudança de preset.
- **Demais flags `LIA_*`** listadas em `replit.md` (compliance, wizard, supervisor) **não governam diretamente** os controles desta tela. Em particular, `LIA_DISABLE_C3B`, `LIA_ALLOW_NON_COMPLIANT_AGENTS` e `LIA_AGENT_TENANT_STRICT` afetam transversalmente o `pipeline_react_agent` que consome `screening_config` — bypass aqui é emergency-only.
- **`CompanyHiringPolicy`** (Progressive Automation) — política company-wide que pode sobrescrever os limites de **I1–I3** via `confidence-based decision engine` (caminho canônico ⚠️ pendente — não auditado neste handoff).
- **Nenhuma `LIA_*` flag específica governa F1–F4, G0–G4, K0–K4 ou J1** — comportamento dirigido 100% pelo conteúdo do `screening_config` persistido.

---

## 5. Seções detalhadas (uma por controle)

### A. Header da página da vaga (screenshot 8.39 — topo)

#### A1. Botão `← Voltar`

- **O que é.** Navegação client-side para a página anterior (`router.back()` ou `onBack` injetado).
- **Estado atual no protótipo.** Sempre habilitado. Sem confirmação ao sair com edição pendente.
- **Efeito ao clicar.** Sai da página; **não há prompt** se o usuário estiver no modo "Editar Configurações" com mudanças não salvas.
- **Rails (`ats_api`).** N/A.
- **Camada de IA.** N/A.
- **Arquivo.** `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx:57-60`.
- **Paridade.** ✅ Implementado · ⚠️ falta proteger edição pendente.
- **Jira sugerido — LIA-XXX1.** *Proteger Voltar contra perda de edição em "Configurações do Roteiro"* — adicionar dialog de confirmação quando `isEditingScreeningConfig === true` e houver diff.
  - Critérios: (a) clicar `Voltar` em modo edição abre modal; (b) "Sair sem salvar" descarta diff; (c) "Continuar editando" mantém estado.

#### A2. Título da vaga

- **O que é.** Render de `currentJob.title` (`<h1>`).
- **Estado.** Read-only neste header.
- **Efeito ao salvar título em outra tela.** Reflete imediatamente via revalidação de `getJobVacancy`.
- **Rails.** GET `/v1/jobs/:id` (paridade ✅).
- **Arquivo.** `KanbanJobHeader.tsx:64-66`.
- **Paridade.** ✅.
- **Jira sugerido — LIA-XXX2.** N/A (só citado para inventário).

#### A3. Chip do código da vaga (`jobId`)

- **O que é.** Render de `currentJob.jobId` (ou `id` fallback).
- **Arquivo.** `KanbanJobHeader.tsx:67-71`.
- **Paridade.** ✅.

#### A4. Badge de status `Ativa` (popover Pausar / Encerrar / Reativar)

- **O que é.** Pílula clicável que mostra o status da vaga. Popover muda conforme `status` atual: se `Ativa` mostra `Pausar vaga` + `Encerrar vaga`; senão mostra `Reativar vaga` + `Encerrar vaga`.
- **Estado.** Default = valor do backend. Edição direta inline via popover.
- **Efeito ao mudar.** Abre `StatusChangeConfirmModal` que recalcula `screeningImpact` (`useJobEditTab.handleStatusChangeWithScreening`); ao confirmar, PATCH `/v1/jobs/{id}` e atualiza `jobEditForm.status`.
- **Rails.** PATCH `/v1/jobs/:id` (paridade ✅ para status).
- **Camada de IA.** `app/domains/cv_screening/agents/pipeline_react_agent.py` recalcula gating quando `status='Paralisada'`.
- **Arquivos.** `KanbanJobHeader.tsx:72-115`; `JobEditTab.tsx:209-216`; `job-edit-tab/StatusChangeConfirmModal.tsx`.
- **Paridade.** 🟡 (modal de impacto não bloqueia inconsistências entre status da vaga e `screeningStatus`).
- **Jira sugerido — LIA-XXX3.** *Bloquear "Encerrar vaga" quando há triagem ativa sem revisão* — exigir confirmação dupla.

#### A5. Badge `Triagem: Configurar` (popover por `screeningStatus`)

- **O que é.** Pílula que mostra a etapa atual da triagem. Cinco labels possíveis: `Configurar | Não iniciada | Ativa | Pausada | Concluída`.
- **Estado.** Vem de `currentJob.screeningStatus` (default `not_configured`).
- **Comportamento por status:**
  - `not_configured` → opção `Configurar triagem` (leva à tab `Configurações` desta página).
  - `not_started` → `Iniciar triagem` + `Configurar`.
  - `active` → `Pausar triagem`.
  - `paused` → `Retomar triagem` + `Configurar`.
  - `completed` → não-clicável.
- **Efeito ao mudar.** `liaApi.updateJobVacancy(id, { screeningStatus })` + toast.
- **Rails.** ⚠️ não existe coluna `screening_status` em `ats_api/app/models/job.rb`.
- **Camada de IA.** `app/domains/cv_screening/agents/pipeline_react_agent.py` filtra ações por `screening_status`.
- **Arquivos.** `KanbanJobHeader.tsx:116-205`; `src/types/screening.ts`.
- **Paridade.** 🟡 (front + FastAPI ✅; Rails 🔴).
- **Jira sugerido — LIA-XXX4.** *Adicionar coluna `screening_status` em `ats_api/app/models/job.rb`* — migration, presence validation, sync com FastAPI.

#### A6 / A7 / A8. Chips de meta e prazo

- **O que é.** Sequência horizontal de chips read-only: `Sênior`, `Híbrido`, `CLT`, `Tecnologia`, `São Paulo, São Paulo`, separador `|`, `14 de mai. de 2026`, `1d aberta`, `Atualizada: 16 de mai.`, `Prazo triagem: 21 de mai.`, `Prazo short: 24 de mai.`, `Encerramento: 4 jun.`.
- **Estado.** Vem da API; não-editáveis aqui.
- **Arquivo.** `KanbanJobHeader.tsx:207-277`.
- **Paridade.** 🟡 — Rails tem `deadline` único; precisa de `deadline_screening`, `deadline_shortlist`, `deadline_closing` para paridade.
- **Jira sugerido — LIA-XXX5.** *Migrar Rails para suportar 3 prazos distintos* — `add_column :jobs, :deadline_screening`, `:deadline_shortlist`, `:deadline_closing`; backfill com `deadline` atual; expor no controller.

#### A9. Chip `Sugestões LIA`

- Não visível nas screenshots 8.39/8.41 (lista vazia). Citado para completude do componente.

#### A10. Botão `📄 Relatório`

- **O que é.** Abre o modal/relatório executivo da vaga (`handleShowReport`).
- **Efeito.** Render-only no client; nenhum side-effect server-side a partir deste botão.
- **Rails.** ⚠️ Sem endpoint paritário.
- **Arquivo.** `KanbanJobHeader.tsx:294-298`.
- **Paridade.** 🟡.
- **Jira sugerido — LIA-XXX6.** *Adicionar endpoint Rails `/v1/jobs/:id/report`* paritário ao FastAPI, com cache curto.

#### A11. Botão `↗ Compartilhar`

- **O que é.** Entra em "modo de seleção" — se nenhum candidato está selecionado, marca todos e mostra toast `Modo compartilhamento`. Se há seleção, abre `ShareGestorModal`.
- **Estado.** Stateful; depende de `selectedCandidates`.
- **Arquivo.** `KanbanJobHeader.tsx:299-309`.
- **Paridade.** 🟡 — Rails sem endpoint de share scoped por candidato.
- **Jira sugerido — LIA-XXX7.** *Confirmar entrega de e-mail de compartilhamento via Mailgun* (atualmente client-side abre modal; precisa de auditoria SOX).

### B. Page tabs (screenshot 8.39 — abaixo do header)

#### B1. Tab `Gestão da Vaga (0)`

- **O que é.** Renderiza o kanban + tabela de candidatos. Contador = `allTableCandidates.length`.
- **Arquivo.** `KanbanJobHeader.tsx:315-332`.
- **Paridade.** ✅.

#### B2. Tab `Triagem`

- **O que é.** Visível na screenshot, **não implementada no `KanbanJobHeader.tsx` canônico** (que tem só 2 tabs: management/edit).
- **Paridade.** 🔴 Mockado apenas.
- **Jira sugerido — LIA-XXX8.** *Implementar tab `Triagem` (execução) entre `Gestão da Vaga` e `Configurações`* — deve apresentar o run-time da triagem (fila, candidatos em conversa, paradas por paralização). Sem isso, a screenshot fica divergente do código.

#### B3. Tab `⚙ Configurações` (ativa nesta screenshot)

- **O que é.** Alterna `activeTab='edit'` e mostra `<JobEditTab>`.
- **Arquivo.** `KanbanJobHeader.tsx:333-343`.
- **Paridade.** ✅.

#### B4. Indicador `🔗 Herdado da empresa` (lado direito da barra de tabs)

- **O que é.** Texto + ícone que indica que o pipeline da vaga vem do template company-wide. Quando o pipeline foi customizado, vira `⚠ Pipeline customizado` + botão `Resetar para padrão`.
- **Efeito ao clicar `Resetar para padrão`.** `pipelineInheritance.resetToCompanyDefault()` → POST que descarta override; toast `Pipeline resetado`; recarrega a página.
- **Rails.** ⚠️ Sem paridade — herança vive só no FastAPI.
- **Camada de IA.** `app/domains/cv_screening/agents/pipeline_react_agent.py` lê o override.
- **Arquivo.** `KanbanJobHeader.tsx:344-373`.
- **Paridade.** 🟡.
- **Jira sugerido — LIA-XXX9.** *Expor estado de herança do pipeline no Rails* — coluna `pipeline_overrides_company_default:boolean` em `jobs` + endpoint para reset.

### C. Sidebar esquerda (screenshot 8.39)

Sidebar com **dois grupos** renderizados por `JobEditTab.tsx:111-182`. Cada item mostra ícone, título, descrição e marker de progresso (`CheckCircle2` verde para concluído, `Circle` cinza para pendente).

#### C1. Grupo `CONFIGURAÇÕES DA VAGA`

Itens vêm de `SECTIONS` (`job-edit-tab.constants.ts`).

| Item | Descrição | Marker na screenshot | Arquivo |
|---|---|---|---|
| **C1.1** `Informações Gerais` | Dados principais, perfil e publicação | ✓ verde | `JobInfoGeralSection.tsx` |
| **C1.2** `Pessoas` | Recrutador e gestor | ✓ verde | `JobEditTab.tsx:232-269` |
| **C1.3** `Processo Seletivo` | Etapas do recrutamento | ✓ verde | `JobProcessSection.tsx` |
| **C1.4** `Remuneração` | Salário, bônus e benefícios | ✓ verde | `JobRemuneracaoSection.tsx` |

- **Estado.** O marker verde vem de `jobSectionCompletion(section.fields)` (todos os campos obrigatórios preenchidos).
- **Efeito ao clicar.** `setActiveSection(section.id)` — alterna o painel direito.
- **Rails.** Cada seção bate em `PATCH /v1/jobs/:id` com payload parcial (paridade ✅ para `info-geral`, `pessoas`, `remuneracao`; 🟡 para `processo`).
- **Paridade global do grupo.** ✅.
- **Jira sugerido — LIA-XX10.** *Padronizar nome dos campos do "Processo Seletivo" entre Rails e FastAPI* (`hiring_process` vs `interview_stages`).

#### C2. Grupo `CONFIGURAÇÕES DE TRIAGEM`

Itens vêm de `SCREENING_SECTIONS` (`ScreeningConfigManager.tsx:57-76`).

| Item | Descrição | Marker na screenshot | Arquivo |
|---|---|---|---|
| **C2.1** `Configurações do Roteiro` *(ativo)* | Formato e duração da triagem | ✓ verde (implícito por estar ativo) | `SCMSectionConfiguracoes.tsx` |
| **C2.2** `Descrição do Cargo` | Informações da vaga para a LIA | ✓ verde | `SCMSectionDescricao.tsx` (out of scope) |
| **C2.3** `Perguntas de Triagem` | Blocos WSI de avaliação | ◯ cinza (pendente) | `SCMSectionPerguntas.tsx` (out of scope) |

- **Estado.** Marker vem de `screeningCompletion[section.id]` (`useJobEditTab.ts`).
- **Efeito ao clicar.** `setActiveSection(section.id)` — renderiza `<ScreeningConfigContent>` com a sub-seção.
- **Rails.** ⚠️ Os 3 sub-states (`configDone`, `jdDone`, `questionsDone`) vivem só no FastAPI.
- **Paridade.** 🟡 — falta surfacing em listagens Rails (ex.: relatório de vagas).
- **Jira sugerido — LIA-XX11.** *Expor `screening_completion` por sub-seção no payload Rails da vaga* — para que listagens "/vagas" também mostrem o progresso.

### D. Cabeçalho da sub-seção "Configurações do Roteiro" (screenshot 8.39 — painel direito, topo)

#### D1. Cabeçalho `≡ Configurações do Roteiro` + descrição `Formato e duração da triagem`

- **O que é.** Banner do painel direito. Render por `ScreeningConfigManager.tsx:134-141`.
- **Estado.** Read-only.
- **Paridade.** ✅.

#### D2. Chip `Canal: Chat Web`

- **O que é.** Pílula informativa à direita do cabeçalho que mostra o canal principal vigente. Texto produzido por `getConfigStatusInfo()`.
- **Estado.** Computed a partir de `screeningConfig.screening_channels.primary_channel`.
- **Arquivo.** `ScreeningConfigManager.tsx:143-147`.
- **Paridade.** ✅.

#### D3. Botão `✏️ Editar Configurações`

- **O que é.** Entra em modo edição (`setIsEditingScreeningConfig(true)`). Os 4 blocos abaixo (E, F, G, H, I, J, K) viram editáveis. Antes desse clique, os blocos estão em modo "view".
- **Efeito.** Hidrata todos os state setters `setEditXxx` com os valores atuais de `screeningConfig`.
- **Arquivo.** `ScreeningConfigManager.tsx:148-157`.
- **Paridade.** ✅.

#### D4. Botão `Cancelar` (modo edição)

- **O que é.** Sai do modo edição e reverte todos os `editXxx` para os valores originais de `screeningConfig`. **Não pergunta** se há diff não salvo.
- **Arquivo.** `ScreeningConfigManager.tsx:160-189`.
- **Paridade.** ✅.
- **Jira sugerido — LIA-XX12.** *Avisar diff ao cancelar* — mostrar dialog se houver diff entre `editXxx` e `screeningConfig`.

#### D5. Botão `💾 Salvar` (modo edição)

- **O que é.** Persiste o payload completo via `updateScreeningConfig({...})`.
- **Payload.** `channels_master_enabled`, `channels.{chat_web,whatsapp,phone_pstn,voice_web}`, `screening_channels.{primary_channel, fallback_order}`, `settings.{min_score_preset, response_timeout_hours, max_retries, auto_approval_preset, auto_approval_limit}`, `scheduling.{auto_enabled, min_score_for_auto_preset, calendar_provider, available_hours, available_hours_inherited, interview_duration_min}`.
- **Endpoint.** PUT `/api/backend-proxy/jobs/{id}/screening-config` → FastAPI `/api/v1/jobs/{id}/screening-config`.
- **Side-effects:** `app/domains/cv_screening/agents/pipeline_react_agent.py` recarrega config; `app/domains/cv_screening/services/confidence_policy_service.py` recalcula gates; `app/shared/messaging/broker_interface.py` reconfigura fallback chain.
- **Rails.** ⚠️ Sem paridade.
- **Arquivo.** `ScreeningConfigManager.tsx:190-260`.
- **Paridade.** 🟡.
- **Jira sugerido — LIA-XX13.** *Mirror do payload `screening-config` no Rails* — coluna `screening_config:jsonb` em `jobs` ou tabela `job_screening_configs`.

### E. Bloco `Status da Triagem` (screenshot 8.39)

#### E1. Linha `Status da Triagem` + badge `Configurar`

- **O que é.** Cabeçalho da primeira sub-seção. Mostra o `screeningStatus` resumido com um botão/badge `Configurar` que abre o `ScreeningStatusModal`.
- **Efeito.** Permite ativar/pausar/encerrar/configurar a triagem sem sair da página.
- **Default.** `not_configured` na primeira vez.
- **Rails.** ⚠️ Sem paridade.
- **Camada de IA.** `app/domains/cv_screening/agents/pipeline_react_agent.py` lê o status.
- **Paridade.** 🟡.
- **Jira sugerido — LIA-XX14.** *Unificar o "Status da Triagem" deste card com o badge A5 do header* — hoje são 2 entry points distintos; risco de divergência visual.

### F. Bloco `CANAL DE TRIAGEM` (screenshot 8.39)

> "Escolha o canal principal e a ordem de fallback caso o candidato não responda."

Cada linha é um card de canal com label, descrição, badge de papel (`★ Principal` / `Fallback 1` / `+ Fallback`) e botão `Definir principal` quando aplicável.

#### F1. `Chat Web` — *Chat via portal de carreiras*

- **Estado atual.** `★ Principal` (default).
- **Efeito ao clicar `Definir principal` em outro canal.** Move este para a fila de fallback automaticamente.
- **Persistência.** `screening_channels.primary_channel`.
- **Camada de IA.** `app/shared/messaging/broker_interface.py` (`send(channel='chat_web')`).
- **Paridade.** ✅.

#### F2. `WhatsApp` — *Mensagens via WhatsApp Business*

- **Estado atual.** `Fallback 1`. Botão `Definir principal` à direita.
- **Efeito ao clicar `Definir principal`.** `setEditPrimaryChannel('whatsapp')` + reorganiza `editFallbackOrder` (filtra o novo principal).
- **Persistência.** `screening_channels.primary_channel` + `fallback_order`.
- **Camada de IA.** `app/shared/messaging/broker_interface.py` + WhatsApp BSP (Twilio WA Business ou link wa.me — ver G2).
- **Paridade.** 🟡 (precisa de credencial BSP no Rails para envio real).
- **Jira sugerido — LIA-XX15.** *Adicionar configuração de credencial WhatsApp BSP no Rails* (`company.whatsapp_bsp_credentials_id`).

#### F3. `Ligação (PSTN)` — *Chamada de voz via Twilio*

- **Estado atual.** Card cinza com badge `Não disponível — config. pendente` à direita do label. Sem botão `Definir principal`.
- **Efeito.** Desabilitado até integração Twilio ser configurada na empresa.
- **Camada de IA.** `app/shared/messaging/broker_interface.py` (Twilio PSTN — fallback only).
- **Paridade.** 🔴.
- **Jira sugerido — LIA-XX16.** *Habilitar Ligação (PSTN)* — UI de onboarding de credencial Twilio + verificação número origem + audit log.

#### F4. `Voz no Navegador` — *Conversa por voz via Gemini Live*

- **Estado atual.** Disponível, mas não escolhido. Mostra `+ Fallback` (ainda não está na chain) + `Definir principal`.
- **Persistência.** `screening_channels.primary_channel` / `fallback_order`.
- **Camada de IA.** Gemini Live Audio API.
- **Paridade.** 🟡 (UI ✅; fluxo end-to-end no agente ainda usa Whisper/TTS fallback).

### G. Bloco `CANAIS HABILITADOS` (screenshot 8.39)

#### G0. Master switch `Master ligado`

- **O que é.** Switch único no cabeçalho do bloco. Quando OFF, **desabilita** os 4 toggles abaixo.
- **Estado atual.** ON (rótulo "Master ligado").
- **Persistência.** `channels_master_enabled`.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:259-272`.
- **Paridade.** ✅.

#### G1. Toggle `Chat Web`

- **Estado.** ON. Persiste em `channels.chat_web.enabled`.
- **Paridade.** ✅.

#### G2. Toggle `WhatsApp` + sub-radio `Modo de envio`

- **Estado.** Toggle ON. Sub-radio com 3 opções, exibidas como 3 cards:
  - `Link wa.me` — *Candidato clica e abre conversa* (ativo na screenshot).
  - `Twilio WA Business` — *Envio direto via API*.
  - `Ambos` — *Link + envio Twilio*.
- **Efeito.** Persiste `channels.whatsapp.enabled` e `channels.whatsapp.mode` (`wa_link | twilio_direct | both`).
- **Camada de IA.** `app/shared/messaging/broker_interface.py` escolhe transport.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:291-340`.
- **Paridade.** 🟡 (UI ✅; modo `twilio_direct` precisa de credencial — vide LIA-XX15).

#### G3. Toggle `Ligação (PSTN)` *(Integração pendente)*

- **Estado.** OFF, desabilitado, rótulo cinza.
- **Persistência.** `channels.phone_pstn.enabled` (sempre `false` enquanto integração não estiver pronta).
- **Paridade.** 🔴 — depende de LIA-XX16.

#### G4. Toggle `Voz no Navegador`

- **Estado.** OFF.
- **Persistência.** `channels.voice_web.enabled`.
- **Paridade.** ✅ (UI + agente).

### H. Bloco `CONFIGURAÇÕES` (screenshot 8.41 — topo)

#### H1–H3. `Score Mínimo Aprovação (WSI)` — 3 presets

- **O que é.** Cards-pílula radio com 3 opções:
  - `Rigoroso ≥ 8.4/10` — *Só aprovados automaticamente*.
  - `Recomendado ≥ 7.6/10` — *Inclui revisão manual* (selecionado na screenshot).
  - `Flexível ≥ 6.0/10` — *Todos acima do corte*.
- **Estado default.** `recommended`.
- **Persistência.** `settings.min_score_preset` ∈ `{rigorous, recommended, flexible}`. Convertido para float pelo `presetToScore(...)` no Save (`ScreeningConfigManager.tsx:193-199`).
- **Camada de IA.** `app/services/wsi_compact_pipeline.py` + `app/domains/cv_screening/agents/pipeline_react_agent.py` usam o threshold para aprovação automática; `app/shared/compliance/fairness_guard.py` L1 valida antes de cada decisão.
- **Rails.** ⚠️ Sem paridade.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:386-417`.
- **Paridade.** ✅ (front + agente); 🟡 (Rails).
- **Jira sugerido — LIA-XX17.** *Documentar a escala WSI 0–10 na seção de ajuda da empresa* — recrutadores reportam confusão com a escala antiga 0–100.

#### H4. Select `Timeout Resposta` (default `48h`)

- **O que é.** Quanto tempo esperar antes de tentar novamente. Opções típicas: `12h | 24h | 48h | 72h`.
- **Persistência.** `settings.response_timeout_hours`.
- **Camada de IA.** `app/shared/messaging/broker_interface.py` agenda re-tentativas.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:419-440`.
- **Paridade.** ✅.

#### H5. Select `Re-tentativas` (default `2x`)

- **Persistência.** `settings.max_retries`.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:442-462`.
- **Paridade.** ✅.

### I. Bloco `CONTROLE DE PARALIZAÇÃO` (screenshot 8.41)

#### I1–I3. `Limite de aprovações automáticas` — 3 presets

- **O que é.** Cards-pílula com 3 opções:
  - `Conservador 5 aprovações` — *Revisão humana frequente*.
  - `Recomendado 10 aprovações` — *Equilíbrio automação/supervisão* (selecionado).
  - `Autônomo 25 aprovações` — *Máxima automação*.
- **Default.** `recommended` (10).
- **Persistência.** `settings.auto_approval_preset` + `settings.auto_approval_limit` (helpers `limitToApprovalPreset` / `approvalPresetToLimit` em `useScreeningConfig.ts`).
- **Comportamento.** Ao atingir o limite, `app/domains/cv_screening/services/confidence_policy_service.py` pausa o pipeline e o `screeningStatus` vira `paused`. O recrutador precisa revisar/retomar.
- **Camada de IA.** `app/domains/cv_screening/services/confidence_policy_service.py`; `CompanyHiringPolicy` ⚠️ (referência conceitual — path canônico não auditado neste handoff).
- **Rails.** ⚠️ Sem paridade.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:467-510`.
- **Paridade.** ✅ (front + agente); 🟡 (Rails sem espelho).

#### I4. Aviso amarelo `Triagem pausada — limite atingido` + botão `Retomar`

- **O que é.** Banner exibido quando `screeningStatus='paused'` por estouro do limite. Botão `Retomar` deveria zerar o contador.
- **Estado atual.** **Handler vazio** — clicar não emite nada (`SCMSectionConfiguracoes.tsx:676-682`).
- **Paridade.** 🔴 — quebrado em produção.
- **Jira sugerido — LIA-XX18.** *Implementar handler de "Retomar" da paralização* — PUT que zera contador + remove `paused` + audit log SOX (já registrado como Task #1140 na proposta de follow-ups).

### J. Bloco `PRAZO DA TRIAGEM` (screenshot 8.41)

#### J1. Date picker `Data Limite` (default `22/05/2026`)

- **O que é.** Date input HTML5 (`type="date"`).
- **Persistência.** `deadline_screening` (campo do JD).
- **Comportamento.** `app/domains/cv_screening/agents/pipeline_react_agent.py` usa este prazo para gating; após a data, a vaga não aceita novas triagens automáticas.
- **Rails.** ⚠️ Coluna não existe em `jobs` (paridade depende de LIA-XXX5).
- **Arquivo.** `SCMSectionConfiguracoes.tsx:512-528`.
- **Paridade.** 🟡.
- **Jira sugerido — LIA-XX19.** *Validar `deadline_screening ≥ today + 1 dia`* no front e no agente (hoje aceita data no passado).

### K. Bloco `AGENDAMENTO AUTOMÁTICO` (screenshot 8.41)

#### K0. Master switch (ON na screenshot)

- **Persistência.** `scheduling.auto_enabled`.
- **Efeito.** Quando OFF, esconde K1–K4.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:534-553`.
- **Paridade.** ✅.

#### K1. `Score Mínimo para Agendamento (WSI)` — 3 presets

- **O que é.** Mesmos 3 cards-pílula de H1–H3 (`Rigoroso ≥ 8.4`, `Recomendado ≥ 7.6` [selecionado], `Flexível ≥ 6.0`), porém para a etapa de **agendamento** (não aprovação).
- **Persistência.** `scheduling.min_score_for_auto_preset`.
- **Camada de IA.** `app/domains/interview_intelligence/services/*` agenda só se candidato cruzar este threshold (⚠️ não existe um único ReAct agent "InterviewIntelligenceAgent" — orquestração é por serviços + endpoints REST).
- **Paridade.** ✅ (front + agente); 🟡 (Rails).
- **Jira sugerido — LIA-XX20.** *Reaproveitar componente de presets WSI entre H1–H3 e K1* — hoje há duplicação visual (manter UX, deduplicar código).

#### K2. Select `Calendário` (`Microsoft`)

- **O que é.** Provedor de calendário. Hoje só `Microsoft` (Microsoft Graph).
- **Persistência.** `scheduling.calendar_provider`.
- **Paridade.** 🟡 — sem opção `Google` (Google Calendar não está exposto, embora seja dependência declarada).
- **Cross-ref.** Registrado como Task #1142 na proposta de follow-ups (Google Calendar picker).

#### K3. Campo `Horários` (`9h-18h`) + texto "Conforme config. da empresa"

- **O que é.** Janela de disponibilidade para agendamento.
- **Estado.** Read-only com hint "Conforme config. da empresa" quando `available_hours_inherited === true`. Ao editar, vira input livre e `available_hours_inherited` vai para `false`.
- **Persistência.** `scheduling.available_hours` + `scheduling.available_hours_inherited`.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:627-668`.
- **Paridade.** ✅.

#### K4. Select `Duração` (default `60min`)

- **Opções típicas.** `15min | 30min | 45min | 60min | 90min`.
- **Persistência.** `scheduling.interview_duration_min`.
- **Camada de IA.** `app/domains/interview_intelligence/services/*` agenda blocos do tamanho informado.
- **Arquivo.** `SCMSectionConfiguracoes.tsx:670-695`.
- **Paridade.** ✅.

---

## 6. Cards de Jira sugeridos — lista consolidada por épico

### Épico: Header & Permissões da página

- **LIA-XXX1** — Proteger `Voltar` contra perda de edição em "Configurações do Roteiro".
- **LIA-XXX2** — (reservado para evolução do título).
- **LIA-XXX3** — Bloquear "Encerrar vaga" quando há triagem ativa sem revisão.
- **LIA-XXX6** — Adicionar endpoint Rails `/v1/jobs/:id/report` paritário ao FastAPI.
- **LIA-XXX7** — Auditar entrega do botão "Compartilhar" via Mailgun (SOX).

### Épico: Estado/Status da triagem

- **LIA-XXX4** — Migrar Rails para suportar `screening_status` (`add_column :jobs, :screening_status`).
- **LIA-XX14** — Unificar entry points "Status da Triagem" (badge A5 ↔ card E1) — eliminar divergência.
- **LIA-XX18** — Implementar handler do botão "Retomar" da paralização (atual: handler vazio). **Já registrado como Task #1140.**

### Épico: Prazos & datas

- **LIA-XXX5** — Migration Rails para `deadline_screening`, `deadline_shortlist`, `deadline_closing`.
- **LIA-XX19** — Validar `deadline_screening ≥ hoje+1` no front e no agente.

### Épico: Sidebar & Pipeline

- **LIA-XXX9** — Expor estado de herança do pipeline no Rails (`pipeline_overrides_company_default`) + endpoint de reset.
- **LIA-XX10** — Padronizar nomes de campos do "Processo Seletivo" entre Rails e FastAPI.
- **LIA-XX11** — Expor `screening_completion` por sub-seção no payload Rails.

### Épico: Tabs

- **LIA-XXX8** — Implementar tab `Triagem` (execução) — hoje mockada apenas.

### Épico: Edição da sub-seção (Cancelar/Salvar)

- **LIA-XX12** — Avisar diff ao clicar `Cancelar`.
- **LIA-XX13** — Mirror do payload `screening-config` no Rails (`jsonb` ou tabela dedicada).

### Épico: Canais

- **LIA-XX15** — Adicionar credencial WhatsApp BSP no Rails (`company.whatsapp_bsp_credentials_id`).
- **LIA-XX16** — Habilitar `Ligação (PSTN)` — credencial Twilio + verificação origem + audit.

### Épico: Scoring / WSI

- **LIA-XX17** — Documentar a escala WSI 0–10 (recrutadores reportam confusão vs escala antiga 0–100).

### Épico: Paralização & prazos

- **LIA-XX18** — (mesmo card; veja Estado/Status).

### Épico: Agendamento

- **LIA-XX20** — Reaproveitar componente de presets WSI entre H1–H3 e K1 (deduplicação visual).
- *(Google Calendar picker — já registrado como Task #1142.)*

---

## 7. Riscos & dependências cross-camada

1. **Alterar `Score Mínimo Aprovação (WSI)` (H1–H3) muda comportamento do pipeline de screening em runtime.** Toda mudança deve disparar revalidação de candidatos em fila para evitar fila parada com threshold velho. Avaliar emissão de audit row (`decision_type='screening_threshold_changed'`) — política de retenção a confirmar com Compliance.
2. **Toggle de canal (G1–G4) precisa refletir no `app/shared/messaging/broker_interface.py` em tempo hábil.** Há cache do `screening-config` no FastAPI (TTL exato a confirmar) — risco de mensagem indo para canal desligado durante a janela. Mitigar com invalidação imediata por `company_id` no Save (D5).
3. **`Master switch` (G0) OFF não cancela retries em voo.** Se um candidato já está em conversa via WhatsApp e o recrutador desativa o master, a conversa atual continua; só novos disparos são bloqueados. Documentar e mostrar warning ao desligar.
4. **`Controle de Paralização` (I1–I3) interage com `CompanyHiringPolicy`.** Quando a empresa tem política `confidence-based decision engine` ativa, o limite por vaga ainda é o teto, mas pode ser ultrapassado por delegação CrewAI-style. Risco de duplo-controle.
5. **`Agendamento Automático` (K0–K4) depende de OAuth Microsoft Graph válido na empresa.** Ativar o switch sem OAuth válido pode levar os serviços de `interview_intelligence` a falhar silenciosamente — recomenda-se verificação ativa do token antes de habilitar (implementação a definir).
6. **`Triagem: Configurar` (A5) + `Status da Triagem` (E1) são entry points distintos para o mesmo estado.** Divergência de UI ao mudar via um e refrescar pelo outro. Ver LIA-XX14.
7. **Salvar (D5) PUT sem paridade no Rails.** O `ats_api` não recebe o payload `screening-config`; relatórios de RH que leem só do Rails ficam desatualizados. Crítico para auditoria SOX. Ver LIA-XX13. **Já registrado como Task #1141.**

---

## 8. Cross-refs com follow-ups já abertos

- **Task #1140** — Reativar o botão `Retomar` da triagem pausada (cobre LIA-XX18).
- **Task #1141** — Mostrar o estado da triagem nas listagens da vaga no Rails (cobre LIA-XXX4 + LIA-XX13).
- **Task #1142** — Deixar o recrutador escolher Google Calendar além do Microsoft (cobre LIA-XX20 parcial + K2).

> **Nota de revisão de paridade.** Todas as referências `arquivo:linhas` neste documento foram validadas contra os arquivos reais em `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx`, `plataforma-lia/src/components/jobs/JobEditTab.tsx`, `plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx` e `plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx`. Quando o linhar exato pode mudar entre PRs, as referências apontam para o bloco lógico (não a linha exata) — ver os imports no topo do arquivo para o componente correto.
