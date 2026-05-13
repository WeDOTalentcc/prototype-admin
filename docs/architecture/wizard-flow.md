# Fluxo do Wizard de Criação de Vagas

> Mapa completo do wizard de criação de vagas da Plataforma LIA, com nós do
> LangGraph, decisões de roteamento, stages, integração com `TenantAwareAgentMixin`
> (Task #1043) e índice de arquivos de referência.

A LIA tem **dois wizards convivendo** durante a migração canônica
(`.planning/adrs/ADR-CANONICAL-001-wizard-domain.md`):

| | Wizard A (legacy) | Wizard B (canônico) |
|---|---|---|
| Entry point | `POST /api/v1/wizard/smart-orchestrate` | Chat principal → `MainOrchestrator` → `WizardReActAgent` |
| Implementação | `JobWizardGraph` (StateGraph custom) | `LangGraphReActBase.create_react_agent` |
| Status | CANONICAL-EXEMPT (mantido só para HITL resume) | Piloto canônico do `TenantAwareAgentMixin` (T-B) |
| Persistência | `PostgresSaver` (LangGraph nativo) | `PostgresSaver` |
| Arquivo principal | `app/domains/job_management/agents/job_wizard_graph.py` | `app/domains/job_management/agents/wizard_react_agent.py` |

---

## 0. Como o wizard funciona, do ponto de vista do recrutador

Esta seção é uma **simulação narrada** de uma criação de vaga real. Cada
turno mostra três coisas:

- **👤 O que você (recrutador) digita** no chat;
- **🔧 O que acontece por trás** — quais nós do grafo rodam, qual *intent*
  o LLM classifica, quais *tools* são chamadas, e em que *stage* o wizard
  está;
- **💬 O que a LIA responde** — texto realista, em PT-BR, no estilo
  chat-first.

> Pré-requisitos: você já está logada (ou usando o usuário demo). A LIA
> **já sabe** o nome da empresa, setor, plano, headcount e seu cargo —
> esses dados vêm do JWT via `tenant_context_snippet` (Task #1043) e a
> LIA tem ordem explícita nos prompts para **não** perguntá-los de novo.

### Stage `input-evaluation` — a vaga nasce

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 1 — você abre o wizard                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita:                                                     │
│    "Preciso contratar um engenheiro backend pleno em Python."       │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás (stage = input-evaluation):              │
│    1. intent_classifier  → intent = PROVIDE_INFO                    │
│    2. field_extractor    → {title: "Engenheiro Backend",            │
│                              seniority: "Pleno",                    │
│                              skills_hint: ["Python"]}               │
│    3. tool_router        → 1 tool call: save_job_basics             │
│    4. tool_executor      → grava rascunho no estado                 │
│    5. response_generator → injeta tenant_context_snippet            │
│                            ("Demo Company, setor Tecnologia…") +    │
│                            stage_context da input-evaluation        │
│    6. stage_transition   → required_fields=[title, department];     │
│                            falta department → fica na mesma stage   │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Boa! Anotei aqui: Engenheiro Backend Pleno, com Python.        │
│     Em qual área da Demo Company essa vaga vai ficar — Engenharia, │
│     Dados, Plataforma? E é remoto, híbrido ou presencial?"         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 2 — você completa os dados básicos                            │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita:                                                     │
│    "Engenharia de Plataforma, híbrido em SP, CLT."                  │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás:                                         │
│    1. intent_classifier  → PROVIDE_INFO                             │
│    2. field_extractor    → {department: "Engenharia de Plataforma",│
│                              work_model: "hybrid",                  │
│                              location: "São Paulo",                 │
│                              contract_type: "CLT"}                  │
│    3. tool_router        → save_job_basics (atualiza rascunho)      │
│    4. response_generator → resume e PERGUNTA se pode avançar        │
│    5. stage_transition   → required_fields ✅ → marca avanço para  │
│                            jd-enrichment, mas espera confirmação    │
│                            (interrupt_before pausa o grafo aqui)    │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Fechado. Resumo da vaga até aqui:                              │
│     • Engenheiro Backend Pleno — Python                             │
│     • Engenharia de Plataforma · Híbrido em SP · CLT                │
│     Posso avançar para enriquecer a descrição com sugestões de      │
│     responsabilidades e benefícios?"                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 3 — você confirma o avanço de stage                           │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita:                                                     │
│    "Pode avançar."                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás:                                         │
│    1. intent_classifier  → CONFIRM (entende "pode avançar",        │
│       "vamos", "sim", "bora", "ok"… via _CONFIRMATION_WORDS)        │
│    2. router atalha direto para stage_transition                    │
│    3. stage_transition   → libera o interrupt_before, troca         │
│                            current_stage = "jd-enrichment"          │
│    4. should_continue=True → loop volta para intent_classifier      │
│       já no novo stage                                              │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    (resposta combinada com o turno 4 abaixo, pois o grafo loopa)   │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage `jd-enrichment` — a LIA enriquece a descrição

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 4 — a LIA traz sugestões de mercado (sem você pedir nada)    │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás (stage = jd-enrichment):                 │
│    1. intent_classifier  → ASK_QUESTION (atalho — não tem mensagem  │
│       sua nova; o grafo entrou na nova stage)                       │
│    2. tool_router        → enrich_responsibilities + enrich_        │
│                            benefits + suggest_description           │
│    3. tool_executor      → consulta benchmarks setoriais (8         │
│                            fontes canônicas) + histórico da Demo    │
│                            Company + catálogo de skills             │
│    4. response_generator → renderiza sugestões em formato editável  │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Com base em vagas parecidas no mercado e no que a Demo Company │
│     já contratou, sugiro:                                           │
│                                                                     │
│     📋 Responsabilidades                                            │
│      1. Desenhar e manter APIs Python (FastAPI/Django)              │
│      2. Cuidar de performance, observabilidade e SLOs               │
│      3. Mentorar juniores em revisão de código                      │
│                                                                     │
│     🎁 Benefícios (alinhados ao plano da Demo Company)              │
│      • VR + VA · Plano de saúde Bradesco Top                        │
│      • Home office stipend · 30 dias de férias                      │
│                                                                     │
│     Quer que eu ajuste algo, ou sigo para a faixa salarial?"       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 5 — você ajusta uma sugestão                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita:                                                     │
│    "Tira mentoria de junior. Adiciona experiência com AWS."        │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás:                                         │
│    1. intent_classifier  → MODIFY                                   │
│    2. field_extractor    → diff: remove "mentorar juniores",       │
│                            adiciona "experiência com AWS"           │
│    3. tool_router        → save_job_basics (merge no draft)         │
│    4. response_generator → reapresenta lista com a edição           │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Atualizei. Lista final de responsabilidades:                   │
│      1. Desenhar e manter APIs Python (FastAPI/Django)              │
│      2. Cuidar de performance, observabilidade e SLOs               │
│      3. Experiência sólida com AWS (EC2, RDS, Lambda)               │
│     Pode seguir para salário?"                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage `salary` — a LIA traz benchmarks

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 6 — você confirma e a LIA puxa benchmark salarial             │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita: "Vamos."                                            │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 O que acontece por trás (stage = salary):                        │
│    1. intent_classifier  → CONFIRM → stage_transition avança        │
│    2. (loop) intent_classifier → ASK_QUESTION                       │
│    3. tool_router        → fetch_salary_benchmark                   │
│    4. tool_executor      → consulta Parecer + 8 benchmarks          │
│                            (ABRH, Robert Half, Catho, etc.)         │
│    5. response_generator → exibe faixa com p25/p50/p75              │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Para Backend Pleno em Python, híbrido em SP (CLT), o mercado  │
│     paga (n=312 vagas, últimos 90 dias):                            │
│        p25  R$ 9.500   |  p50  R$ 12.000   |  p75  R$ 14.500       │
│     A Demo Company costuma pagar entre p50 e p60 nesse nível.       │
│     Quer fixar entre R$ 11.000 e R$ 13.500, ou prefere outra       │
│     faixa?"                                                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 7 — você define a faixa                                       │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita: "Pode ser 11 a 13.500."                            │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 Por trás:                                                        │
│    1. intent_classifier  → PROVIDE_INFO                             │
│    2. field_extractor    → {salary_min: 11000, salary_max: 13500,  │
│                              salary_currency: "BRL"}                │
│    3. tool_router        → validate_salary_range                    │
│       (checa se está dentro do p10–p90 do mercado para evitar       │
│        viés econômico — Inegociável #4 / FairnessGuard)             │
│    4. tool_executor      → ✅ válida                                │
│    5. stage_transition   → required ✅ → propõe avanço             │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Salvo: R$ 11.000 a R$ 13.500. Tá dentro do mercado e da       │
│     política da Demo Company. Vamos para as competências?"         │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage `competencies` — skills técnicas e comportamentais

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 8 — a LIA sugere skills (após você confirmar o avanço)        │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 Por trás (stage = competencies):                                 │
│    1. tool_router        → suggest_skills + suggest_behavioral_     │
│                            competencies                             │
│    2. tool_executor      → cruza title+seniority+department com o   │
│                            Skills Ontology Engine                   │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Com base no perfil, sugiro:                                    │
│                                                                     │
│     🛠 Skills técnicas (selecione/edite)                            │
│      [✓] Python · FastAPI · PostgreSQL · Docker · AWS · Git         │
│      [ ] Kafka · Redis · Terraform                                  │
│                                                                     │
│     🤝 Soft skills                                                  │
│      [✓] Comunicação assíncrona · Autonomia · Resolução de         │
│           problemas                                                 │
│                                                                     │
│     Quer adicionar/remover algo, ou seguimos para as perguntas de  │
│     triagem?"                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage `wsi-questions` — perguntas de triagem WSI

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 9 — a LIA gera as 6 perguntas WSI                             │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 Por trás (stage = wsi-questions):                                │
│    1. tool_router        → generate_wsi_questions                   │
│    2. tool_executor      → gera 6 blocos do WSI (técnico,           │
│                            comportamental, motivacional, fit        │
│                            cultural, situacional, anti-bias)        │
│    3. response_generator → renderiza editável                       │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Gerei 6 perguntas de triagem (você pode editar qualquer uma):  │
│      1. [Técnica] Conte uma situação em que você precisou           │
│         escalar uma API Python sob carga…                           │
│      2. [Comportamental] Como você lida com débito técnico…        │
│      3. [Motivacional] O que te atrai numa vaga híbrida…           │
│      4. [Fit cultural] Como você prefere receber feedback…         │
│      5. [Situacional] Imagine um incidente em produção às 2h…       │
│      6. [Anti-bias] Conte um projeto de impacto além do código…    │
│                                                                     │
│     Aprovado? Posso publicar a vaga?"                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage `review/publish` — HITL antes de publicar

```
┌─────────────────────────────────────────────────────────────────────┐
│ TURNO 10 — você aprova a publicação                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 👤 Você digita: "Aprovado, publica."                                │
├─────────────────────────────────────────────────────────────────────┤
│ 🔧 Por trás:                                                        │
│    1. intent_classifier  → CONFIRM                                  │
│    2. ⚠ interrupt_before=["stage_transition"] PAUSA o grafo aqui   │
│       — esse é o ponto HITL antes de qualquer mutação destrutiva    │
│    3. backend libera o interrupt apenas porque o intent é CONFIRM   │
│    4. tool_router        → validate_job_compliance + publish_job    │
│    5. tool_executor      →                                          │
│        a) FairnessGuard L3 audita descrição e perguntas             │
│        b) FactChecker valida benchmarks citados                     │
│        c) ComplianceDomainPrompt grava audit log (SOX 7 anos)       │
│        d) INSERT na tabela job_vacancies (RLS por company_id)       │
│        e) emite evento para o pipeline de Sourcing                  │
│    6. stage_transition   → should_continue=False → END              │
├─────────────────────────────────────────────────────────────────────┤
│ 💬 LIA responde:                                                    │
│    "Pronto! Vaga publicada como #VG-1287.                          │
│     • Pipeline padrão (7 stages) já aplicado                        │
│     • Triagem WSI ativa para novos candidatos                       │
│     • Monitoramento de fairness ligado                              │
│     Quer que eu já comece a sourcing ou prefere revisar antes?"    │
└─────────────────────────────────────────────────────────────────────┘
```

### O que a LIA **não faz** em momento algum

Por ordem explícita nos prompts (regra #8 dos `behavioral_rules`,
adicionada em 8 YAMLs pela Task #1043):

- ❌ Não pergunta seu nome, cargo, e-mail ou telefone (vem do JWT).
- ❌ Não pergunta o nome, setor, plano ou headcount da empresa (vem do
  `tenant_context_snippet`).
- ❌ Não pergunta o `company_id` em momento algum.
- ❌ Não publica a vaga sem o intent `CONFIRM` explícito (HITL via
  `interrupt_before`).
- ❌ Não salva uma faixa salarial fora do mercado sem validar com
  `validate_salary_range`.

### Resumo visual stage-a-stage

```
input-evaluation  ──┐
                    │  você descreve a vaga em linguagem natural
                    │  LIA extrai title, dept, modelo, contrato
                    ▼
jd-enrichment     ──┐
                    │  LIA puxa benchmarks de mercado + histórico
                    │  da empresa e propõe responsabilidades/benefícios
                    ▼
salary            ──┐
                    │  LIA traz p25/p50/p75; você fixa a faixa
                    │  validate_salary_range protege contra viés
                    ▼
competencies      ──┐
                    │  LIA sugere skills via Skills Ontology Engine
                    │  você aceita/edita
                    ▼
wsi-questions     ──┐
                    │  LIA gera 6 perguntas (6 blocos WSI)
                    │  você revisa e aprova
                    ▼
review/publish    ──┐
                    │  HITL: interrupt_before pausa o grafo
                    │  CONFIRM → publica + audit + Fairness L3
                    ▼
                  END (vaga viva no pipeline de sourcing)
```

> **Como cada turno acima mapeia no grafo:** todo o fluxo passa pelos
> mesmos 6 nós (`intent_classifier → field_extractor → tool_router →
> tool_executor → response_generator → stage_transition`) — o que muda
> entre stages é **qual conjunto de tools** o `tool_router` libera (via
> `get_stage_tools(stage)`) e **quais campos** o `field_extractor`
> tenta capturar (via `STAGE_DEFINITIONS[stage].required_fields`). A
> seção 2 abaixo descreve esse mecanismo em detalhe.

---

## 1. Entrada HTTP — wizard A (`/smart-orchestrate`)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Frontend (chat-first, plataforma-lia/Next.js)                             │
│  POST /api/v1/wizard/smart-orchestrate                                     │
│  body: { message, current_stage, collected_data, conversation_history,     │
│          conversation_id?, company_id?, user_id? }                         │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │  Authorization: Bearer <jwt>?  (opcional → dev fallback)
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  app/api/v1/wizard_smart_orchestrator.py:151  smart_orchestrate()          │
│  ─ Depends(get_current_user_or_demo)  ◄── PR-A: sempre amarra usuário ao   │
│                                            CANONICAL_DEMO_UUID em dev      │
│  ─ session_id = conv_id or create_session_id(user.company_id)              │
│  ─ company_id = req.company_id or get_user_company_id(user)                │
│  ─ backend_stage = map_frontend_to_backend_stage(stage)                    │
│  ─ initial_state: JobWizardState  (TypedDict do lia-agents-core)           │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │  await job_wizard_graph.invoke(initial_state)
                 ▼
                ┌──────────────────────────────────────────┐
                │  JobWizardGraph._invoke_langgraph(state) │
                │  (cria StateGraph na 1ª chamada, lazy)   │
                └────────────────┬─────────────────────────┘
                                 │
                                 ▼
```

## 2. StateGraph — nós, edges e roteadores

`app/domains/job_management/agents/job_wizard_graph.py:181  _build_langgraph()`

```
                              ┌─────────────────────────┐
                              │   set_entry_point       │
                              │ "intent_classifier"     │
                              └────────────┬────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────┐
                  │  NODE: intent_classifier                 │
                  │  → classifica WizardIntent (LLM)         │
                  │  app/agents/nodes.py                     │
                  │  Intents possíveis (lia_agents_core):    │
                  │   - START_FROM_SCRATCH / USE_EXISTING /  │
                  │     USE_TEMPLATE                         │
                  │   - HELP / ASK_QUESTION                  │
                  │   - PROVIDE_INFO / MODIFY                │
                  │   - SKIP / GO_BACK / CONFIRM             │
                  └────────────┬─────────────────────────────┘
                               │
              add_conditional_edges("intent_classifier",
                                    route_intent_classifier)
                               │
        ┌──────────────────────┼──────────────────────────┐
        │                      │                          │
        │ START/USE/HELP/ASK   │ PROVIDE_INFO / MODIFY    │ SKIP/GO_BACK/CONFIRM
        ▼                      ▼                          ▼
┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐
│ response_        │  │ NODE: field_        │  │ NODE: stage_         │
│   generator      │  │   extractor         │  │   transition         │
│ (atalho —        │  │ (LLM extrai dados   │  │ (avança/volta etapa) │
│  sem extrair)    │  │  do user_message)   │  │                      │
└────────┬─────────┘  └──────────┬──────────┘  └──────────┬───────────┘
         │                       │                        │
         │           add_edge("field_extractor",          │
         │                    "tool_router")              │
         │                       ▼                        │
         │            ┌───────────────────────┐           │
         │            │ NODE: tool_router     │           │
         │            │ (decide se chama tool │           │
         │            │  baseado em stage +   │           │
         │            │  campos coletados)    │           │
         │            └──────────┬────────────┘           │
         │                       │                        │
         │       add_conditional_edges("tool_router",     │
         │                              route_tool_router)│
         │                       │                        │
         │       ┌───────────────┴────────────────┐       │
         │       │ tool_calls > 0  │  tool_calls = 0      │
         │       ▼                 ▼                      │
         │  ┌─────────────┐  (fall through)               │
         │  │ NODE: tool_ │                               │
         │  │  executor   │ ◄── chama get_stage_tools()   │
         │  │             │     wizard_tool_registry.py   │
         │  └──────┬──────┘                               │
         │         │  add_edge("tool_executor",           │
         │         │           "response_generator")      │
         │         ▼                                      │
         └───►┌──────────────────────────────┐            │
              │ NODE: response_generator     │            │
              │ (LIA gera mensagem PT-BR     │            │
              │  com tenant_context_snippet  │            │
              │  + stage_context + memory)   │            │
              └──────────────┬───────────────┘            │
                             │                            │
                  add_edge("response_generator",          │
                           "stage_transition")            │
                             ▼                            ▼
                    ┌──────────────────────────────────────┐
                    │ NODE: stage_transition               │
                    │ (avalia transition_criteria do       │
                    │  STAGE_DEFINITIONS, define           │
                    │  state["should_continue"])           │
                    │                                      │
                    │  ⚠ interrupt_before=["stage_         │
                    │     transition"]  ◄── HITL: pausa    │
                    │     antes de criar a vaga (CONFIRM)  │
                    └──────────────┬───────────────────────┘
                                   │
                  add_conditional_edges("stage_transition",
                                        route_stage_transition)
                                   │
                  ┌────────────────┴────────────────┐
                  │ should_continue = False         │ should_continue = True
                  ▼                                 ▼
                ┌─────┐                  ┌─────────────────────┐
                │ END │                  │ intent_classifier   │
                └─────┘                  │ (loop — multi-turn) │
                                         └─────────────────────┘
```

## 3. Decisões dos roteadores (linhas exatas)

`job_wizard_graph.py:203-225`

```
route_intent_classifier(state) → str        route_tool_router(state) → str
─────────────────────────────────────        ─────────────────────────────────
intent ∈ {START_FROM_SCRATCH,                len(tool_calls) > 0
          USE_EXISTING, USE_TEMPLATE,           → "tool_executor"
          HELP, ASK_QUESTION}                else
   → "response_generator"                       → "response_generator"
intent ∈ {SKIP, GO_BACK, CONFIRM}
   → "stage_transition"                     route_stage_transition(state) → str
default (PROVIDE_INFO, MODIFY)               ─────────────────────────────────
   → "field_extractor"                       not should_continue → "end" (END)
                                             else                → "continue"
                                                                   (loop intent_classifier)
```

## 4. Stages do wizard (`stage_context.py:STAGE_DEFINITIONS`)

```
┌──────────────────┬───────────────────────────┬──────────────────────────────┐
│ Stage            │ required_fields           │ transition_criteria          │
├──────────────────┼───────────────────────────┼──────────────────────────────┤
│ input-evaluation │ title, department         │ ambos preenchidos            │
│ jd-enrichment    │ title                     │ usuário confirmou sugestões  │
│ salary           │ salary_min, salary_max    │ faixa definida               │
│ competencies     │ skills                    │ ≥ 3 skills                   │
│ wsi-questions    │ screening_questions       │ recrutador aprovou perguntas │
│ review/publish   │ todos os anteriores       │ CONFIRM intent → cria vaga   │
└──────────────────┴───────────────────────────┴──────────────────────────────┘
                          ↓ ordem definida em STAGE_DEFINITIONS["next_stage"]
   input-evaluation → jd-enrichment → salary → competencies → wsi-questions → publish
```

## 5. Onde o tenant context entra (fix da Task #1043)

```
get_current_user_or_demo (auth/dependencies.py:271)
        │  PR-A: company_id = CANONICAL_DEMO_UUID  ◄── era "demo_company"
        ▼
WizardReActAgent.__init__   (TenantAwareAgentMixin, tenant_strict_override=True)
        │
        ▼
_get_tenant_context_snippet (shared/agents/tenant_aware_agent.py:514)
        │  PR-C: se snippet pré-existente OU recém-renderizado contém
        │        "sua empresa" → MissingTenantContextError (fail-LOUD)
        ▼
PromptComposer injeta {tenant_context_snippet} no system prompt
        │  PR-B: 8 YAMLs proíbem LLM de re-perguntar dados do snippet
        ▼
LLM responde sobre a vaga, NÃO sobre identidade da empresa/recrutador
```

## 6. Wizard B canônico (chat principal) — fluxo paralelo

```
WebSocket /chat ─→ MainOrchestrator ─→ CascadedRouter
                                              │
                                              ▼ intent=create_job
                                    ┌─────────────────────┐
                                    │ WizardReActAgent    │
                                    │  (LangGraph React)  │
                                    └──────────┬──────────┘
                                               │
              create_react_agent(LLM, tools, checkpointer=PostgresSaver)
                                               │
                                ┌──────────────┴──────────────┐
                                ▼                             ▼
                        ┌──────────────┐              ┌──────────────┐
                        │ agent_node   │  ←─────────  │  tools_node  │
                        │ (LLM thinks) │              │ (executes)   │
                        └──────┬───────┘              └──────────────┘
                               │
                               ▼ tools_condition: continue | end
                            ┌─────┐
                            │ END │
                            └─────┘
```

## 7. Arquivos de referência (todos relativos a `lia-agent-system/`)

| Arquivo | Papel |
|---|---|
| `app/api/v1/wizard_smart_orchestrator.py` | Endpoint REST (wizard A) |
| `app/domains/job_management/agents/job_wizard_graph.py` | StateGraph custom (wizard A) |
| `app/agents/nodes.py` | Implementação dos 6 nós (wizard A) |
| `app/domains/job_management/agents/stage_context.py` | `STAGE_DEFINITIONS` + `get_stage_context()` |
| `app/domains/job_management/agents/wizard_system_prompt.py` | `build_system_prompt(stage_context, memory)` |
| `app/domains/job_management/agents/wizard_tool_registry.py` | 14 tools `@tool_handler("wizard")` |
| `app/domains/job_management/agents/wizard_react_agent.py` | Wizard canônico B (ReAct) |
| `app/domains/job_creation/graph.py` | `JobCreationGraph` (futuro substituto, ADR-CANONICAL-001 fase 2) |
| `app/domains/job_creation/services/` | `WizardSessionService` (canônico) |
| `app/shared/agents/tenant_aware_agent.py` | Mixin com `_get_tenant_context_snippet` (PR-C) |
| `app/auth/dependencies.py` | `get_current_user_or_demo` (PR-A) |
| `app/auth/models.py` | `User.company_id` + `@validates` (PR-D) |
| `app/prompts/domains/job_management.yaml` | Prompt do wizard B com regra anti-T-E (PR-B) |
| `lia_agents_core.state_machine.JobWizardState` | TypedDict do estado |
| `lia_agents_core.checkpointer.get_checkpointer()` | `PostgresSaver` compartilhado |
| `.planning/adrs/ADR-CANONICAL-001-wizard-domain.md` | Plano de migração A → B |

## 8. Cheat-sheet das 14 tools do wizard

`wizard_tool_registry.py` — todas decoradas `@tool_handler("wizard")`, filtradas
por stage via `get_stage_tools(stage)`:

```
input-evaluation  → search_existing_jobs, suggest_job_template, save_job_basics
jd-enrichment     → enrich_responsibilities, enrich_benefits, suggest_description
salary            → fetch_salary_benchmark, validate_salary_range
competencies      → suggest_skills, suggest_behavioral_competencies
wsi-questions     → generate_wsi_questions, customize_wsi_question
review/publish    → validate_job_compliance, publish_job
```

## TL;DR do que acontece em uma mensagem

1. Frontend manda `POST /smart-orchestrate` com a frase do recrutador.
2. `get_current_user_or_demo` resolve o usuário (e desde Task #1043 o
   `company_id` é UUID válido).
3. `JobWizardGraph.invoke()` entra no `intent_classifier` → LLM rotula o intent.
4. Roteador despacha para `field_extractor` (extrai dados) → `tool_router`
   (decide se chama tool) → opcionalmente `tool_executor` → `response_generator`
   (LIA escreve a resposta com `tenant_context_snippet` injetado).
5. `stage_transition` avalia se os `transition_criteria` da stage atual foram
   batidos. Se sim, marca avanço. **`interrupt_before=["stage_transition"]`** dá
   HITL antes de qualquer mutação destrutiva (publicar vaga).
6. Se `should_continue=True`, loopa para `intent_classifier`; senão termina e
   devolve `SmartOrchestrateResponse` para o frontend.
