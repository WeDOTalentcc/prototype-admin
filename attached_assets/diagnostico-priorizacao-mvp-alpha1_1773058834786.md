# DIAGNÓSTICO DE PRIORIZAÇÃO — MVP ALPHA 1

**Data:** 25/fev/2026 (rev.5: 26/fev/2026 — correção de incoerências e visão consolidada)
**Fonte Jira:** Projeto WT, label `lia-mvp` — pós-limpeza: ~172 work items (era 240)
**Fonte Doc:** `docs/mvp-alpha-scenarios.md` v2.9 (168 cards planejados + 4 cards saturação)

---

## 1. RESUMO EXECUTIVO

### Snapshot — Visão Consolidada (rev.5)

#### Produto (cards do doc com correspondência direta no Jira)

| Indicador | Valor |
|-----------|-------|
| Cards planejados no doc MVP Alpha | **172** (168 original + 4 saturação) |
| Cards com label `lia-mvp` no Jira (pré-limpeza) | **88** |
| Cards do doc mapeados no Jira | **92** |
| Desses: ✅ Done | **26** (28%) |
| Desses: 🔍 QA / 📋 Code Review | **14** (15%) |
| Desses: 🔨 In Progress | **5** (5%) |
| Desses: 🏷️ MVP P / 📝 TO DO (prontos p/ iniciar) | **38** (41%) |
| Desses: 📦 Backlog / 🔄 Revisão | **9** (10%) |

#### IA (cards do doc com equivalentes indiretos no Jira — rev.4)

| Indicador | Valor |
|-----------|-------|
| Cards IA planejados no doc | **63** (478 pts) |
| Cards IA com trabalho significativo via equivalentes Jira | **~25** (39%) — 8 Done, ~10 em andamento, ~7 parciais |
| Cards IA realmente novos (sem trabalho no Jira) | **~38** (~300 pts) |
| Desses novos, com código de referência no protótipo | **~70%** (~27 cards) |

#### Resposta: quantos cards precisam ser trabalhados?

| Situação | Cards | Pts aprox. |
|----------|:-----:|:----------:|
| ✅ Já concluídos (Done) — produto + IA equiv. | **~34** | ~200 |
| 🔄 Em andamento (QA/InProg/CR) — produto + IA equiv. | **~29** | ~170 |
| 🏷️ Prontos p/ iniciar (MVP P/TO DO) | **~38** | ~200 |
| ❌ **Precisam ser trabalhados do zero** | **~71** | ~440 |
| **Total** | **172** | ~1010 |

> **Resumo:** Dos 172 cards planejados, **~63 (37%) já têm algum grau de avanço** (Done/QA/InProg). **~38 estão priorizados e prontos** para iniciar. **~71 cards precisam de trabalho novo**, mas desses, ~27 têm código de referência no protótipo Replit.

#### Limpeza e organização (rev.3)

| Indicador | Valor |
|-----------|-------|
| Cards deletados do Jira (limpeza rev.3) | **68** (45 nesta sessão + 23 já não existiam) |
| Cards mantidos no backlog com label | **27** (23 WDT + 4 saturação) |
| Cards extras no Jira sem correspondência no doc | **~104** (pós-limpeza) |
| Gap: Cards do doc sem card próprio no Jira | **~80** (IA ~63 + Pipeline 10 + gaps 7) |

### Conclusão

O Jira cobre diretamente **92 dos 172 cards planejados** (53%). Os ~80 cards sem card próprio são majoritariamente IA (PREP/INF/SRV/AGT/AUT/TRV/INT-AI = ~63 cards) e Pipeline (PIP-001~010 = 10 cards). Porém, o cruzamento rev.4 revelou que **~25 desses cards IA têm trabalho significativo via cards equivalentes** no Jira (INT-LLM, INT-MSG, INT-TWI, etc.), reduzindo o esforço real.

**Limpeza rev.3 (26/fev/2026):** Removidos **68 cards** do Jira que eram duplicados, obsoletos ou fora do escopo Alpha 1 (Wizard Steps, APIs Rails, Backend IA duplicados dos SRV, Stripe/Billing, HubSpot/CRM, Privacy Tools, Infra LLM avançada, avulsos P3). 23 cards WDT mantidos com label `otimizacao-de-busca` (Alpha 2+). 4 cards de saturação de pipeline (WT-405~408) promovidos para Alpha 1 com prioridade alta.

**Priorização rev.2 (MoSCoW) — com esforço real (rev.5):**

| Nível | Cards Total | Já avançados | Trabalho novo | Pts novos | Descrição |
|-------|:----------:|:------------:|:-------------:|:---------:|-----------|
| P0 — Must Have | **17** | **3** (1 QA, 1 CR, 1 Revisão) | **~14** | **~105** | Caminho crítico + WhatsApp |
| P1 — Should Have | **32** | **10** (3 QA, 3 InProg, 3 Revisão, 1 TO DO) | **~22** | **~130** | Scoring, gates, agendamento, templates, MS Graph |
| P2 — Could Have | **~72** | **~25** (IA equiv. Done/QA/MVP P) | **~38** | **~300** | IA completa (portar protótipo) + refinamentos |
| P3 — Won't Have | **~50** | — | — | — | Config Admin, WorkOS, WDT (mantidos); Wizard Conversacional/Rails/Stripe/HubSpot/Privacy/LLM (deletados) |
| **Total P0+P1+P2** | **121** | **~38** | **~74** | **~535** | |

> **Leitura:** Dos 121 cards P0+P1+P2, **~38 já estão em andamento** (QA/InProg/CR/Revisão) e precisam apenas ser validados ou completados. O **trabalho genuinamente novo é ~74 cards / ~535 pts**. Dos 74 novos, ~27 têm código de referência no protótipo Replit.

**Implicação para negociação:** O doc planeja 172 cards em 3 semanas (~57/semana). Dos 121 cards de trabalho (P0+P1+P2), **~38 já estão avançados** e ~74 precisam de trabalho novo (~535 pts). Somando os 26 Done + 38 avançados = **~64 cards com progresso**. **Ações imediatas:** criar PUB-001 e INT-AI-007 no Jira (P0 sem card), definir provider WhatsApp, replanejamento dos deadlines Feb 20 atrasados.

---

## 2. MAPA JIRA × DOC MVP ALPHA — POR ÉPICO

> **Legenda de Status Jira:**
> ✅ Done | 🔍 QA | 🔨 In Progress | 📋 Code Review | 🏷️ MVP P (priorizado, não iniciado) | 📦 Backlog | 🔄 Revisão pré-MVP | 📝 TO DO

---

### É1 — Login + Dashboard de Vagas (4 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| VAG-001 | Tabela de Vagas | WT-283 / WT-981 | ✅ Done | Duplicado no Jira (2 tickets) |
| VAG-002 | Tabs de Status | WT-284 / WT-982 | ✅ Done | Duplicado no Jira |
| VAG-007 | Contador Candidatos | WT-289 | ✅ Done | — |
| VAG-008 | Navegação Vaga→Kanban | WT-290 | ✅ Done | — |

**Resultado: 4/4 Done ✅ — Épico completo**

---

### É2 — Editar Vaga (3 cards no doc + 1 Pós-MVP)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| WIZ-008 | Form Edição Completa | WT-904 | 🔍 QA | — |
| VAG-003 | Menu Ações Vaga | WT-285 / WT-983 | ✅ Done | Duplicado |
| VAG-004 | Pausar/Ativar Vaga | WT-286 / WT-984 | ✅ Done | Duplicado |
| NOT-007 | Notif. Teams | WT-1465 | ✅ Criado | Pós-MVP no doc |

**Resultado: 2/3 Done, 1 em QA — quase completo**

---

### É3 — Roteiro WSI (7 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| WSI-001 | Motor Geração Perguntas | WT-911 | 🔍 QA | Core do sistema |
| WSI-002 | Blocos Metodologia WSI | WT-912 | 🔍 QA | — |
| WSI-003 | Preview de Perguntas | WT-913 | 🔍 QA | — |
| WSI-004 | Edição Manual Perguntas | WT-914 | 📦 Backlog | **REMOVIDO** do escopo |
| WSI-005 | Aprovação Perguntas | WT-915 | 🔍 QA | — |
| WSI-006 | Edição via Prompt | WT-1466 | ✅ Criado | Não existe no Jira |
| WIZ-012 | Estágio Perguntas WSI | WT-1467 | ✅ Criado | Não existe no Jira |
| WIZ-013 | Quality Gates WSI | WT-1468 | ✅ Criado | Não existe no Jira |

**Resultado: 4 em QA, 1 REMOVIDO, 2 sem card Jira**
**Ação necessária:** Criar WIZ-012 e WIZ-013 no Jira ou confirmar que estão cobertos por WSI-001~005.

---

### É4 — Mapeamento de Candidatos (16 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| MAP-001 | Lista Candidatos Base | WT-905 | ✅ Done | — |
| MAP-002 | Busca Semântica ES+PGV+WRF | WT-906 | ✅ Done | — |
| MAP-003 | Filtros Avançados | WT-907 | 🏷️ MVP P | — |
| MAP-004 | Adicionar Cand. à Vaga | WT-908 | 🏷️ MVP P | — |
| MAP-005 | Matching Score IA | WT-909 | 🏷️ MVP P | — |
| MAP-006 | Sugestões Proativas LIA | WT-910 | ✅ Done | — |
| MAP-007 | Endpoint Busca Paginada | WT-1280 | 🏷️ MVP P | Identificado na screenshot |
| MAP-008 | Paginação On-Demand | WT-1456 | ✅ Criado | WT-1456 |
| MAP-009 | Exclusão IDs no ES | WT-1457 | ✅ Criado | WT-1457 |
| MAP-010 | Exclusão IDs no PGV | WT-1458 | ✅ Criado | WT-1458 |
| MAP-011 | API Feedback Like/Dislike | WT-1459 | ✅ Criado | WT-1459 |
| MAP-012 | Componente Like/Dislike | WT-1460 | ✅ Criado | WT-1460 |
| MAP-013 | Remover Ord. por Ranking | WT-1461 | ✅ Criado | WT-1461 |
| INT-APY-001 | Config Apify | WT-1230 | 🏷️ MVP P | Feb 27 deadline |
| INT-APY-002 | LinkedIn Scraper | WT-1231 | 🏷️ MVP P | Feb 27 deadline |
| INT-APY-003 | Integr. Sourcing Agent | WT-1232 | 🏷️ MVP P | Feb 27 deadline |

**Resultado: 3 Done, 7 MVP P, 6 sem card Jira**
**Ação necessária:** MAP-008~013 são cards de UI/backend complementares. Avaliar se são cobertos implicitamente pelo MAP-002/003 ou se precisam ser criados.

---

### É5 — Pipeline Kanban + Preview (18 cards Kanban/Tab/Preview no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| KAN-001 | Estrutura Kanban 4 Col. | WT-963 | ✅ Done | — |
| KAN-002 | Card de Candidato | WT-964 | ✅ Done | — |
| KAN-003 | Drag-and-Drop | WT-965 | ✅ Done | — |
| KAN-004 | Menu Ações Card | WT-966 | ✅ Done | — |
| KAN-005 | Ícones Ação Rápida | WT-967 | 📦 Backlog | **OBSOLETO** |
| KAN-006 | Badge Score WSI | WT-968 | 📋 Code Review | — |
| KAN-007 | Filtro por Status | WT-969 | ✅ Done | — |
| KAN-008 | Busca por Nome | WT-970 | ✅ Done | — |
| KAN-011 | Triagem em Lote | WT-1462 | ✅ Criado | WT-1462 |
| TAB-001 | Tabela Candidatos | WT-971 | ✅ Done | — |
| TAB-002 | Colunas Ordenáveis | WT-972 | 🏷️ MVP P | — |
| TAB-003 | Seleção Múltipla | WT-973 | ✅ Done | — |
| TAB-004 | Paginação | WT-974 | ✅ Done | — |
| TAB-005 | Ações em Massa/Barra | WT-975 | ✅ Done | — |
| PRV-001 | Preview Lateral Cand. | WT-976 | 🏷️ MVP P | — |
| PRV-002 | Tab Perfil | WT-977 | 🏷️ MVP P | — |
| PRV-003 | Tab Atividades | WT-978 | ✅ Done | — |
| PRV-004 | Tab Arquivos | WT-979 | ✅ Done | — |
| PRV-005 | Tab Parecer LIA | WT-980 | ✅ Done | — |

