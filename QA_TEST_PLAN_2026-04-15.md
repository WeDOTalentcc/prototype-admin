# Plano de Testes Exaustivos — LIA (pré-lançamento cliente)

> Data: 2026-04-15
> Input: QA manual do Paulo reportou "LIA diz que não consegue listar vagas abertas" e "LIA não me leva para outra página".

---

## Achados imediatos (bugs de roteamento)

### 🔴 BUG-17 — LIA não lista vagas abertas

**Onde:** `lia-agent-system/app/orchestrator/config/domain_routing.yaml`

O YAML tem padrões só para **criar/editar/pausar/publicar vaga** + `\bvaga\b` genérico. Faltam:
- `listar?\s+\w*\s*vagas?`
- `minhas\s+vagas?`
- `vagas?\s+(abertas?|ativas?|em\s+aberto)`
- `quais\s+vagas?`
- `ver\s+vagas?`

Com `\bvaga\b` matching genérico, o roteador manda para o **`job_wizard`** (criação) — que não tem `list_jobs` no tool_registry. O agente responde "não consigo".

**Tool já existe:** `list_jobs` em `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py:105` — executa SQL e retorna lista ordenada por prioridade. Só falta o roteador mandar pra ele.

**Fix rápido:** adicionar ~5 patterns ao `domain_routing.yaml` (novo sub-domínio `jobs_portfolio` ou patterns adicionais no `job_management` **priorizados** antes de "criar"). Para o MVP, patterns novos no `job_management` e mudança no agent default para rotas de leitura.

---

### 🔴 BUG-18 — LIA não tem tool de navegação

**Onde:** `lia-agent-system/app/orchestrator/navigation_intent.py` + `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx:151`

A plataforma **não tem tool `navigate_to_page`** no tool_registry. O que existe é um `NavigationIntentDetector` que:
1. Analisa a mensagem com keyword matching
2. Retorna `(page, confidence, hint)` com threshold backend 0.50 e frontend **0.85**
3. Emite evento `lia:navigation-hint` → mostra **card sugestão opcional** ("Quer que eu abra Vagas?")

Problemas:
- **Perguntas** (`"me leva pra vagas?"`) entram na regex `_INTERROGATIVE_PREFIXES` que **reduz a confidence** — dificilmente atinge 0.85
- Não existe forma da LIA, por si só, **executar** a navegação (só sugerir)
- O LLM da LIA (ReAct agent) não recebe nenhuma tool `navigate_to(page)` — daí ela responde "não consigo"

**Fixes possíveis:**
- **Curto prazo:** reduzir threshold FE para 0.70 + ajustar lógica de interrogativas (se a pergunta é "me leva pra X", reforçar confidence em vez de reduzir)
- **Médio prazo:** criar tool `navigate_to_page` no tool_registry + agente despacha via evento (resposta LLM conhece a ação)

---

## Inventário de capabilities da LIA

**76 tools registradas** em `app/tools/tool_registry_metadata.yaml` — source of truth.

### Capabilities agrupadas por domínio (top 50 user-facing)

