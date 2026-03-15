# Diagnostico Completo dos Prompts e IA da Plataforma LIA

**Data:** 2026-03-12
**Versao:** 1.0

---

## 1. RESUMO EXECUTIVO

A plataforma LIA possui 6 prompts/assistentes de IA especializados, cada um com seu dominio de atuacao. Esta auditoria cobre arquitetura, capacidades, falhas, oportunidades de melhoria e correcoes aplicadas.

### Status Geral

| Prompt | Arquivos | Status | Bugs Corrigidos |
|:---|:---|:---|:---|
| 1. Funil de Talentos | `talent_assistant_prompts.py` | Funcional com correcoes | 2 |
| 2. Tabela de Vagas | `jobs_management_prompts.py` | Funcional com correcoes | 2 |
| 3. Kanban (Dentro de Vagas) | `kanban_assistant_prompts.py` | Funcional com correcoes | 3 |
| 4. LIA Float (Geral) | `orchestrator.py` + hooks | Funcional | 0 |
| 5. Wizard de Criacao | `wizard_system_prompt.py` | Funcional | 0 |
| 6. Politicas de Contratacao | `policy_system_prompt.py` | Funcional | 0 |

---

## 2. BUGS CORRIGIDOS (P0/P1)

### BUG-1: Deteccao de keywords sem negacao (P0 — Corrigido)

**Impacto:** Alto — mensagens como "nao quero ranking" eram classificadas como intent "rankear_candidatos"

**Arquivos afetados:**
- `talent_assistant_prompts.py` — `detect_talent_command_type()`
- `jobs_management_prompts.py` — `detect_jobs_command_type()`
- `kanban_assistant_prompts.py` — `detect_command_type()`

**Correcao aplicada:** Adicionada funcao `_is_negated()` que verifica uma janela de 25 caracteres antes da keyword por prefixos de negacao (`nao quero`, `sem`, `ignore`, etc.). Lista de 18 prefixos de negacao em PT-BR com e sem acentos.

### BUG-2: Confianca artificial inflada (P0 — Corrigido)

**Impacto:** Alto — a formula `max(0.6, min(best_score * 3, 0.95))` garantia confianca minima de 0.6 mesmo com match fragil e 0.5 sem match algum. Isso impedia o fallback correto para LLM na funcao `_enhanced`.

**Arquivos afetados:** Mesmos 3 arquivos acima.

**Correcao aplicada:**
- Talent/Jobs: `min(0.5 + best_score * 2, 0.95)` — confianca proporcional ao match real
- Kanban: `min(0.5 + best_score * 0.15, 0.95)` — escala diferente pois kanban usa score cumulativo
- Default sem match: `0.4` (antes era `0.5`) — permite que o threshold de 0.7 no `_enhanced` sempre acione o fallback LLM

### BUG-3: Name matching fragil no Kanban (P1 — Corrigido)

**Impacto:** Medio — `target_name in candidate_name or candidate_name in target_name` causava false positives ("Ana" matchava "Mariana", "Carlos" matchava "Carlos Alberto" mas tambem matchava "Nao Carlos")

**Arquivo:** `kanban_assistant_prompts.py` — `resolve_ui_action()`

**Correcao aplicada:** Minimo de 3 caracteres para match. Matching baseado em partes de palavras: exige que TODAS as palavras do nome-alvo estejam presentes no nome do candidato (ou vice-versa). Ex: "Ana Silva" matcha "Ana Maria Silva" mas "Ana" sozinho nao matcha "Mariana".

---

## 3. ANALISE DETALHADA POR PROMPT

### 3.1 Prompt do Funil de Talentos

**Arquivo:** `talent_assistant_prompts.py` (606 linhas)
**Frontend:** `expandable-ai-prompt.tsx` (4.309 linhas)
**Scope:** `TALENT_FUNNEL` — 19 tools (11 query + 8 action)

**Capacidades:**
- 13 tipos de comando com templates especializados
- Deteccao hibrida: keywords (rapida) + fallback LLM
- Construcao de contexto rica com metricas do pool
- Resposta JSON estruturada

**Gaps identificados:**
- Sem memoria de conversa entre analises
- Tools de action (mover, rejeitar, email) existem no scope mas nao sao invocadas pelo prompt
- `get_ml_predictions` e `get_conversion_patterns` disponiveis mas nao usados
- Limite de 10 candidatos no contexto (`sorted_cands[:10]`)
- Frontend monolitico (4.309 linhas)

**Prioridade de melhorias:**
1. (Alta) Integrar `get_ml_predictions` para previsao de dropout
2. (Media) Adicionar memoria de sessao
3. (Baixa) Quebrar `expandable-ai-prompt.tsx` em componentes menores

### 3.2 Prompt da Tabela de Vagas