**Resultado: 13 Done, 1 Code Review, 3 MVP P, 1 OBSOLETO, 1 sem card**

---

### É5 — Gate 1: Aprovar Mapeados (6 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| GAT-001 | Gate 1: Aprovar Mapeados | WT-935 | 🏷️ MVP P | Feb 27 deadline |
| GAT-003 | Modal de Reprovação | WT-937 | 🏷️ MVP P | — |
| GAT-004 | Geração Feedback LIA | WT-938 | 🏷️ MVP P | Feb 20 deadline (atrasado?) |
| GAT-005 | Envio de Feedback | WT-939 | 🏷️ MVP P | — |
| GAT-006 | Aprovação em Massa | WT-940 | 🏷️ MVP P | — |
| GAT-007 | Histórico Decisões | WT-941 | 🏷️ MVP P | Feb 27 deadline |

**Resultado: 0 Done, 6 MVP P — épico inteiro não iniciado**
**Risco:** Épico crítico (path completo) sem nenhum card iniciado.

---

### É6 — Contato Email (9 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| TPL-001 | Template Abordagem Inicial | WT-942 | 🏷️ MVP P | — |
| TPL-005 | Editor de Templates | WT-946 | 🔨 In Progress | — |
| TPL-006 | Variáveis Dinâmicas | WT-947 | 🏷️ MVP P | — |
| TPL-007 | Preview de Template | WT-948 | 📝 TO DO | — |
| TRI-002 | Envio Mensagem Inicial | WT-917 | 🔄 Revisão pré-MVP | — |
| TRI-009 | Templates de Mensagem | WT-924 | 🔄 Revisão pré-MVP | — |
| TRI-010 | Envio em Massa/Bulk | WT-925 | 🔍 QA | — |
| NOT-001 | Sistema Bell | WT-957 | 📦 Backlog | Feb 27 deadline |
| TPL-009 | Template Email Contato | WT-1475 | ✅ Criado | Gap identificado no doc |

**Resultado: 0 Done, 1 In Progress, 2 Revisão, 1 QA, 2 MVP P, 1 TO DO, 1 Backlog, 1 sem card**

---

### É6B — Follow-up Automático (1 card no doc + 2 gaps)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| TRI-007 | Timeout e Retentativas | WT-922 | 🔨 In Progress | — |
| FLW-001 | Follow-up 7 dias | WT-1473 | ✅ Criado | Gap — A CRIAR |
| FLW-002 | Status "sem_resposta" | WT-1474 | ✅ Criado | Gap — A CRIAR |

**Resultado: 1 In Progress, 2 gaps sem card**

---

### É7 — Triagem WSI (7 cards Produto + 7 cards SCO/AGT no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| TRI-001 | Config WhatsApp Business | WT-916 | 🏷️ MVP P | — |
| TRI-003 | Webhook Recebimento | WT-918 | 🔍 QA | — |
| TRI-004 | Fluxo Conversacional LIA | WT-919 | 🔍 QA | Core — BLOQUEANTE |
| TRI-005 | Persistência Conversa | WT-920 | 🔨 In Progress | — |
| TRI-006 | Transcrição no Card | WT-921 | 🔨 In Progress | — |
| TRI-008 | Opt-out e Consentimento | WT-923 | 🔨 In Progress | — |
| TRI-011 | Pré-Qualificação | WT-926 | 📦 Backlog | Feb 20 deadline (atrasado?) |
| TRI-013 | Reporte Problemas Cand. | WT-1464 | ✅ Criado | WT-1464 |
| SCO-001 | Cálculo Score WSI | WT-927 | 🏷️ MVP P | Feb 27 deadline |
| SCO-002 | Modelo Big Five | WT-928 | 🏷️ MVP P | Feb 27 deadline |
| SCO-003 | Avaliação Bloom/Dreyfus | WT-929 | 🏷️ MVP P | Feb 27 deadline |
| SCO-004 | Parecer Textual LIA | WT-930 | 🏷️ MVP P | — |
| SCO-005 | Visualização Score | WT-931 | 🏷️ MVP P | Feb 20 deadline (atrasado?) |
| SCO-006 | Breakdown Dimensões | WT-932 | 🏷️ MVP P | Feb 20 deadline (atrasado?) |
| SCO-007 | Comparação Candidatos | WT-933 | 🏷️ MVP P | Feb 20 deadline (atrasado?) |
| SCO-008 | Histórico Scores | WT-934 | 🏷️ MVP P | — |
| AGT-001 | Agente Avaliador WSI | WT-1223 | 🏷️ MVP P | — |
| AGT-004 | Orquestr. Pipeline Chat | WT-1438 | ✅ Criado | — |

**Resultado: 0 Done, 3 In Progress, 2 QA, 9 MVP P, 1 Backlog, 3 sem card**
**Risco ALTO:** Scoring inteiro (SCO-001~008) não iniciado. Deadlines Feb 20 atrasados.

---

### É8 — Gate 2: Aprovar Triados (2 cards únicos no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| GAT-002 | Gate 2: Aprovar Triados | WT-936 | 🏷️ MVP P | Feb 22 deadline (atrasado?) |
| GAT-008 | Aprendizagem IA | WT-1298 | 🏷️ MVP P | Feb 27 deadline |

**Resultado: 0 Done, 2 MVP P — não iniciado**

---

### É9A — Agendamento de Entrevista (14 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| AGE-001 | Integração MS Graph | WT-949 | 🔍 QA | — |
| AGE-002 | Consulta Disponibilidade | WT-950 | 🏷️ MVP P | — |
| AGE-003 | Sugestão Horários | WT-951 | 🔍 QA | — |
| AGE-004 | Criação Evento Teams | WT-952 | 🔍 QA | — |
| AGE-005 | Confirmação Candidato | WT-953 | 🏷️ MVP P | — |
| AGE-006 | Reagendamento | WT-954 | 🔨 In Progress | — |
| AGE-007 | Lembretes Automáticos | WT-955 | 🔍 QA | — |
| AGE-008 | Cancelamento | WT-956 | 🔍 QA | — |
| AGT-003 | Ag. Agendamento | WT-1225 | 📦 Backlog | — |
| TPL-002 | Template Agendamento | WT-943 | 🏷️ MVP P | Feb 27 deadline |
| TPL-003 | Template Confirmação | WT-944 | 🔄 Revisão pré-MVP | — |
| INT-MSG-002 | OAuth Flow MS | WT-1463 | ✅ Criado | Coberto por WT-1206? (INT-WOS-002) |
| INT-MSG-003 | Calendar API | WT-998 | 🏷️ MVP P | — |
| INT-MSG-004 | Teams Meeting API | WT-999 | 🏷️ MVP P | — |
| INT-MSG-005 | Webhook Eventos | WT-1000 | 🏷️ MVP P | — |
| INT-MSG-006 | Token Refresh | WT-1001 | 🏷️ MVP P | — |

**Resultado: 0 Done, 1 In Progress, 5 QA, 5 MVP P, 1 Revisão, 1 Backlog, 1 sem card**

---

### É9B — Feedback Final (1 card no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| TPL-004 | Template Pós-Entrevista | WT-945 | 🔄 Revisão pré-MVP | — |

**Resultado: 1 Revisão pré-MVP**

---

### Pipeline PIP-001~010 (10 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| PIP-001 | Arquitetura 3 Camadas | WT-1400 | ✅ Criado | — |
| PIP-002 | Motor action_behavior | WT-1401 | ✅ Criado | — |
| PIP-003 | UniversalTransitionModal | WT-1402 | ✅ Criado | — |
| PIP-004 | use-transition-context | WT-1403 | ✅ Criado | — |
| PIP-005 | Movimentação Livre | WT-1404 | ✅ Criado | — |
| PIP-006 | Badges nos Cards | WT-1405 | ✅ Criado | — |
| PIP-007 | TransitionDispatchService | WT-1406 | ✅ Criado | — |
| PIP-008 | Endpoints de Transição | WT-1407 | ✅ Criado | — |
| PIP-009 | Pipeline CRUD | WT-1408 | ✅ Criado | — |
| PIP-010 | Barra de Ações em Massa | WT-1409 | ✅ Criado | — |

**Resultado: 10/10 — Todos os cards PIP foram criados no Jira (WT-1400~WT-1409) ✅**
**Nota:** Cards criados em 26/02/2026 via sincronização automática dos docs.

---

### IA — Fundação PREP (14 cards no doc)

| Card Doc | Título | Jira Key | Status Jira |
|----------|--------|----------|-------------|
| PREP-001 | Estrutura Diretórios DDD | WT-1410 | ✅ Criado |
| PREP-002 | Contratos Base (DomainPrompt ABC) | WT-1411 | ✅ Criado |
| PREP-003 | DomainWorkflow Pipeline | WT-1412 | ✅ Criado |
| PREP-004 | DomainRegistry + Auto-discovery | WT-1413 | ✅ Criado |
| PREP-005 | CascadedRouter | WT-1414 | ✅ Criado |
| PREP-006 | LLM Provider ABC + Factory | WT-1415 | ✅ Criado |
| PREP-007 | Prompt System (YAML) | WT-1416 | ✅ Criado |
| PREP-008 | Tool System (Registry) | WT-1417 | ✅ Criado |
| PREP-009 | ConversationState + Memory | WT-1418 | ✅ Criado |
| PREP-010 | Database Migrations | WT-1419 | ✅ Criado |
| PREP-011 | Mapa de Equivalências | WT-1420 | ✅ Criado |
| PREP-012 | Dependências entre Domínios | WT-1421 | ✅ Criado |
| PREP-013 | Robustness Layer | WT-1422 | ✅ Criado |
| PREP-014 | Few-Shot Examples | WT-1423 | ✅ Criado |

**Resultado: 14/14 — Todos os cards PREP foram criados no Jira (WT-1410~WT-1423) ✅**
**Nota:** 94% do código PREP é portável do protótipo Replit. Os cards são de tracking/planejamento.

---

### IA — Infraestrutura INF (8 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| INF-001 | DomainPrompt ABC + Registry | WT-1424 | ✅ Criado | Código existe no protótipo |
| INF-002 | DomainWorkflow | WT-1425 | ✅ Criado | Código existe no protótipo |
| INF-003 | CascadedRouter | WT-1426 | ✅ Criado | Código existe no protótipo |
| INF-004 | FastRouter | WT-1427 | ✅ Criado | Código existe no protótipo |
| INF-005 | EventDispatcher + Pipeline L2 | WT-1428 | ✅ Criado | Código existe no protótipo |
| INF-008 | ConversationMemory | WT-1429 | ✅ Criado | Código existe no protótipo |
| INF-012 | Feature Flags Service | WT-1430 | ✅ Criado | Código existe no protótipo |
| INF-014 | Structured Output Parser | WT-1431 | ✅ Criado | Código existe no protótipo |