| # | Domain | Tool | Prompt exemplo (PT-BR) | Scope | Resposta esperada |
|---|---|---|---|---|---|
| 1 | job-wizard | `create_job` | "Crie uma vaga de dev backend sênior" | JOB_TABLE | Wizard abre com fields pré-preenchidos |
| 2 | job-wizard | `generate_enriched_jd` | "Gere a JD da vaga que acabei de criar" | JOB_TABLE | Texto de JD estruturada |
| 3 | job-wizard | `get_intelligent_salary` | "Qual o salário de mercado pra dev sênior em SP?" | JOB_TABLE | Faixa salarial + fontes |
| 4 | job-wizard | `get_intelligent_skills` | "Que skills devo exigir pra um PM sênior?" | JOB_TABLE | Lista de skills + adjacências |
| 5 | job-wizard | `search_salary_benchmark` | "Busca benchmark salarial pra designer UX" | JOB_TABLE | Dados de mercado |
| 6 | job-wizard | `validate_job_fields` | "Valida os campos da vaga antes de publicar" | JOB_TABLE | Lista de faltantes/OK |
| 7 | job-wizard | `save_job_draft` | "Salva como rascunho essa vaga" | JOB_TABLE | Confirmação + draft_id |
| 8 | jobs-mgmt | `list_jobs` ⚠️ **BUG-17** | "Lista minhas vagas abertas" | JOB_TABLE | Tabela/card com vagas |
| 9 | jobs-mgmt | `search_jobs` ⚠️ **BUG-17** | "Busca vagas de TI ativas" | JOB_TABLE | Lista filtrada |
| 10 | jobs-mgmt | `get_job_details` | "Me mostra os detalhes da vaga V0001" | JOB_TABLE | Card detalhado |
| 11 | jobs-mgmt | `get_pipeline_stats` | "Como está o funil da vaga V0001?" | JOB_TABLE | Stats por stage |
| 12 | jobs-mgmt | `get_vacancy_funnel` | "Mostra o funil da vaga atual" | IN_JOB | Dados do funil |
| 13 | jobs-mgmt | `publish_job` | "Publica essa vaga" | JOB_TABLE | Confirmação + URL |
| 14 | jobs-mgmt | `update_job` | "Atualiza o salário da vaga V0001 para R$ 15k" | JOB_TABLE | Confirmação + diff |
| 15 | jobs-mgmt | `publish_to_job_board` | "Publica essa vaga no LinkedIn e Indeed" | IN_JOB | Links + tracking |
| 16 | jobs-mgmt | `pause_vacancy` | "Pausa a vaga V0001 por 15 dias" | IN_JOB | Confirmação |
| 17 | jobs-mgmt | `cancel_vacancy` | "Cancela a vaga V0001" | IN_JOB | Confirmação + motivo |
| 18 | pipeline | `update_candidate_stage` | "Move o candidato X para Entrevista" | IN_JOB | Confirmação stage |
| 19 | pipeline | `bulk_update_candidates_stage` | "Move todos da triagem para entrevista" | IN_JOB | Contador + lista |
| 20 | pipeline | `add_candidate_to_vacancy` | "Adiciona a Maria Silva na vaga V0001" | TALENT_FUNNEL | Confirmação |
| 21 | pipeline | `reject_candidate` | "Rejeita o João Pedro com motivo 'não se encaixa'" | IN_JOB | Confirmação |
| 22 | pipeline | `shortlist_candidate` | "Adiciona Maria à shortlist" | TALENT_FUNNEL | Confirmação |
| 23 | pipeline | `hide_candidate` | "Esconde o candidato X do pipeline" | IN_JOB | Confirmação |
| 24 | pipeline | `add_to_list` | "Adiciona Maria à lista 'Top Talents'" | TALENT_FUNNEL | Confirmação |
| 25 | talent | `search_candidates` | "Busca candidatos com Python e AWS" | TALENT_FUNNEL | Lista + scores |
| 26 | talent | `get_candidate_details` | "Me mostra o perfil da Maria Silva" | TALENT_FUNNEL | Card detalhado |
| 27 | talent | `get_candidate_stats` | "Quantos candidatos ativos eu tenho?" | TALENT_FUNNEL | Stats agregados |
| 28 | talent | `export_candidates` | "Exporta pra Excel os candidatos da vaga V0001" | TALENT_FUNNEL | Link download |
| 29 | sourcing | `create_sourcing_agent` | "Cria um agente sourcing pra vaga V0001" | GLOBAL | Confirmação + agent_id |
| 30 | sourcing | `calibrate_sourcing_agent` | "Calibra o agente sourcing X" | GLOBAL | Modal calibração |
| 31 | sourcing | `get_agent_status` | "Status do agente sourcing X" | GLOBAL | Stats do agente |
| 32 | sourcing | `run_multi_strategy_search` | "Roda busca multi-estratégia pra vaga V0001" | TALENT_FUNNEL | 4 listas (direta/adjacente/silver/reeng) |
| 33 | sourcing | `search_candidates_pearch` | "Busca na Pearch candidatos de Python" | TALENT_FUNNEL | Lista + créditos consumidos |
| 34 | talent-pool | `create_talent_pool` | "Cria pool 'Top Devs Python'" | TALENT_FUNNEL | Confirmação |
| 35 | talent-pool | `list_talent_pools` | "Lista meus pools de talento" | TALENT_FUNNEL | Lista |
| 36 | talent-pool | `add_to_talent_pool` | "Adiciona Maria ao pool Top Devs" | TALENT_FUNNEL | Confirmação |
| 37 | talent-pool | `get_pool_candidates` | "Quem está no pool Top Devs?" | TALENT_FUNNEL | Lista candidatos |
| 38 | talent-pool | `move_pool_to_job` | "Move candidatos do pool pra vaga V0001" | TALENT_FUNNEL | Confirmação + count |
| 39 | digital-twin | `create_digital_twin` | "Cria um Gêmeo Digital do meu melhor recrutador" | GLOBAL | Confirmação |
| 40 | digital-twin | `list_digital_twins` | "Lista meus Gêmeos Digitais" | GLOBAL | Lista |
| 41 | digital-twin | `evaluate_with_twin` | "Avalia a Maria com meu Gêmeo Ana" | IN_JOB | Avaliação + score |
| 42 | campaign | `create_recruitment_campaign` | "Cria campanha de recrutamento pra vaga V0001" | GLOBAL | Confirmação |
| 43 | campaign | `get_campaign_progress` | "Como está a campanha X?" | GLOBAL | Progress |
| 44 | campaign | `advance_campaign_stage` | "Avança pro próximo estágio da campanha X" | GLOBAL | Confirmação |
| 45 | offer | `create_offer_letter` | "Gera carta de oferta pra Maria, vaga V0001" | IN_JOB | PDF/texto |
| 46 | offer | `confirm_placement` | "Confirma contratação da Maria" | IN_JOB | Confirmação |
| 47 | comms | `send_email` | "Envia email de parabéns pra Maria" | TALENT_FUNNEL | Confirmação |
| 48 | comms | `send_whatsapp` | "Manda WhatsApp pro João com status" | TALENT_FUNNEL | Confirmação |
| 49 | analytics | `generate_report` | "Gera relatório de vagas fechadas no mês" | GLOBAL | URL/PDF |
| 50 | analytics | `schedule_report` | "Agenda esse relatório pra toda segunda" | GLOBAL | Confirmação |
| 51 | wsi | `wsi_screening` | "Inicia WSI pra Maria Silva" | IN_JOB | Link/iniciado |
| 52 | wsi | `analyze_interview_recording` | "Analisa a gravação da entrevista do João" | IN_JOB | Análise completa |
| 53 | wsi | `detect_interview_bias` | "Detecta viés na entrevista do João" | IN_JOB | Relatório viés |
| 54 | wsi | `generate_interview_opinion` | "Gera parecer estratégico pro João" | IN_JOB | Parecer |
| 55 | wsi | `compare_interview_performance` | "Compara performance do João vs outros" | IN_JOB | Ranking |
| 56 | skills | `infer_related_skills` | "Que skills são relacionadas a Kubernetes?" | GLOBAL | Grafo skills |
| 57 | skills | `analyze_skill_gaps` | "Analisa gap de skills da Maria vs vaga" | TALENT_FUNNEL | Relatório gaps |
| 58 | skills | `match_internal_candidates` | "Quais funcionários combinam com a vaga V0001?" | TALENT_FUNNEL | Lista internos |
| 59 | planning | `forecast_hiring_needs` | "Projete minha necessidade de contratação pros próximos 6 meses" | GLOBAL | Previsão |
| 60 | nurture | `create_nurture_sequence` | "Cria nurture pra pool Top Devs" | TALENT_FUNNEL | Confirmação |
| 61 | nurture | `get_engagement_metrics` | "Qual engajamento do nurture X?" | TALENT_FUNNEL | Stats |
| 62 | nurture | `suggest_reengagement` | "Quem devo re-engajar hoje?" | TALENT_FUNNEL | Lista |
| 63 | market | `get_market_intelligence` | "Mercado de dev Python em SP hoje" | GLOBAL | Insights mercado |
| 64 | proactive | `get_proactive_alerts` | "Quais alertas eu tenho hoje?" | GLOBAL | Alertas |
| 65 | autonomous | `get_autonomous_actions` | "Que ações automáticas você executou?" | GLOBAL | Lista ações |
| 66 | autonomous | `confirm_autonomous_action` | "Confirma a ação pendente X" | GLOBAL | Confirmação |
| 67 | autonomous | `reject_autonomous_action` | "Rejeita a ação pendente X" | GLOBAL | Confirmação |
| 68 | learning | `detect_pending_decisions` | "O que precisa de decisão minha?" | GLOBAL | Lista |
| 69 | learning | `get_learning_insights` | "Que padrões você aprendeu das últimas contratações?" | GLOBAL | Insights |
| 70 | learning | `record_hiring_outcome` | "Registra outcome 'contratado' pra Maria, vaga V0001" | IN_JOB | Confirmação |