**Arquivo:** `jobs_management_prompts.py` (455 linhas)
**Scope:** `JOB_TABLE` — 19 tools (12 query + 7 action)

**Capacidades:**
- 12 tipos de analise com dashboard executivo
- Deteccao hibrida padronizada
- Resolucao de acoes UI (`resolve_jobs_ui_action`)

**Gaps identificados:**
- Templates pedem "comparativo com periodo anterior" mas nao ha pipeline temporal
- `get_market_benchmarks` nao injeta dados automaticamente no contexto
- Formato do `jobs_context` depende 100% do frontend — campos vazios empobrecem o prompt
- Sem alertas proativos quando SLAs vencem

**Prioridade de melhorias:**
1. (Alta) Adicionar pipeline de dados temporal para tendencias reais
2. (Media) Integrar alertas proativos via `get_smart_alerts`
3. (Baixa) Cross-reference automatico com dados de mercado

### 3.3 Prompt do Kanban (Dentro de Vagas)

**Arquivo:** `kanban_assistant_prompts.py` (1.238 linhas)
**Scope:** `IN_JOB` — 26 tools (14 query + 12 action)

**Capacidades:**
- 18 tipos de comando (o mais completo dos 3)
- HITL para acoes destrutivas
- Fluxo progressivo para emails (3 etapas)
- Confirmacao dupla para rejeicao

**Gaps identificados:**
- Templates JSON enormes (30+ linhas de formato obrigatorio) — alto consumo de tokens
- Sem validacao de etapa destino valida em `mover_candidato`
- Duplicacao significativa com prompt do funil (ranking, comparacao, top candidatos)
- Sem sugestoes proativas automaticas

**Prioridade de melhorias:**
1. (Alta) Validar etapa destino contra pipeline da vaga
2. (Media) Refatorar templates JSON para reduzir consumo de tokens
3. (Baixa) Unificar logica duplicada com funil de talentos

### 3.4 Prompt Geral Flutuante (LIA Float)

**Arquivos:** `orchestrator.py`, `intent_router.py`, `cascaded_router.py`
**Frontend:** `LiaChatPanel.tsx`, `use-float-streaming.ts`

**Capacidades:**
- Roteamento em 6 tiers (Memory → Redis → Vector → Fast → LLM → Clarification)
- 9 agentes roteáveis
- WebSocket streaming com HITL
- Cache semantico (MD5 + pgvector)

**Gaps identificados:**
- Routing depende de LLM cascade (Haiku → Sonnet → Opus) — latencia alta
- Sem fallback graceful se todos os 3 provedores falharem
- Sem metricas de routing accuracy

**Prioridade de melhorias:**
1. (Alta) Adicionar metricas de routing accuracy
2. (Media) Otimizar cascade com modelo mais leve (regex/embedding) antes do LLM
3. (Baixa) Implementar fallback para mensagem generica se todos os provedores falharem

### 3.5 Wizard de Criacao de Vagas

**Arquivo:** `wizard_system_prompt.py` (231 linhas)
**Frontend:** `WizardContainer.tsx`

**Capacidades:**
- 6 estagios de criacao guiados por conversa
- Extracao automatica de campos de linguagem natural
- Contra-argumentacao com benchmarks salariais
- Anti-sycophancy explicito
- Compliance LGPD e fairness integrados no prompt

**Gaps identificados:**
- Nao usa `get_company_context` automaticamente no inicio
- Calibracao por contexto (startup/PME/corporacao) depende de ferramenta nao chamada automaticamente
- Regra de `generate_enriched_jd` autonoma pode causar chamadas duplicadas se o endpoint tambem disparar

**Prioridade de melhorias:**
1. (Media) Auto-chamada de `get_company_context` no primeiro turno
2. (Baixa) Deduplicar chamada de `generate_enriched_jd` entre agente e endpoint

### 3.6 Politicas de Contratacao

**Arquivo:** `policy_system_prompt.py` (273 linhas)
**Frontend:** `HiringPoliciesHub.tsx`

**Capacidades:**
- 5 blocos tematicos de configuracao
- Validacao etica e compliance ANTES de salvar
- Raciocinio consultivo com trade-offs
- Anti-sycophancy e contra-argumentacao fortes
- Calibracao por porte e setor da empresa

**Gaps identificados:**
- Nao persiste motivo quando recrutador insiste apos alerta (apenas menciona no texto)
- Sem historico de mudancas de politica (quem mudou, quando, de que para que)
- Sem integracao com dashboard de compliance

**Prioridade de melhorias:**
1. (Media) Registrar no audit log quando recrutador insiste apos alerta
2. (Baixa) Adicionar historico de mudancas de politica

---

## 4. PADRONIZACAO CROSS-PROMPT