**Resultado: 8/8 — Cards INF prioritários foram criados no Jira (WT-1424~WT-1431) ✅**
**PORÉM:** Cards S4 equivalentes JÁ FEITOS: INF-010/Circuit Breaker parcial via WT-1006 (Fallback) + WT-1010 (Rate Limiting) Done; INF-011/Token Tracking via WT-1009 (Monitoramento Custos) Done; INF-013/Agent Monitoring via WT-1011 (Logging Audit) Done. Código do protótipo cobre ~75% dos INF restantes.

---

### IA — Serviços SRV (14 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | % Feito | Obs |
|----------|--------|----------|-------------|:-------:|-----|
| SRV-001 | LLM Service | WT-1003~1011 | ✅ Done | 100% | 9 cards INT-LLM Done (Cliente Claude, Gemini, Router, Fallback, Prompts, Cache, Custos, Rate Limiting, Audit) |
| SRV-002 | WSI Screening Pipeline | WT-912 | 🔍 QA | ~80% | WSI Blocos em QA + WT-546 Doc WSI Done |
| SRV-003 | WSI Question Generator | WT-911 | 🔍 QA | ~80% | Motor WSI em QA + WT-1295 Edição Prompt Done |
| SRV-004 | WSI Scoring Engine | WT-927 | 🏷️ MVP P | ~50% | SCO-001 em MVP P + WT-1141 Scoring em QA |
| SRV-005 | JD Generator Service | WT-900 | 📦 Backlog | ~50% | WT-1121/1122 JD Generation Done |
| SRV-007 | CV Parser + Scoring | WT-1163 | Parcial | ~30% | curriculum_text Done, parser completo pendente |
| SRV-008 | Embedding Service | WT-906 | ✅ Done | 100% | MAP-002 Busca Semântica Done |
| SRV-009 | Sourcing Pipeline ES+PGV+WRF | WT-1146/910 | ✅ ~70% Done | ~70% | WT-1282/1283 Dedup+Ranking Done |
| SRV-010 | Scheduling Service | WT-1432 | ✅ Criado | 0% | Lógica parcial em AGE-001~008 (QA) |
| SRV-011 | Email Service Mailgun | WT-939 | 🏷️ MVP P | ~40% | GAT-005 Envio Feedback em MVP P |
| SRV-012 | WhatsApp Service | WT-990~995 | ✅ ~70% Done | ~70% | 6 cards INT-TWI Done (infra WhatsApp funciona) |
| SRV-013 | Teams Notification | WT-1434 | ✅ Criado | 0% | — |
| SRV-014 | ATS Sync Service Merge | WT-1347 | Parcial | ~30% | Integração Questt Done |
| SRV-016 | Stage Automation Engine | WT-1436 | ✅ Criado | 0% | — |

**Resultado ATUALIZADO: 3/14 Done (SRV-001, SRV-008, SRV-012), 2 em QA (SRV-002/003), 1 MVP P (SRV-004), 4 parciais, 4 sem card**
**Conclusão:** Dos 14 cards SRV (~118 pts), ~60 pts já estão feitos ou em QA. Esforço real: ~58 pts novos.

---

### IA — Agentes AGT (11 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| AGT-000 | Orchestrator | WT-1437 | ✅ Criado | Código existe no protótipo |
| AGT-001 | Ag.5 Avaliador WSI | WT-1223 | 🏷️ MVP P | Coberto parcialmente por SCO-001~008 (WT-927~934) em MVP P |
| AGT-002 | Ag.3 Triagem Curricular | WT-1224 | 🏷️ MVP P | Fluxo conversacional em QA via TRI-004 (WT-919) |
| AGT-003 | Ag.6 SchedulingAgent | WT-1225 | 🏷️ MVP P | Lógica coberta por AGE-001~008 (WT-949~956) em QA |
| AGT-004 | Ag.0 Orquestrador Pipeline Chat | WT-1438 | ✅ Criado | Código existe no protótipo |
| AGT-006 | Ag.2 SourcingAgent | WT-1439 | ✅ Criado | Código existe no protótipo |
| AGT-007 | Ag.4 EntrevistadorWSI | WT-1440 | ✅ Criado | Código existe no protótipo |
| AGT-008 | Ag.7 AnalistaFeedback | WT-1441 | ✅ Criado | — |
| AGT-009 | Ag.8 IntegradorATS | WT-1442 | ✅ Criado | — |
| AGT-010 | Ag.9 TaskPlanner | WT-1443 | ✅ Criado | — |
| AGT-011 | Ag.10 CommunicationAgent | WT-1444 | ✅ Criado | — |

**Resultado ATUALIZADO: 3/11 em MVP P (AGT-001/002/003), 8 sem card**
**PORÉM:** AGT-001/002/003 têm trabalho significativo via cards de produto: SCO-001~008 (scoring) em MVP P, TRI-004 (triagem conversacional) em QA, AGE-001~008 (agendamento) em QA. AGT-000/004/006/007 têm código completo no protótipo.

---

### IA — Automações AUT (6 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| AUT-001 | Follow-up automático 7 dias | WT-1445 | ✅ Criado | — |
| AUT-002 | Timeout triagem abandonada | WT-1446 | ✅ Criado | — |
| AUT-003 | Auto-pause/complete | WT-1447 | ✅ Criado | — |
| AUT-004 | Cascata job_published→sourcing | WT-1448 | ✅ Criado | — |
| AUT-005 | Cascata screening→feedback | WT-1449 | ✅ Criado | — |
| AUT-006 | Cascata stage→rejection | WT-1450 | ✅ Criado | — |

**Resultado: 6/6 — Todos os cards AUT foram criados no Jira (WT-1445~WT-1450) ✅**
**Nota:** Dependem de infraestrutura de eventos (INF-005 EventDispatcher). Código de referência existe no protótipo para AUT-005/006.

---

### IA — Transversais TRV (4 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | Obs |
|----------|--------|----------|-------------|-----|
| TRV-001 | LGPD Básico | WT-920 | 🔨 In Progress | TRI-008 Opt-out LGPD em desenvolvimento |
| TRV-003 | Calibração Contextual Senioridade | WT-1451 | ✅ Criado | Código existe no protótipo |
| TRV-004 | Multi-Signal Seniority | WT-1452 | ✅ Criado | Código existe no protótipo |
| TRV-005 | Governança Humana | WT-1453 | ✅ Criado | Código existe no protótipo |

**Resultado ATUALIZADO: 1/4 parcial (TRV-001 via WT-920 In Progress), 3 sem card**
**Nota:** TRV-003/004/005 têm código completo no protótipo (calibração senioridade, multi-signal, governança).

---

### IA — Integrações INT-AI (6 cards no doc)

| Card Doc | Título | Jira Key | Status Jira | % Feito | Obs |
|----------|--------|----------|-------------|:-------:|-----|
| INT-AI-001 | Gemini API Setup | WT-1004/1106 | ✅ Done | 100% | Cliente Gemini + Embedding Done (INT-LLM-002/003) |
| INT-AI-002 | Merge.dev ATS | WT-1454 | ✅ Criado | 0% | Integração nova |
| INT-AI-003 | Mailgun Email | WT-1455 | ✅ Criado | 0% | Integração nova |
| INT-AI-004 | Pearch + Apify | WT-1230~1232 | 🏷️ MVP P | ~40% | INT-APY-001~003 em MVP P |
| INT-AI-005 | Microsoft Graph | WT-996~1002 + WT-1098~1104 | ✅ Done | 100% | ~14 cards INT-MSG Done (OAuth, Calendar, Teams, Webhook, Token, etc.) |
| INT-AI-007 | WhatsApp Business API | WT-990~995 | ✅ Done (infra) | ~80% | 6 cards INT-TWI Done (Twilio config, send, receive, webhook, templates, status) |

**Resultado ATUALIZADO: 3/6 Done (INT-AI-001, INT-AI-005, INT-AI-007), 1 MVP P (INT-AI-004), 2 novos (INT-AI-002/003)**
**Conclusão:** Dos 6 cards INT-AI (~55 pts), ~39 pts já estão Done. Esforço real: ~18 pts novos (Merge.dev + Mailgun).

---

## 3. CARDS NO JIRA SEM CORRESPONDÊNCIA NO DOC MVP ALPHA

Estes cards existem no Jira (visíveis nas screenshots) mas **NÃO estão mapeados** no documento `mvp-alpha-scenarios.md`:

### 3.1 Wizard Steps (VAG-079~087) — 9 cards → 🗑️ DELETADOS

> **Status rev.3:** Todos os 9 cards já não existiam no Jira (404) — deletados em sessão anterior. Wizard conversacional adiado para Alpha 2+.

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| ~~WT-358~366~~ | ~~VAG-079~087~~ | ~~Wizard Steps 3-11~~ | 🗑️ Deletados (não existiam no Jira) |

**Avaliação original:** O doc MVP Alpha ADIOU o wizard conversacional para Alpha 2+. Alpha 1 usa form de edição simplificado (WIZ-008).

### 3.2 Backend Rails — APIs (VAG-088~108) — 21 cards → 🗑️ DELETADOS (19 nesta sessão)

> **Status rev.3:** 19 cards deletados nesta sessão. WT-385 (VAG-106 API Integração WorkOS) estava como Done e foi deletado por engano — recriado como **WT-1398** (Done). WT-373 (VAG-094) e WT-387 (VAG-108) não constavam na lista.

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| ~~WT-367~386~~ | ~~VAG-088~107~~ | ~~APIs Backend Rails (19 cards)~~ | 🗑️ Deletados |
| **WT-1398** | VAG-106 | [BACK-RAILS] API Integração WorkOS | ✅ Done (recriado) |

**Avaliação original:** APIs do backend Rails. Alpha 1 roda com Python/Next.js — APIs Rails são Alpha 2.

### 3.3 Backend IA (VAG-109~122) — 14 cards → 🗑️ DELETADOS (já não existiam)

> **Status rev.3:** Todos os 14 cards já não existiam no Jira (404) — deletados em sessão anterior. Substituídos pelos cards SRV/AGT do novo documento de arquitetura IA (`docs/lia-ai-architecture-cards-jira.md` v2.6).

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| ~~WT-388~401~~ | ~~VAG-109~122~~ | ~~Backend IA (14 cards)~~ | 🗑️ Deletados (não existiam no Jira) |

**Mapeamento de substituição (para referência):**

| Card Jira deletado | Substituído por (novo) |
|---------------------|------------------------|
| VAG-112 Metodologia LIA | SRV-002 WSI Screening Pipeline |
| VAG-115 WSI Service | SRV-004 WSI Scoring Engine |
| VAG-116 CV Parser | SRV-007 CV Parser |
| VAG-117 WSI Question Generator | SRV-003 WSI Question Generator |
| VAG-118 Personalized Feedback | AGT-008 AnalistaFeedback |
| VAG-121 Semantic Search | SRV-008 Embedding Service |
| VAG-109~111, 113~114, 119~120, 122 | Cobertos por SRV/AGT diversos |