**Capabilities ausentes descobertas:**
- 🔴 `navigate_to_page` — LIA não sabe navegar (BUG-18)
- 🟠 `get_tasks_list` / `get_briefing` — tarefas e briefing só têm endpoint REST, sem tool
- 🟠 `open_agent_studio` / `open_settings` — ações de UI sem tool

---

## Framework de avaliação existente (já implementado)

### `tests/eval/` — pronto pra usar

```
tests/eval/
├── config.yaml                              # configuração geral
├── rubrics/
│   ├── chat.yaml                           # LLM-as-judge: understanding/helpfulness/proactivity/accuracy/tone (0-3)
│   ├── sourcing.yaml                       # relevance/fairness/actionability
│   └── communication.yaml
├── datasets/
│   ├── sourcing/scenarios.yaml             # 10 cenários (happy/edge/failure/adversarial)
│   ├── screening/scenarios.yaml
│   ├── integration/handoff_scenarios.yaml
│   └── adversarial/attack_scenarios.yaml
└── runner.py                               # python -m tests.eval.runner --suite all
```

**Judge:** Claude Sonnet 4, threshold pass=2.0, excellence=2.7.

**Dimensões avaliadas no chat (pesos):**
- Understanding (0.25) — entendeu o pedido?
- Helpfulness (0.25) — resolve o problema?
- Proactivity (0.20) — oferece insights além do pedido?
- Accuracy (0.20) — dados corretos, sem hallucination?
- Tone (0.10) — português BR, profissional, consultivo?