### 4.1 Padroes ja padronizados (positivos)

| Padrao | Status | Arquivos |
|:---|:---|:---|
| Identidade LIA | Consistente | Todos os 6 prompts |
| Anti-sycophancy | Consistente | Todos os 6 prompts |
| Tratamento de erros | Consistente | Todos os 6 prompts |
| Confirmacoes PT-BR | Consistente | Todos os 6 prompts |
| Negation detection | Padronizado (corrigido) | talent, jobs, kanban |
| Confianca realista | Padronizado (corrigido) | talent, jobs, kanban |

### 4.2 Inconsistencias identificadas

| Aspecto | Talent | Jobs | Kanban | Wizard | Policy |
|:---|:---|:---|:---|:---|:---|
| Formato resposta | JSON obrigatorio | JSON obrigatorio | JSON obrigatorio (templates enormes) | Portugues natural | Portugues natural |
| Anti-sycophancy | 5 regras | 5 regras | 5 regras | 5 regras + verificacao de premissas | 5 regras + verificacao de premissas + contra-argumentacao |
| Compliance/Fairness | Basico | Basico | Basico | Detalhado (leis citadas) | Detalhado (leis citadas) |
| Tools scope | 19 | 19 | 26 | Variavel por estagio | 8 |

### 4.3 Duplicacao de codigo

Funcoes duplicadas entre os 3 arquivos de deteccao:
- `detect_*_command_type()` — mesma logica, mesma formula
- `_is_negated()` — identica nos 3 arquivos
- `NEGATION_PREFIXES` — identica nos 3 arquivos
- `detect_*_command_type_enhanced()` — mesma logica de fallback LLM

**Recomendacao:** Extrair para modulo compartilhado `app/shared/intent/keyword_detector.py`

---

## 5. INFRAESTRUTURA DE PROMPTS

### 5.1 Sistemas de gerenciamento existentes

| Sistema | Arquivo | Status |
|:---|:---|:---|
| PromptTemplate (Pydantic) | `shared/prompts/templates.py` | Ativo — usado pelo wizard |
| PromptLibrary (singleton) | `shared/prompts/templates.py` | Ativo — registro de templates |
| PromptRegistry (versionado) | `shared/prompts/prompt_registry.py` | Ativo — 14 prompts registrados |
| PromptLoader (YAML) | `shared/prompts/loader.py` | Ativo — carrega de YAML |
| agent_prompts.yaml | `prompts/shared/agent_prompts.yaml` | Ativo — 1.687 linhas |

### 5.2 Gaps de infraestrutura

1. **3 sistemas paralelos:** PromptLibrary, PromptRegistry e PromptLoader fazem coisas similares sem integracao
2. **Prompts inline vs YAML:** Wizard usa PromptTemplate, kanban/talent/jobs usam strings inline, agent_prompts usa YAML
3. **Sem A/B testing:** Nao ha mecanismo para testar variantes de prompts
4. **Sem metricas de performance:** Nao se sabe qual prompt gera melhores respostas

---

## 6. PRIORIZACAO DE CORRECOES VS MELHORIAS

### Correcoes (ja aplicadas)

| ID | Descricao | Severidade | Status |
|:---|:---|:---|:---|
| BUG-1 | Negation detection em keyword matching | P0 | Corrigido |
| BUG-2 | Confianca artificial inflada | P0 | Corrigido |
| BUG-3 | Name matching fragil no Kanban | P1 | Corrigido |

### Melhorias priorizadas (backlog)

| ID | Descricao | Impacto | Esforco | Prioridade |
|:---|:---|:---|:---|:---|
| M-1 | Extrair intent detection para modulo compartilhado | Alto (manutencao) | Medio | P1 |
| M-2 | Integrar `get_ml_predictions` no funil de talentos | Alto (valor) | Baixo | P1 |
| M-3 | Validar etapa destino em `mover_candidato` | Alto (corretude) | Baixo | P1 |
| M-4 | Adicionar memoria de sessao ao funil de talentos | Medio (UX) | Medio | P2 |
| M-5 | Pipeline de dados temporal para tendencias em Jobs | Medio (valor) | Alto | P2 |
| M-6 | Unificar 3 sistemas de gerenciamento de prompts | Medio (arquitetura) | Alto | P2 |
| M-7 | Reduzir templates JSON do Kanban (consumo de tokens) | Medio (custo) | Medio | P2 |
| M-8 | Quebrar `expandable-ai-prompt.tsx` em componentes | Baixo (manutencao) | Medio | P3 |
| M-9 | Adicionar metricas de routing accuracy ao Float | Baixo (observabilidade) | Medio | P3 |
| M-10 | A/B testing de variantes de prompts | Baixo (otimizacao) | Alto | P3 |