### 3.4 Frontend VAG extras (VAG-123~132) — 10 cards → 4 promovidos + 6 deletados

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| WT-405 | VAG-123 | [FRONT] Badge Pipeline Saturado | 🏷️ **Alpha 1 — Prioridade Alta** |
| WT-406 | VAG-124 | [FRONT] Botão Desbloquear Pipeline - Override Manual | 🏷️ **Alpha 1 — Prioridade Alta** |
| WT-407 | VAG-125 | [BACK-IA] API GET /saturation-status | 🏷️ **Alpha 1 — Prioridade Alta** |
| WT-408 | VAG-126 | [BACK-IA] API POST /unlock-pipeline | 🏷️ **Alpha 1 — Prioridade Alta** |
| ~~WT-409~~ | ~~VAG-127~~ | ~~[FRONT] Wizard Step 7.5 - GovernanceRules~~ | 🗑️ Deletado — coberto por TRV-005 |
| ~~WT-410~~ | ~~VAG-128~~ | ~~[FRONT] GovernanceRulesForm Reutilizável~~ | 🗑️ Deletado — coberto por TRV-005 |
| ~~WT-411~~ | ~~VAG-129~~ | ~~[FRONT] LIAFeedbackWidget - Thumbs Up/Down~~ | 🗑️ Deletado — coberto por TRV-003 |
| ~~WT-412~~ | ~~VAG-130~~ | ~~[FRONT] CalibrationInsights - Divergências~~ | 🗑️ Deletado — coberto por TRV-003/004 |
| ~~WT-413~~ | ~~VAG-131~~ | ~~[BACK-IA] API POST /calibration/feedback~~ | 🗑️ Deletado — coberto por TRV-003 |
| ~~WT-414~~ | ~~VAG-132~~ | ~~[BACK-IA] API GET /calibration/divergences~~ | 🗑️ Deletado — coberto por TRV-003 |

**Avaliação atualizada (fev/2026):**

**Promovidos para Alpha 1 (WT-405~408 — Saturação de Pipeline):**
Cards de governança de triagem promovidos para Alpha 1 como prioridade alta. Saturação de pipeline impede que o recrutador continue aprovando candidatos quando uma etapa já está sobrecarregada. Diretamente ligados à triagem WSI e TRV-005 (GovernanceRules).

**⚠️ Estado atual da implementação — AÇÃO NECESSÁRIA:**
- **Backend:** O agente de triagem (`lia-agent-system/app/domains/cv_screening/agents/triagem_curricular_agent.py`) já tem a ação `check_saturation` com handler `_handle_check_saturation`. Porém os dados são **hardcoded/mock** (`approved_count: 18`, `saturation_threshold: 20`) — **precisa conectar ao banco de dados real**. Os endpoints REST `/saturation-status` e `/unlock-pipeline` **não existem** e precisam ser criados.
- **Frontend:** **Nenhum componente de UI existe.** Badge Pipeline Saturado (indicador visual no Kanban) e Botão Desbloquear Pipeline (override manual) precisam ser **construídos do zero**.

**Deletados (WT-409~414 — Governança/Calibração):**
6 cards deletados permanentemente do Jira. Funcionalidades cobertas pelos novos cards de arquitetura IA: TRV-003 (WSI Calibração Contextual), TRV-004 (Multi-Signal Seniority), TRV-005 (GovernanceRules).

### 3.5 Config Admin (CFG-001~005, IMP-001) — 6 cards

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| WT-1217 | CFG-001 | [FRONTEND] Configurar Campos Consumidos por LIA | 🏷️ MVP P |
| WT-1218 | CFG-002 | [BACKEND] Serviço de Completude de Configuração | 📦 Backlog |
| WT-1219 | CFG-003 | [FRONTEND] Editor de Jornada de Recrutamento | 📦 Backlog |
| WT-1220 | CFG-004 | [FRONTEND] Hub de Configuração de Comunicação | 🏷️ MVP P |
| WT-1221 | CFG-005 | [FRONTEND] Seção de Dados da Empresa | 📦 Backlog |
| WT-1222 | IMP-001 | [FRONTEND] Smart Import Zone | 📦 Backlog |

**Avaliação:** O doc MVP Alpha **EXCLUI explicitamente** configs admin do Alpha 1 (seção 2.3). Todos são Alpha 2.

### 3.6 DevOps/Infra (DEV-S1~S5) — ~20 cards

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| WT-43 | DEV-S1-001 | Setup Inicial do Projeto Rails | 📦 Backlog |
| WT-51 | DEV-S2-004 | Gerenciamento de Sessão JWT | 📦 Backlog |
| WT-53 | DEV-S3-001 | Implementar StripeWebhookService | 📦 Backlog |
| WT-54 | DEV-S3-002 | Implementar StripeBillingService | 📦 Backlog |
| WT-55 | DEV-S3-003 | Criar Endpoints de Billing | 📦 Backlog |
| WT-56 | DEV-S3-004 | Implementar Controller de Webhooks Stripe | 📦 Backlog |
| WT-58 | DEV-S4-001 | Implementar HubSpotSyncService | 📦 Backlog |
| WT-59 | DEV-S4-002 | Implementar Jobs de Sync HubSpot | 📦 Backlog |
| WT-63 | DEV-S5-001 | Implementar PrivacyToolsService | 📦 Backlog |
| WT-64 | DEV-S5-002 | Implementar Webhook Privacy Tools | 📦 Backlog |
| WT-65 | DEV-S5-003 | Implementar AuditLogService | 📦 Backlog |

**Avaliação:** Infraestrutura Rails e integrações de billing/CRM. O DEV-S1-001 (Setup Rails) é pré-requisito para todas as APIs Rails. Stripe/HubSpot/Privacy são **Alpha 2+**.

### 3.7 WDT — Otimização de Busca (WDT-008~030) — ~23 cards

| Jira Key | Card | Título | Status |
|----------|------|--------|--------|
| WT-1311 | WDT-008 | Dashboard básico de métricas de feedback | 📦 Backlog |
| WT-1312 | WDT-009 | Classificação automática de nível de qualificação | 📦 Backlog |
| WT-1319 | WDT-016 | Schema e modelo da base de critérios | 📦 Backlog |
| WT-1320 | WDT-017 | Interface admin para gestão de critérios | 📦 Backlog |
| WT-1325 | WDT-022 | Score de confiança individual por requisito | 📦 Backlog |
| ... | ... | *(mais ~18 cards)* | 📦 Backlog |

**Avaliação:** Otimização avançada do sistema de busca (WeDoTalent Search). **Alpha 2+** — não são bloqueantes para o fluxo core.

### 3.8 Cards Avulsos Relevantes (Bugs, Melhorias, Layout)

| Jira Key | Título | Status | Relevância Alpha 1 |
|----------|--------|--------|---------------------|
| WT-1268 | Melhorias LIA (Teste de segurança XSS) | 📋 Code Review | Alta — segurança |
| WT-1269 | Melhorias LIA (Memory Leak) | 🔨 In Progress | Alta — estabilidade |
| WT-1270 | Melhorias LIA (Padronização de UI) | 🔨 In Progress | Média — DS v4.1 |
| WT-1141 | Coleta evaluation + score LIA | Processo de Avaliação | Alta — scoring |
| WT-1142 | Frontend demonstração score LIA | Processo de Avaliação | Média — demo |
| WT-1149 | Layout preview do job adaptado | Layout Job | Alta — UX |
| WT-1151 | Mudança no show de job | Layout Job | Média — UX |
| WT-1187 | Serviço Pré-Qualificação Automatizada | 📦 Backlog | Alta — TRI-012 |
| WT-1188 | [KAN-009] Refatoração Modular Kanban | 🏷️ MVP P | Média — refactor |
| WT-1199 | [INT-LLM-004] Fallback Automático entre Modelos LLM | 📦 Backlog | Alta — resiliência |
| WT-1292 | [AUTH-006] Revisão Final Design | ❌ Sem label | Baixa — design |
| WT-1297 | [TRI-014] Pesquisa Alternativas Twilio→WhatsApp BSP | 📦 Backlog | Alta — WhatsApp |

---

## 4. CARDS DO DOC QUE NÃO EXISTEM NO JIRA — RESUMO

### Quantidade por categoria (atualizado rev.5 c/ cruzamento IA)

| Categoria | Cards Doc | Cards Jira | Gap Bruto | Trabalho Existente (rev.4) | Gap Real |
|-----------|:---------:|:----------:|:---------:|:---------------------------|:--------:|
| PREP (infraestrutura DDD) | 14 | 0 | 14 | 94% portável do protótipo | **14** |
| INF (infraestrutura IA) | 8 | 0 | 8 | INF-010/011/013 equiv. ✅ Done (3); 75% portável | **~5** |
| SRV (serviços core) | 14 | 0 | 14 | SRV-001/008 ✅ Done; 002/003 🔍 QA; 009/012 ~70% | **~6** |
| AGT (agentes) | 11 | 3 | 8 | AGT-001/002/003 🏷️ MVP P; 4 core c/ código no protótipo | **~4** |
| AUT (automações) | 6 | 0 | 6 | Código ref. para AUT-005/006 | **~4** |
| TRV (transversais) | 4 | 0 | 4 | TRV-001 🔨 In Prog (WT-920); TRV-003~005 c/ código | **~3** |
| INT-AI (integrações IA) | 6 | 0 | 6 | INT-AI-001/005/007 ✅ Done; INT-AI-004 🏷️ MVP P | **~2** |
| PIP (pipeline) | 10 | 0 | 10 | KAN-001~008 (Done) cobrem parte | **~10** |
| Gaps a Criar (PUB, FLW, etc.) | 10 | 0 | 10 | — | **~10** |
| **TOTAL** | **83** | **3** | **~80** | **~25 com trabalho significativo** | **~58** |

> **Nota rev.5:** O "Gap Real" desconta cards com equivalentes Done/QA no Jira e cards com código completo no protótipo. Dos ~58 cards de gap real, **~35 têm código de referência** no protótipo Replit — o esforço é portar e adaptar, não construir do zero.

### Recomendação

1. **Criar como épico "IA Architecture" no Jira:** PREP, INF, AUT, TRV (32 cards) — são tracking de portabilidade do protótipo
2. **Não duplicar equivalentes:** SRV-001/008, INT-AI-001/005/007, INF-010/011/013 já estão Done via cards equivalentes — apenas linkar, não criar novos
3. **Criar gaps bloqueantes:** PUB-001 (página pública triagem), FLW-001/002 (follow-up), TRI-015~017 (triagem abandonada) — 5 cards obrigatórios
4. **PIP cards:** Avaliar se KAN-001~008 (Done) cobrem PIP-001~010 ou se são complementares
5. **Adiar criação massiva:** Não criar todos os 80 cards de uma vez — priorizar os ~20 bloqueantes

---

## 4B. CRUZAMENTO JIRA REAL × CARDS IA — O QUE JÁ ESTÁ FEITO

> Resultado do cruzamento dos 63 cards IA planejados (478 pts) com o estado real do Jira (478 cards WT consultados em fev/2026).
> **Conclusão: esforço real de IA é ~38 cards novos (~300 pts), NÃO 63 cards (478 pts).**

### ✅ JÁ FEITO (Done no Jira) — ~8 cards equivalentes / ~85 pts eliminados

| Card Alpha | Título | Equivalente Jira | Status |
|------------|--------|------------------|--------|
| SRV-001 | LLM Service | WT-1003~1011 (9 cards INT-LLM) | ✅ Done — Cliente Claude/Gemini, Router, Fallback, Cache, Custos, Rate Limiting, Audit |
| SRV-008 | Embedding Service | WT-906 (MAP-002) | ✅ Done — Busca Semântica |
| SRV-012 | WhatsApp Service | WT-990~995 (6 cards INT-TWI) | ✅ ~70% Done — Infra WhatsApp funciona |
| SRV-009 | Sourcing Pipeline | WT-1146/910/1282/1283 | ✅ ~70% Done — Dedup+Ranking feitos |
| INT-AI-001 | Gemini API Setup | WT-1004/1106 (INT-LLM-002/003) | ✅ Done — Cliente Gemini + Embedding |
| INT-AI-005 | Microsoft Graph | WT-996~1002 + WT-1098~1104 (~14 cards) | ✅ Done — OAuth, Calendar, Teams, Webhook, Token |
| INT-AI-007 | WhatsApp Business API | WT-990~995 (6 cards INT-TWI) | ✅ Done — Infra Twilio completa |
| INF-010/011/013 | Circuit Breaker, Token, Monitoring | WT-1006/1009/1010/1011 | ✅ Done — Equivalentes S4 feitos |