---

## Proposta de suíte de testes exaustivos

### Camada 1 — **Functional Playwright** (cobertura: chamada de tool + 200 OK)

**Arquivo novo:** `plataforma-lia/e2e/tests/lia-capabilities-suite.spec.ts`

- 1 teste por capability (70 testes)
- Cada teste: envia prompt → espera `POST /api/backend-proxy/chat/message` com 200 OK + `content.length > 0` + (quando aplicável) UI card correto
- Labels: `@domain:jobs`, `@domain:pipeline`, etc para filtrar no CLI
- Reporter HTML com PASS/FAIL/SKIP por tag
- Paralelismo: serializar por conversation_id (prompts independentes)

**Critérios PASS:**
- Resposta recebida
- Tool esperada chamada (inspecionar `message_metadata.intent` e `entities`)
- Zero erro 5xx
- Resposta tem estrutura válida (texto OU card)

### Camada 2 — **Quality Eval** (reaproveitar `tests/eval/`)

**Novo arquivo:** `lia-agent-system/tests/eval/datasets/lia_capabilities/scenarios.yaml`

- Mesmos 70 prompts da Camada 1
- `expected.must_include` / `must_not_include` por prompt
- `rubric` referencia `rubrics/chat.yaml`
- `threshold: 7` (0-3 × 5 dim × pesos ≈ 2.0 média)
- Roda com `python -m tests.eval.runner --suite lia-capabilities`