### 🔄 EM ANDAMENTO (QA / In Progress / MVP P) — ~10 cards / ~80 pts parciais

| Card Alpha | Título | Equivalente Jira | Status | % |
|------------|--------|------------------|--------|:-:|
| SRV-002 | WSI Screening Pipeline | WT-912 | 🔍 QA | ~80% |
| SRV-003 | WSI Question Generator | WT-911 | 🔍 QA | ~80% |
| SRV-004 | WSI Scoring Engine | WT-927 + WT-1141 | 🏷️ MVP P / 🔍 QA | ~50% |
| SRV-005 | JD Generator | WT-900 + WT-1121/1122 | 📦 Backlog + ✅ Done | ~50% |
| SRV-007 | CV Parser | WT-1163 | Parcial | ~30% |
| AGT-001 | Avaliador WSI | WT-1223 + SCO-001~008 | 🏷️ MVP P | ~40% |
| AGT-002 | Triagem Curricular | WT-1224 + WT-919 (TRI-004) | 🏷️ MVP P + 🔍 QA | ~50% |
| AGT-003 | SchedulingAgent | WT-1225 + AGE-001~008 | 🏷️ MVP P + 🔍 QA | ~40% |
| INT-AI-004 | Pearch + Apify | WT-1230~1232 | 🏷️ MVP P | ~40% |
| TRV-001 | LGPD Básico | WT-920 (TRI-008) | 🔨 In Progress | ~30% |

### ❌ REALMENTE NOVO (sem trabalho no Jira) — ~38 cards / ~300 pts

| Grupo | Cards | Pts | Observação |
|-------|:-----:|:---:|------------|
| PREP-001~014 | 14 | 71 | Estrutura DDD — 94% portável do protótipo |
| INF-001~005, 008, 012, 014 | 8 | 56 | Infraestrutura — 75% portável |
| SRV-010, 013, 016 | 3 | 18 | Scheduling, Teams, Automation |
| SRV-011, 014 | 2 | 13 | Email, ATS Sync (parcial) |
| AGT-000, 004, 006, 007 | 4 | 47 | Agentes core — código no protótipo |
| AGT-008~011 | 4 | 32 | Agentes complementares |
| AUT-001~006 | 6 | 33 | Automações — código referência para 2 |
| TRV-003~005 | 3 | 29 | Calibração e Governança — código no protótipo |
| INT-AI-002, 003 | 2 | 18 | Merge.dev e Mailgun — integração nova |
| **TOTAL NOVO** | **~38** | **~300** | **~63% do plano original** |

### 📊 Resumo do Cruzamento

| Categoria | Cards | Pts | % do Total IA |
|-----------|:-----:|:---:|:------------:|
| ✅ Já feito (Done) | ~8 | ~85 | 18% |
| 🔄 Em andamento (QA/MVP P) | ~10 | ~80 | 17% |
| ❌ Realmente novo | ~38 | ~300 | 63% |
| ❓ Parcial (código no protótipo) | ~7 | ~13 | 3% |
| **Total IA Alpha 1** | **63** | **478** | **100%** |

> **Impacto na negociação:** O esforço real de IA para Alpha 1 é significativamente menor que o planejado. Dos 478 pts de IA, ~85 pts já estão Done e ~80 pts estão em andamento. O esforço líquido novo é ~300 pts, e desses, ~70% têm código de referência no protótipo Replit.

---

## 5. ANÁLISE DE PRIORIZAÇÃO MoSCoW PARA NEGOCIAÇÃO

### Resumo: Cards que precisam de trabalho de desenvolvimento

> Apenas cards com status MVP P, Sem card, Backlog ou TO DO. Exclui cards Done, QA, In Progress, Code Review e Revisão.

| Grupo | Cards | Pts | Descrição |
|-------|:-----:|:---:|-----------|
| P0 — Must Have | 14 | 105 | Gates, Scoring core, Mapeamento, WhatsApp, Bloqueante |
| P1 — Should Have | 23 | 144 | Scoring completo, Gates completos, Templates, Agendamento, MS Graph, Busca+UI |
| P2 — Produto | 9 | 28 | Histórico scores, Like/Dislike, Pré-qualificação, Triagem lote |
| P2 — IA (novos) | 38 | 300 | PREP, INF, SRV, AGT, AUT, TRV, INT-AI — ~70% c/ código no protótipo |
| Pipeline | 10 | 62 | PIP-001~010 — parcialmente coberto por KAN (Done) |
| Gaps a Criar | 7 | 30 | Follow-up, Saturação pipeline, Templates faltantes |
| **TOTAL trabalho novo** | **101** | **669** | |

> Ver seção 6 para lista detalhada card a card.

---

### MUST HAVE (P0) — Caminho Crítico Alpha 1

> Sem estes, o fluxo core **não funciona**. WhatsApp é canal prioritário junto com email.

| # | Card | Título | Jira Key | Status Jira | Semana | Pts | Justificativa |
|---|------|--------|----------|:-----------:|:------:|:---:|---------------|
| 1 | GAT-001 | Gate 1: Aprovar Mapeados | WT-935 | 🏷️ MVP P | 1 | 8 | Sem Gate 1, candidatos não avançam |
| 2 | GAT-002 | Gate 2: Aprovar Triados | WT-936 | 🏷️ MVP P | 1 | 8 | Sem Gate 2, não há decisão pós-triagem |
| 3 | GAT-003 | Modal de Reprovação | WT-937 | 🏷️ MVP P | 1 | 3 | Obrigatório para rejeição |
| 4 | GAT-006 | Aprovação em Massa | WT-940 | 🏷️ MVP P | 1 | 5 | Eficiência do consultor |
| 5 | SCO-001 | Cálculo Score WSI | WT-927 | 🏷️ MVP P | 1 | 13 | Core — sem score, sem decisão |
| 6 | SCO-004 | Parecer Textual LIA | WT-930 | 🏷️ MVP P | 1 | 8 | Core — parecer para o consultor |
| 7 | MAP-003 | Filtros Avançados | WT-907 | 🏷️ MVP P | 1 | 8 | Busca funcional de candidatos |
| 8 | MAP-004 | Adicionar Cand. à Vaga | WT-908 | 🏷️ MVP P | 1 | 5 | Ação fundamental |
| 9 | PRV-001 | Preview Lateral Cand. | WT-976 | 🏷️ MVP P | 1 | 5 | Ver dados do candidato |
| 10 | PRV-002 | Tab Perfil | WT-977 | 🏷️ MVP P | 1 | 5 | Dados básicos no preview |
| 11 | KAN-006 | Badge Score WSI | WT-968 | 📋 Code Rev | 1 | 2 | Score visível no card — aprovar PR |
| 12 | TRI-004 | Fluxo Conversacional LIA | WT-919 | 🔍 QA | 1 | 13 | Core — triagem via chat |
| 13 | PUB-001 | Página pública chat web | WT-1472 | ✅ Criado | 1 | 13 | **BLOQUEANTE CRÍTICO** — sem página, sem triagem web |
| 14 | TPL-001 | Template Abordagem Inicial | WT-942 | 🏷️ MVP P | 1 | 5 | Contato com candidato |
| 15 | TRI-002 | Envio Mensagem Inicial | WT-917 | 🔄 Revisão | 1 | 5 | Abordagem do candidato |
| 16 | TRI-001 | Config WhatsApp Business | WT-916 | 🏷️ MVP P | 1 | 8 | **WhatsApp é canal prioritário** |
| 17 | INT-AI-007 | WhatsApp Business API (provider) | WT-1399 | ✅ Criado | 1 | 8 | Integração com Twilio/Gupshup — obrigatório para WhatsApp |
| | | **Subtotal P0** | | | | **122** | **17 cards** |

### SHOULD HAVE (P1) — Melhoria importante

> Melhoram significativamente a experiência. Inclui cards já em andamento (QA/In Progress/Revisão) que devem ser completados.

| # | Card | Título | Jira Key | Status Jira | Pts | Justificativa |
|---|------|--------|----------|:-----------:|:---:|---------------|
| | | **— Scoring Completo —** | | | | |
| 1 | SCO-002 | Modelo Big Five (OCEAN) | WT-928 | 🏷️ MVP P | 8 | Avaliação comportamental |
| 2 | SCO-003 | Avaliação Bloom/Dreyfus | WT-929 | 🏷️ MVP P | 8 | Avaliação técnica |
| 3 | SCO-005 | Visualização Score | WT-931 | 🏷️ MVP P | 5 | Radar chart — deadline Feb 20 atrasado |
| 4 | SCO-006 | Breakdown Dimensões | WT-932 | 🏷️ MVP P | 8 | Detalhamento por competência — deadline Feb 20 atrasado |
| 5 | SCO-007 | Comparação Candidatos | WT-933 | 🏷️ MVP P | 8 | Side-by-side — deadline Feb 20 atrasado |
| | | **— Gates Completos —** | | | | |
| 6 | GAT-004 | Geração Feedback LIA | WT-938 | 🏷️ MVP P | 8 | Feedback automático — deadline Feb 20 atrasado |
| 7 | GAT-005 | Envio de Feedback | WT-939 | 🏷️ MVP P | 5 | Via email/WhatsApp |
| 8 | GAT-007 | Histórico Decisões | WT-941 | 🏷️ MVP P | 5 | Audit trail |
| 9 | GAT-008 | Aprendizagem IA | WT-1298 | 🏷️ MVP P | 8 | Padrões aprovação/rejeição |
| | | **— Templates e Busca —** | | | | |
| 10 | TAB-002 | Colunas Ordenáveis | WT-972 | 🏷️ MVP P | 3 | Ordenação tabela |
| 11 | TPL-005 | Editor de Templates | WT-946 | 🔨 In Prog | 8 | Editor WYSIWYG — já em desenvolvimento |
| 12 | TPL-006 | Variáveis Dinâmicas | WT-947 | 🏷️ MVP P | 5 | Merge tags |
| 13 | TPL-007 | Preview de Template | WT-948 | 📝 TO DO | 3 | Preview com dados reais |
| 14 | MAP-005 | Matching Score IA | WT-909 | 🏷️ MVP P | 13 | Score candidato×vaga |
| 15 | NOT-001 | Sistema Bell | WT-957 | 📦 Backlog | 5 | Notificações in-app |
| | | **— Agendamento (já em QA/Prog) —** | | | | |
| 16 | AGE-002 | Consulta Disponibilidade | WT-950 | 🏷️ MVP P | 5 | Disponibilidade do recrutador |
| 17 | AGE-005 | Confirmação Candidato | WT-953 | 🏷️ MVP P | 5 | Confirmação de horário |
| 18 | AGE-006 | Reagendamento | WT-954 | 🔨 In Prog | 5 | Já em desenvolvimento |
| 19 | AGE-007 | Lembretes Automáticos | WT-955 | 🔍 QA | 3 | Já em QA — completar |
| 20 | AGE-008 | Cancelamento | WT-956 | 🔍 QA | 3 | Já em QA — completar |
| | | **— MS Graph Integrações —** | | | | |
| 21 | INT-MSG-002 | OAuth Flow MS | WT-1463 | ✅ Criado | 8 | Pré-requisito MS Graph |
| 22 | INT-MSG-003 | Calendar API | WT-998 | 🏷️ MVP P | 5 | Calendário MS |
| 23 | INT-MSG-004 | Teams Meeting API | WT-999 | 🏷️ MVP P | 5 | Reuniões Teams |
| 24 | INT-MSG-005 | Webhook Eventos | WT-1000 | 🏷️ MVP P | 3 | Eventos calendar |
| 25 | INT-MSG-006 | Token Refresh | WT-1001 | 🏷️ MVP P | 3 | Renovação OAuth |
| | | **— Templates Específicos —** | | | | |
| 26 | TPL-002 | Template Agendamento | WT-943 | 🏷️ MVP P | 3 | Template email agendamento |
| 27 | TPL-003 | Template Confirmação | WT-944 | 🔄 Revisão | 3 | Confirmação entrevista — já em revisão |
| 28 | TPL-004 | Template Pós-Entrevista | WT-945 | 🔄 Revisão | 3 | Pós-entrevista — já em revisão |
| | | **— Triagem e Follow-up —** | | | | |
| 29 | TRI-007 | Timeout e Retentativas | WT-922 | 🔨 In Prog | 5 | Já em desenvolvimento |
| 30 | TRI-009 | Templates de Mensagem | WT-924 | 🔄 Revisão | 5 | Já em revisão pré-MVP |
| 31 | TRI-010 | Envio em Massa/Bulk | WT-925 | 🔍 QA | 5 | Já em QA — completar |
| 32 | MAP-007 | Endpoint Busca Paginada | WT-1280 | 🏷️ MVP P | 5 | Paginação candidatos |
| | | **Subtotal P1** | | | **179** | **32 cards** |

### COULD HAVE (P2) — Adiável para Alpha 2

> Portar infraestrutura IA do protótipo + features de refinamento. Adiáveis sem comprometer teste interno.
>
> **O que é "Infraestrutura DDD" (PREP)?** São 14 cards de preparação estrutural para o sistema de IA em produção. DDD = Domain-Driven Design. Incluem: estrutura de diretórios do backend Python, contratos base (DomainPrompt ABC), pipeline de workflow de 7 etapas, roteador de domínios, sistema de prompts YAML, registros de tools, memória de conversação. 94% do código já existe no protótipo Replit — é portar e adaptar para produção.

| # | Card/Grupo | Título | Status Jira (rev.4) | Pts | Justificativa |
|---|------------|--------|:-----------:|:---:|---------------|
| 1 | SCO-008 | Histórico Scores | 🏷️ MVP P (WT-934) | 3 | Auditoria avançada — adiável |
| 2 | MAP-008~013 | Exclusão IDs, Like/Dislike, Reordenação | ✅ Criado (6 cards: WT-1456~WT-1461) | 20 | Refinamento de busca — adiável |
| 3 | TRI-011 | Pré-Qualificação | 📦 Backlog (WT-926) | 5 | Pré-filtro — adiável |
| | | **— IA: Infraestrutura DDD (PREP) —** | | | |
| 4 | PREP-001~014 | Estrutura DDD, Contratos, Registry, Router, Prompts, Tools, Memory, Migrations | ✅ Criado (14 cards: WT-1410~WT-1423) | 71 | Portar protótipo Python→produção. 94% portável |
| | | **— IA: Infraestrutura Core (INF) —** | | | |
| 5 | INF-001~008, 012, 014 | DomainPrompt, DomainWorkflow, CascadedRouter, FastRouter, EventDispatcher, ConversationMemory, FeatureFlags, OutputParser | ✅ Criado (9 cards: WT-1424~WT-1429). INF-010/011/013 equiv. ✅ Done | 56 | Portar protótipo. 75% aproveitável. INF S4 equiv. já feitos (WT-1006/1009/1011) |
| | | **— IA: Serviços de Domínio (SRV) —** | | | |
| 6 | SRV-001~016 | LLM, WSI, Scoring, JD, CV, Embedding, Sourcing, Scheduling, Email, WhatsApp, Teams, ATS, Automation | **SRV-001/008 ✅ Done; SRV-002/003 🔍 QA; SRV-004 🏷️ MVP P; SRV-009/012 ~70% Done** | 118 | **~60 pts já feitos/QA.** Esforço real: ~58 pts novos |
| | | **— IA: Agentes (AGT) —** | | | |
| 7 | AGT-000~011 | Orchestrator, Avaliador WSI, Triagem, Scheduling, Pipeline, Sourcing, Entrevistador, Feedback, ATS, TaskPlanner, Communication | **AGT-001/002/003 🏷️ MVP P** (WT-1223~1225); TRI-004 🔍 QA; AGE-001~008 🔍 QA | 108 | AGT-001/002/003 têm cards produto associados. 4 core com código no protótipo |
| | | **— IA: Automações (AUT) —** | | | |
| 8 | AUT-001~006 | Follow-up 7d, Timeout, Auto-pause, Cascatas | ✅ Criado (6 cards: WT-1445~WT-1450) | 33 | Automações avançadas. Código ref. para AUT-005/006 |
| | | **— IA: Transversais (TRV) —** | | | |
| 9 | TRV-001~005 | LGPD, Calibração Senioridade, Multi-Signal, Governança | **TRV-001 🔨 In Progress** (WT-920); TRV-003~005 ✅ Criado (WT-1451) | 37 | TRV-001 parcial via WT-920. Código no protótipo para TRV-003~005 |
| | | **— IA: Integrações Externas (INT-AI) —** | | | |
| 10 | INT-AI-001~005,007 | Gemini, Merge.dev, Mailgun, Pearch+Apify, MS Graph, WhatsApp | **INT-AI-001/005/007 ✅ Done**; INT-AI-004 🏷️ MVP P; INT-AI-002/003 ❌ Novo | 55 | **~39 pts já Done** (Gemini, MS Graph, WhatsApp). Esforço real: ~18 pts novos |
| | | **Subtotal P2** | | **~498** | **~63 cards IA + 9 produto** |

> **CRUZAMENTO JIRA rev.4:** Dos ~63 cards IA em P2, **~25 (39%) já têm trabalho significativo no Jira**. Esforço real de IA: ~38 cards novos (~300 pts), não 63 (478 pts). Ver seção 4B para detalhamento completo.

### WON'T HAVE (P3) — Excluído/Removido do Alpha 1

> **Limpeza rev.3 (26/fev/2026):** Dos ~90+ cards P3 originais, **45 foram deletados permanentemente** do Jira nesta sessão + 23 já não existiam. Restam ~50 cards P3 mantidos no backlog com labels organizacionais.

| # | Card | Título | Status Jira rev.3 | Motivo |
|---|------|--------|:-----------:|--------|
| | | **— MANTIDOS NO BACKLOG —** | | |
| 1 | AUTH-001~006 | Autenticação WorkOS/SSO (6 cards) | ✅ Done (WT-1201~1206) | Done — login simples ok para Alpha 1 |
| 2 | INT-WOS-001~007 | WorkOS Integration (7 cards) | 📦 Backlog (WT-1207~1213) | Alpha 2 — SSO/MFA/SCIM enterprise |
| 3 | NOT-002~006 | Notificações avançadas (5 cards) | 📦 Backlog | Alpha 2 — NOT-001 (bell básico) é P1 |
| 4 | CFG-001~005, IMP-001 | Config Admin (6 cards) | CFG-001/004 🏷️ MVP P; resto 📦 Backlog | Alpha 2 — configs hardcoded no Alpha 1 |
| 5 | WDT-008~030 | Otimização Busca (23 cards) | 📦 Backlog (WT-1311~1333) + label `otimizacao-de-busca` | Alpha 2+ — busca core já funciona |
| | | **— DELETADOS DO JIRA (rev.3) —** | | |
| 6 | ~~WSI-004~~ | ~~Edição Manual de Perguntas~~ | 🗑️ Deletado (WT-914) | REMOVIDO do escopo |
| 7 | ~~KAN-005~~ | ~~Ícones de Ação Rápida~~ | 🗑️ Deletado (WT-967) | OBSOLETO |
| 8 | ~~DEV-S1-001~~ | ~~Setup Inicial Projeto Rails~~ | 🗑️ Deletado (WT-43) | Rails não é Alpha 1 |
| 9 | ~~INT-LLM-001~007~~ | ~~Infra LLM avançada (8 cards)~~ | 🗑️ Deletados (WT-1195~1202) | Duplicados de SRV-001, INF-010/011/013 |
| 10 | ~~DEV-S3 (Stripe)~~ | ~~Billing/Stripe (4 cards)~~ | 🗑️ Deletados (WT-53~56) | Teste interno, sem billing |
| 11 | ~~DEV-S4 (HubSpot)~~ | ~~CRM Sync (2 cards)~~ | 🗑️ Deletados (WT-58~59) | CRM é Alpha 2+ |
| 12 | ~~DEV-S5 (Privacy)~~ | ~~Privacy Tools (3 cards)~~ | 🗑️ Deletados (WT-63~65) | LGPD avançado — TRV-001 básico suficiente |
| 13 | ~~VAG-079~087~~ | ~~Wizard Steps 3-11 (9 cards)~~ | 🗑️ Já não existiam (WT-358~366) | Wizard conversacional adiado |
| 14 | ~~VAG-088~107~~ | ~~APIs Rails (19 cards)~~ | 🗑️ Deletados (WT-367~386) | Alpha 1 roda com Python/Next.js |
| 15 | ~~VAG-109~122~~ | ~~Backend IA (14 cards)~~ | 🗑️ Já não existiam (WT-388~401) | Substituídos por SRV/AGT |
| 16 | ~~VAG-127~132~~ | ~~Governança/Calibração (6 cards)~~ | 🗑️ Deletados (WT-409~414) | Cobertos por TRV-003/005 |
| | | **— PROMOVIDOS PARA ALPHA 1 (rev.3) —** | | |
| 17 | VAG-123~126 | Saturação de Pipeline (4 cards) | 🏷️ Alpha 1 — Prioridade Alta (WT-405~408) + label `prioridade-alta` | Governança de triagem — ver seção 3.4 |

---

## 6. LISTA CONSOLIDADA DE TRABALHO — TODOS OS CARDS

> Time de 4 devs (2 front + 2 full-stack) decide quantos cards trabalhar por semana. Lista sem separação por sprint — o time prioriza pelo MoSCoW (P0 primeiro, depois P1, depois P2).

### 6.1 Cards de Desenvolvimento Novo (101 cards / 669 pts)

#### P0 — Must Have (14 cards / 105 pts)

| # | Card | Título | Jira Key | Status Jira | Pts | Área |
|---|------|--------|----------|:-----------:|:---:|------|
| | | **— Gates —** | | | | |
| 1 | GAT-001 | Gate 1: Aprovar Mapeados | WT-935 | 🏷️ MVP P | 8 | Front |
| 2 | GAT-002 | Gate 2: Aprovar Triados | WT-936 | 🏷️ MVP P | 8 | Front |
| 3 | GAT-003 | Modal de Reprovação | WT-937 | 🏷️ MVP P | 3 | Front |
| 4 | GAT-006 | Aprovação em Massa | WT-940 | 🏷️ MVP P | 5 | Front + Back |
| | | **— Scoring Core —** | | | | |
| 5 | SCO-001 | Cálculo Score WSI | WT-927 | 🏷️ MVP P | 13 | Back (IA) |
| 6 | SCO-004 | Parecer Textual LIA | WT-930 | 🏷️ MVP P | 8 | Back (IA) |
| | | **— Mapeamento + Preview —** | | | | |
| 7 | MAP-003 | Filtros Avançados | WT-907 | 🏷️ MVP P | 8 | Front + Back |
| 8 | MAP-004 | Adicionar Cand. à Vaga | WT-908 | 🏷️ MVP P | 5 | Front + Back |
| 9 | PRV-001 | Preview Lateral Cand. | WT-976 | 🏷️ MVP P | 5 | Front |
| 10 | PRV-002 | Tab Perfil | WT-977 | 🏷️ MVP P | 5 | Front |
| | | **— Comunicação + WhatsApp —** | | | | |
| 11 | TPL-001 | Template Abordagem Inicial | WT-942 | 🏷️ MVP P | 5 | Front + Back |
| 12 | TRI-001 | Config WhatsApp Business | WT-916 | 🏷️ MVP P | 8 | Back |
| 13 | INT-AI-007 | WhatsApp Business API (provider) | WT-1399 | ✅ Criado | 8 | Back |
| | | **— Bloqueante —** | | | | |
| 14 | PUB-001 | Página pública chat web | WT-1472 | ✅ Criado | 13 | Front + Back |
| | | **Subtotal P0** | | | **105** | |