**Critérios PASS:**
- Score médio ≥ 2.0 nas 5 dimensões
- `must_include` presente
- `must_not_include` ausente (PII, bias, hallucination)

### Camada 3 — **Jornadas E2E** (fluxos multi-turno)

**Arquivo novo:** `plataforma-lia/e2e/tests/lia-journeys.spec.ts`

5 jornadas críticas pré-lançamento:

**J1 — Criar vaga completa:**
`"Crie vaga dev backend Python sênior SP"` → wizard abre → `"salva como rascunho"` → `"publica no LinkedIn"` → validar card de confirmação + link

**J2 — Mover candidato pelo pipeline:**
Estar em `/pt/vagas/V0001` → `"lista candidatos em triagem"` → `"move o primeiro para entrevista"` → validar mudança de stage + toast

**J3 — Gerar relatório:**
`"gera relatório de vagas fechadas no último mês"` → esperar resposta com link/pdf → abrir URL → validar conteúdo

**J4 — Busca candidatos com quality gate:**
`"busca candidatos para dev Python sênior SP, tem que ter K8s"` → validar: ≥1 resultado, sem PII sensível (CPF/idade/gênero), resposta usa score

**J5 — Sourcing agent ciclo completo:**
`"cria agente sourcing pra vaga V0001"` → `"calibra"` → aprovar 3 candidatos → `"status"` → validar calibration_v incrementa

### Camada 4 — **Smoke anti-regressão** (já feita)

- `qa-smoke-2026-04-15.spec.ts` (8 cenários, commit `4d254e2c`)
- Roda em cada CI run pra garantir que fixes não voltaram

---

## O que rodar ANTES do cliente receber

**Ordem recomendada:**

1. **Fix BUG-17 + BUG-18** (vagas + navegação) — sem isso, 20% das capabilities falham por routing
2. **Camada 1 (Playwright funcional)** — ~30-60 min de execução, mostra % de capabilities funcionando
3. **Camada 3 (Jornadas)** — ~15 min, garante que fluxos críticos de demo funcionam
4. **Camada 2 (Quality eval)** — ~30 min, roda judge-LLM, mostra score por capability

**Gate do lançamento:**
- Camada 1 ≥ 90% PASS (destaca capabilities quebradas)
- Camada 3 = 100% PASS (jornadas críticas imperdíveis)
- Camada 2 ≥ 70% com score médio ≥ 2.0 (qualidade das respostas)
- Zero P0 na Smoke anti-regressão

---

## Cronograma sugerido

| Fase | Tempo estimado | Output |
|---|---|---|
| 1. Fix BUG-17 (routing list_jobs) | 30 min | PR |
| 2. Fix BUG-18 (navigate tool) | 1-2h | PR |
| 3. Gerar suite Playwright Camada 1 (70 testes) | 2h | `lia-capabilities-suite.spec.ts` |
| 4. Gerar dataset Camada 2 reaproveitando rubrics | 1h | `datasets/lia_capabilities/scenarios.yaml` |
| 5. Gerar Jornadas Camada 3 | 1h | `lia-journeys.spec.ts` |
| 6. Rodar tudo contra Replit | 1h | Relatório HTML + JSON |
| **Total** | **~6-7h** | **Go/No-Go sólido** |

---

## Próximos passos

1. Você decide escopo e urgência (ver `AskUserQuestion` na próxima mensagem)
2. Com aprovação do escopo, gero os testes em ordem (smoke → jornadas → capabilities)
3. Rodo contra Replit (branch `fix/qa-2026-04-15` + fix BUG-17/18)
4. Gero **`QA_RELEASE_GATE_REPORT.md`** com PASS/FAIL por capability, screenshots das falhas, ranking de severidade