#### P1 — Should Have (23 cards / 144 pts)

| # | Card | Título | Jira Key | Status Jira | Pts | Área |
|---|------|--------|----------|:-----------:|:---:|------|
| | | **— Scoring Completo —** | | | | |
| 15 | SCO-002 | Modelo Big Five (OCEAN) | WT-928 | 🏷️ MVP P | 8 | Back (IA) |
| 16 | SCO-003 | Avaliação Bloom/Dreyfus | WT-929 | 🏷️ MVP P | 8 | Back (IA) |
| 17 | SCO-005 | Visualização Score | WT-931 | 🏷️ MVP P | 5 | Front |
| 18 | SCO-006 | Breakdown Dimensões | WT-932 | 🏷️ MVP P | 8 | Front |
| 19 | SCO-007 | Comparação Candidatos | WT-933 | 🏷️ MVP P | 8 | Front + Back |
| | | **— Gates Completos —** | | | | |
| 20 | GAT-004 | Geração Feedback LIA | WT-938 | 🏷️ MVP P | 8 | Back (IA) |
| 21 | GAT-005 | Envio de Feedback | WT-939 | 🏷️ MVP P | 5 | Front + Back |
| 22 | GAT-007 | Histórico Decisões | WT-941 | 🏷️ MVP P | 5 | Front + Back |
| 23 | GAT-008 | Aprendizagem IA | WT-1298 | 🏷️ MVP P | 8 | Back (IA) |
| | | **— Templates —** | | | | |
| 24 | TPL-002 | Template Agendamento | WT-943 | 🏷️ MVP P | 3 | Front + Back |
| 25 | TPL-006 | Variáveis Dinâmicas | WT-947 | 🏷️ MVP P | 5 | Front + Back |
| 26 | TPL-007 | Preview de Template | WT-948 | 📝 TO DO | 3 | Front |
| | | **— Agendamento —** | | | | |
| 27 | AGE-002 | Consulta Disponibilidade | WT-950 | 🏷️ MVP P | 5 | Back |
| 28 | AGE-005 | Confirmação Candidato | WT-953 | 🏷️ MVP P | 5 | Front + Back |
| | | **— MS Graph —** | | | | |
| 29 | INT-MSG-002 | OAuth Flow MS | WT-1463 | ✅ Criado | 8 | Back |
| 30 | INT-MSG-003 | Calendar API | WT-998 | 🏷️ MVP P | 5 | Back |
| 31 | INT-MSG-004 | Teams Meeting API | WT-999 | 🏷️ MVP P | 5 | Back |
| 32 | INT-MSG-005 | Webhook Eventos | WT-1000 | 🏷️ MVP P | 3 | Back |
| 33 | INT-MSG-006 | Token Refresh | WT-1001 | 🏷️ MVP P | 3 | Back |
| | | **— Busca + UI —** | | | | |
| 34 | TAB-002 | Colunas Ordenáveis | WT-972 | 🏷️ MVP P | 3 | Front |
| 35 | MAP-005 | Matching Score IA | WT-909 | 🏷️ MVP P | 13 | Back (IA) |
| 36 | MAP-007 | Endpoint Busca Paginada | WT-1280 | 🏷️ MVP P | 5 | Back |
| 37 | NOT-001 | Sistema Bell | WT-957 | 📦 Backlog | 5 | Front + Back |
| | | **Subtotal P1** | | | **144** | |

#### P2 — Produto (9 cards / 28 pts)

| # | Card | Título | Jira Key | Status Jira | Pts | Área |
|---|------|--------|----------|:-----------:|:---:|------|
| 38 | SCO-008 | Histórico Scores | WT-934 | 🏷️ MVP P | 3 | Front + Back |
| 39 | MAP-008 | Paginação On-Demand | WT-1456 | ✅ Criado | 3 | Back |
| 40 | MAP-009 | Exclusão IDs no ES | WT-1457 | ✅ Criado | 3 | Back |
| 41 | MAP-010 | Exclusão IDs no PGV | WT-1458 | ✅ Criado | 3 | Back |
| 42 | MAP-011 | API Feedback Like/Dislike | WT-1459 | ✅ Criado | 3 | Back |
| 43 | MAP-012 | Componente Like/Dislike | WT-1460 | ✅ Criado | 5 | Front |
| 44 | MAP-013 | Remover Ord. por Ranking | WT-1461 | ✅ Criado | 3 | Front |
| 45 | TRI-011 | Pré-Qualificação | WT-926 | 📦 Backlog | 5 | Front + Back |
| 46 | KAN-011 | Triagem em Lote | WT-1462 | ✅ Criado | 5 | Front + Back |
| | | **Subtotal P2 Produto** | | | **28** | |

#### P2 — IA Novos (38 cards / 300 pts)

> ~70% têm código de referência no protótipo Replit. Ver seção 4B para detalhamento completo.

| # | Grupo | Cards | Status Jira | Pts | Área | Obs |
|---|-------|:-----:|:-----------:|:---:|------|-----|
| | **— Fundação IA (PREP) —** | | | | | |
| 47 | PREP-001~005 | 5 | ✅ Criado (WT-1410) | 31 | Back (IA) | Estrutura DDD, Contratos, Workflow, Registry, Router — 94% portável |
| 48 | PREP-006~009 | 4 | ✅ Criado (WT-1415) | 20 | Back (IA) | LLM Factory, Prompts YAML, Tool Registry, ConversationState |
| 49 | PREP-010~014 | 5 | ✅ Criado (WT-1419) | 20 | Back (IA) | Migrations, Mapa Equivalências, Diagrama, Robustness, Few-Shot |
| | **— Infraestrutura IA (INF) —** | | | | | |
| 50 | INF-001~004 | 4 | ✅ Criado (WT-1424) | 34 | Back (IA) | DomainPrompt, DomainWorkflow, CascadedRouter, FastRouter |
| 51 | INF-005, 008, 012, 014 | 4 | ✅ Criado (WT-1428) | 22 | Back (IA) | EventDispatcher, ConversationMemory, FeatureFlags, OutputParser |
| | **— Serviços (SRV — novos) —** | | | | | |
| 52 | SRV-010, 013, 016 | 3 | ✅ Criado (WT-1432) | 18 | Back (IA) | Scheduling, Teams, Automation |
| 53 | SRV-011, 014 | 2 | ✅ Criado (WT-1433) | 13 | Back (IA) | Email, ATS Sync |
| | **— Agentes (AGT — novos) —** | | | | | |
| 54 | AGT-000, 004, 006, 007 | 4 | ✅ Criado (WT-1437) | 47 | Back (IA) | Orchestrator, Pipeline Chat, Sourcing, Entrevistador — código no protótipo |
| 55 | AGT-008~011 | 4 | ✅ Criado (WT-1441) | 32 | Back (IA) | Feedback, ATS, TaskPlanner, Communication |
| | **— Automações (AUT) —** | | | | | |
| 56 | AUT-001~006 | 6 | ✅ Criado (WT-1445) | 33 | Back (IA) | Follow-up, Timeout, Auto-pause, Cascatas |
| | **— Transversais (TRV — novos) —** | | | | | |
| 57 | TRV-003~005 | 3 | ✅ Criado (WT-1451) | 29 | Back (IA) | Calibração Senioridade, Multi-Signal, Governança |
| | **— Integrações IA (INT-AI — novos) —** | | | | | |
| 58 | INT-AI-002, 003 | 2 | ✅ Criado (WT-1454) | 18 | Back (IA) | Merge.dev e Mailgun — integração nova |
| | | **Subtotal P2 IA** | | **300** | | |

#### Pipeline (10 cards / 62 pts)

> Todos sem card no Jira. Parcialmente cobertos por KAN (Done). Ver seção 3.

| # | Card | Título | Status Jira | Pts | Área |
|---|------|--------|:-----------:|:---:|------|
| 59 | PIP-001 | Arquitetura 3 Camadas | ✅ Criado (WT-1400) | 8 | Back |
| 60 | PIP-002 | Motor action_behavior | ✅ Criado (WT-1401) | 8 | Back |
| 61 | PIP-003 | UniversalTransitionModal | ✅ Criado (WT-1402) | 5 | Front |
| 62 | PIP-004 | use-transition-context | ✅ Criado (WT-1403) | 5 | Front |
| 63 | PIP-005 | Movimentação Livre | ✅ Criado (WT-1404) | 5 | Front + Back |
| 64 | PIP-006 | Badges nos Cards | ✅ Criado (WT-1405) | 3 | Front |
| 65 | PIP-007 | TransitionDispatchService | ✅ Criado (WT-1406) | 8 | Back |
| 66 | PIP-008 | Endpoints de Transição | ✅ Criado (WT-1407) | 8 | Back |
| 67 | PIP-009 | Pipeline CRUD | ✅ Criado (WT-1408) | 8 | Front + Back |
| 68 | PIP-010 | Barra de Ações em Massa | ✅ Criado (WT-1409) | 5 | Front |
| | | **Subtotal Pipeline** | | **62** | |

#### Gaps a Criar (7 cards / 30 pts)

| # | Card | Título | Status Jira | Pts | Área |
|---|------|--------|:-----------:|:---:|------|
| 69 | FLW-001 | Follow-up 7 dias | ✅ Criado (WT-1473) | 5 | Back |
| 70 | FLW-002 | Status "sem_resposta" | ✅ Criado (WT-1474) | 3 | Back |
| 71 | TRI-013 | Reporte Problemas Cand. | ✅ Criado (WT-1464) | 3 | Front |
| 72 | TPL-009 | Template Email Contato | ✅ Criado (WT-1475) | 3 | Front + Back |
| 73 | VAG-123 | Badge Pipeline Saturado | ✅ Criado (WT-1476) | 3 | Front |
| 74 | VAG-124 | Botão Desbloquear Pipeline | ✅ Criado (WT-1477) | 3 | Front |
| 75 | VAG-125/126 | APIs Saturação (back) | ✅ Criado (WT-1478) | 8 | Back |
| | | **Subtotal Gaps** | | **30** | |

---

### 6.2 Cards em Validação (20 cards / 115 pts)

> Não contam como trabalho de desenvolvimento novo. Precisam apenas de QA, aprovação de PR, completar revisão ou finalizar desenvolvimento em andamento.

#### QA — Validar e Passar (13 cards / 87 pts)

| # | Card | Título | Jira Key | Status Jira | Pts | Área | Ação |
|---|------|--------|----------|:-----------:|:---:|------|------|
| 1 | KAN-006 | Badge Score WSI | WT-968 | 📋 Code Review | 2 | Front | Aprovar PR |
| 2 | WIZ-008 | Form Edição Completa | WT-904 | 🔍 QA | 5 | Front | Validar QA |
| 3 | WSI-001 | Motor Geração Perguntas | WT-911 | 🔍 QA | 8 | Back (IA) | Validar QA |
| 4 | WSI-002 | Blocos Metodologia | WT-912 | 🔍 QA | 5 | Back (IA) | Validar QA |
| 5 | WSI-003 | Preview Perguntas | WT-913 | 🔍 QA | 5 | Front | Validar QA |
| 6 | WSI-005 | Aprovação Perguntas | WT-915 | 🔍 QA | 5 | Front | Validar QA |
| 7 | TRI-003 | Webhook Recebimento | WT-918 | 🔍 QA | 5 | Back | Validar QA |
| 8 | TRI-004 | Fluxo Conversacional LIA | WT-919 | 🔍 QA | 13 | Back (IA) | Validar QA — **P0 core** |
| 9 | TRI-010 | Envio em Massa/Bulk | WT-925 | 🔍 QA | 5 | Back | Validar QA |
| 10 | AGE-001 | Integração MS Graph | WT-949 | 🔍 QA | 13 | Back | Validar QA |
| 11 | AGE-003 | Sugestão Horários | WT-951 | 🔍 QA | 5 | Back (IA) | Validar QA |
| 12 | AGE-004 | Criação Evento Teams | WT-952 | 🔍 QA | 5 | Back | Validar QA |
| 13 | AGE-007 | Lembretes Automáticos | WT-955 | 🔍 QA | 3 | Back | Validar QA |
| | | **Subtotal QA** | | | **79** | | |

#### In Progress / Revisão — Completar (8 cards / 37 pts)

| # | Card | Título | Jira Key | Status Jira | Pts | Área | Ação |
|---|------|--------|----------|:-----------:|:---:|------|------|
| 14 | AGE-008 | Cancelamento | WT-956 | 🔍 QA | 3 | Back | Validar QA |
| 15 | TPL-005 | Editor de Templates | WT-946 | 🔨 In Progress | 8 | Front + Back | Completar dev |
| 16 | AGE-006 | Reagendamento | WT-954 | 🔨 In Progress | 5 | Back | Completar dev |
| 17 | TRI-007 | Timeout e Retentativas | WT-922 | 🔨 In Progress | 5 | Back | Completar dev |
| 18 | TRI-002 | Envio Mensagem Inicial | WT-917 | 🔄 Revisão | 5 | Back | Completar revisão |
| 19 | TPL-003 | Template Confirmação | WT-944 | 🔄 Revisão | 3 | Front + Back | Completar revisão |
| 20 | TPL-004 | Template Pós-Entrevista | WT-945 | 🔄 Revisão | 3 | Front + Back | Completar revisão |
| 21 | TRI-009 | Templates de Mensagem | WT-924 | 🔄 Revisão | 5 | Front + Back | Completar revisão |
| | | **Subtotal In Progress/Revisão** | | | **37** | | |

---

### 6.3 Resumo Geral

| Tipo | Cards | Pts | Status |
|------|:-----:|:---:|--------|
| **Desenvolvimento novo** | **101** | **669** | A iniciar — time prioriza P0→P1→P2 |
| **Validação (QA/CR/InProg/Revisão)** | **21** | **116** | Passáveis em paralelo ao dev |
| **TOTAL Alpha 1** | **122** | **785** | |

> **Nota:** Os 34 cards já Done (produto + IA equiv.) não aparecem aqui — já estão entregues.

---

## 7. MATRIZ DE RISCO

| # | Risco | Probabilidade | Impacto | Status | Mitigação |
|---|-------|:------------:|:-------:|:------:|-----------|
| 1 | Scoring (SCO-001~008) não pronto a tempo | Alta | Crítico | 8 cards 🏷️ MVP P (nenhum iniciado) | Priorizar SCO-001/004 como P0 Sprint 1. Scoring completo Sprint 2 |
| 2 | Gates (GAT-001~007) não iniciados | Alta | Crítico | 6 cards 🏷️ MVP P (nenhum iniciado) | Iniciar imediatamente Sprint 1 — são path crítico |
| 3 | Página pública triagem (PUB-001) não existe | Alta | Bloqueante | ✅ Criado (WT-1472) no Jira | **CRIAR CARD E INICIAR** — sem ela não há triagem web |
| 4 | WhatsApp provider não definido (Twilio vs Gupshup) | Alta | Crítico | TRI-001 🏷️ MVP P; INT-AI-007 ✅ Criado (WT-1399) | Definir provider imediatamente — WhatsApp é P0. Criar card INT-AI-007 |
| 5 | Deadlines Feb 20 já atrasados | Confirmado | Alto | SCO-005/006/007, GAT-004 atrasados | Replanejamento imediato — absorver nos Sprints 1-2 |
| 6 | Cards IA novos (~38) não portados do protótipo | Média | Alto | ~25/63 com trabalho existente; ~38 novos (~300 pts) | Sprint 3 dedicada. ~70% c/ código no protótipo. Se inviável, usar mocks/stubs |
| 7 | ~~Backend Rails (DEV-S1) não iniciado~~ | ~~Alta~~ | ~~Alto~~ | 🗑️ Deletado (WT-43) | **RESOLVIDO rev.3** — Alpha 1 roda com backend Python/Next.js. Card Rails deletado |
| 8 | 2 cards P0 sem representação no Jira | Confirmado | Bloqueante | PUB-001 e INT-AI-007 | Criar ambos imediatamente no Jira como P0 |

---

## APÊNDICE A — Distribuição de Status por Épico (Jira)

| Épico | Cards | ✅ Done | 🔍 QA | 🔨 In Prog | 📋 CR | 🏷️ MVP P | 📦 Bklog | 🔄 Rev | 📝 TODO | Total |
|-------|-------|:------:|:-----:|:---------:|:-----:|:--------:|:-------:|:------:|:-------:|:-----:|
| É1 — Login + Dashboard | VAG-001, VAG-002, VAG-007, VAG-008 | 4 | — | — | — | — | — | — | — | 4 |
| É2 — Editar Vaga | WIZ-008, VAG-003, VAG-004 | 2 | 1 | — | — | — | — | — | — | 3 |
| É3 — Roteiro WSI | WSI-001, WSI-002, WSI-003, WSI-004*, WSI-005 | — | 4 | — | — | — | 1* | — | — | 5 |
| É4 — Mapeamento | MAP-001~007, INT-APY-001~003 | 3 | — | — | — | 7 | — | — | — | 10 |
| É5 — Pipeline Kanban | KAN-001~008, TAB-001~005, PRV-001~005 | 13 | — | — | 1 | 3 | 1* | — | — | 18 |
| É5 — Gate 1 | GAT-001, GAT-003~007 | — | — | — | — | 6 | — | — | — | 6 |
| É6 — Contato Email | TPL-001, TPL-005~007, TRI-002, TRI-009, TRI-010, NOT-001 | — | 1 | 1 | — | 2 | 1 | 2 | 1 | 8 |
| É7 — Triagem WSI | TRI-001, TRI-003~006, TRI-008, TRI-011 | — | 2 | 3 | — | 1 | 1 | — | — | 7 |
| É7B — Scoring WSI | SCO-001~008 | — | — | — | — | 8 | — | — | — | 8 |
| É8 — Gate 2 | GAT-002, GAT-008 | — | — | — | — | 2 | — | — | — | 2 |
| É9A — Agendamento | AGE-001~008, INT-MSG-003~006, TPL-002, TPL-003 | — | 5 | 1 | — | 5 | 1 | 1 | — | 13 |
| É9B — Feedback Final | TPL-004 | — | — | — | — | — | — | 1 | — | 1 |
| IA — Agentes | AGT-001, AGT-002, AGT-003 | — | — | — | — | 3 | — | — | — | 3 |
| AUTH (Done) | AUTH-001~006 | 4 | — | — | — | — | — | — | — | 4 |
| **TOTAL** | | **26** | **13** | **5** | **1** | **37** | **5** | **4** | **1** | **92** |

> \* WSI-004 (REMOVIDO) e KAN-005 (OBSOLETO) — deletados do Jira na limpeza rev.3
>
> **Cards sem representação no Jira (não contabilizados acima):**
> - PIP-001~010 (Pipeline — 10 cards, 62 pts) — parcialmente cobertos por KAN-001~008
> - PREP-001~014, INF-001~014, SRV-001~016, AGT-000/004~011, AUT-001~006, TRV-001~005, INT-AI-001~007 (~60 cards IA, 478 pts)
> - PUB-001, PUB-002, FLW-001, FLW-002, TRI-015~017, KAN-005*, TPL-009, TPL-010 (10 gaps a criar, 56 pts)

---

*Documento atualizado em 25/fev/2026 (rev.2) para suporte à negociação de prioridades do MVP Alpha 1.*
*Alterações rev.2: WhatsApp movido para P0; P2 itens realocados para P0/P1; coluna Status Jira em todas as tabelas; sprints detalhados card-a-card; Apêndice A com relação de cards por épico.*
*Dados do Jira: API REST + Screenshots do backlog (240 work items).*
*Referência: `docs/mvp-alpha-scenarios.md` v2.9 (168 cards planejados).*

*rev.3 (26/fev/2026) — Limpeza do Jira:*
*- 45 cards deletados permanentemente: Stripe/Billing (4), HubSpot/CRM (2), Privacy Tools (3), APIs Rails (19), Infra LLM avançada (8), VAG Governança/Calibração (6), Avulsos P3 (3)*
*- 23 cards já não existiam: Wizard Steps (9), Backend IA duplicados (14)*
*- 27 cards mantidos com labels organizacionais: WDT (23 + label `otimizacao-de-busca`), Saturação (4 + label `prioridade-alta`)*
*- 4 cards de saturação (WT-405~408) promovidos para Alpha 1 como prioridade alta*
*- 1 card recriado: WT-1398 (VAG-106 API Integração WorkOS) em Done*
*- Risco #7 (Backend Rails) resolvido — Alpha 1 roda com Python/Next.js*
*- Seções 3.1~3.4 e P3 atualizadas com status de cada card pós-limpeza*
*- Backlog reduzido de ~240 para ~172 work items*

*rev.4 (26/fev/2026) — Cruzamento Jira × Cards IA:*
*- Cruzamento dos 63 cards IA planejados com estado real do Jira (478 cards WT consultados)*
*- Tabelas PREP/INF/SRV/AGT/AUT/TRV/INT-AI atualizadas com status real, % feito e referências Jira*
*- Nova seção 4B "CRUZAMENTO JIRA REAL × CARDS IA" com 3 tabelas: Done (~8 cards/85pts), Em Andamento (~10/80pts), Novo (~38/300pts)*
*- Tabela P2 MoSCoW atualizada com status real de cada grupo IA*
*- Snapshot atualizado com indicadores de cruzamento*
*- Conclusão: esforço real IA = ~38 cards novos (~300 pts), não 63 (478 pts)*
*- mvp-alpha-scenarios.md: coluna "Status Jira" adicionada em todas as tabelas (É1~É9B, PIP, Semana 2 e 3)*

*rev.5 (26/fev/2026) — Correção de incoerências e visão consolidada:*
*- Snapshot reescrito: 4 sub-seções (Produto, IA, "Quantos precisam ser trabalhados?", Limpeza)*
*- Resposta consolidada: ~63 cards com avanço, ~38 prontos p/ iniciar, ~71 precisam de trabalho novo*
*- Conclusão e "Implicação para negociação" atualizadas com números consolidados (produto + IA equiv.)*
*- Seção 4 (gap table): nova coluna "Trabalho Existente" e "Gap Real" descontando equivalentes Jira*
*- É4 Resultado corrigido: era "3 Done, 1 QA, 6 MVP P" → "3 Done, 7 MVP P, 6 sem card"*
*- AGT-001/002/003 padronizados como 🏷️ MVP P em todas as seções (era Backlog em É7 e Sprint 3)*
*- Apêndice A: É4 corrigido (4→7 MVP P, total 7→10), AGT corrigido (Backlog→MVP P), totais recalculados*
*- Sprint 3: nota atualizada — esforço real ~38 cards novos / ~300 pts (não 63 / 470)*
*- Cenário Mínimo: incorpora dados rev.4 de IA já feita*
*- Risco #6: atualizado de "0/63" para "~25 com trabalho / ~38 novos"*
*- MoSCoW P2: nota de esforço real rev.4 adicionada*
