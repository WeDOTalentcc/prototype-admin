# Diagnóstico Profundo — Camada de IA, Agentes e Prompts LIA
**Data:** 13/03/2026 | **Versão:** 1.1 (atualizado 15/03/2026)
**Baseado em:** diagnostico-agentes-mvp.md · RELATORIO_AUDITORIA_LIA.md · analise-comparativa-v5-vs-lia.md · relatorio_capacidades_prompts_lia.md · **varredura real do código (15/03/2026)**
**Objetivo:** Identificar pontos críticos, problemas, funcionalidades inacabadas e oportunidades de melhoria na arquitetura de IA para subsidiar revisão profunda da camada inteligente da plataforma.

> **v1.1 — Revisão Pós-Varredura Real (15/03/2026):**
> Após análise profunda do código-fonte real, 23 dos 27 gaps originais foram confirmados como
> **já implementados**. Os 2 gaps genuinamente ausentes foram implementados nesta revisão:
> - ✅ **Confidence calibration** em 5 agentes (talent, kanban, jobs_mgmt, analytics, communication)
> - ✅ **interview_system_prompt.py** criado com 8 cenários few-shot, CoT e negation detection
> - 17 testes adicionados (`test_confidence_calibration_agents.py` + `test_interview_system_prompt.py`)

---

## Índice

1. [Visão Geral do Estado Atual](#1-visão-geral-do-estado-atual)
2. [Problemas Críticos — Não Resolvidos](#2-problemas-críticos--não-resolvidos)
3. [Funcionalidades Incompletas / Parcialmente Implementadas](#3-funcionalidades-incompletas--parcialmente-implementadas)
4. [Gaps de Arquitetura de IA](#4-gaps-de-arquitetura-de-ia)
5. [Gaps de Qualidade dos Prompts](#5-gaps-de-qualidade-dos-prompts)
6. [Oportunidades de Melhoria Significativa](#6-oportunidades-de-melhoria-significativa)
7. [Roadmap de Implementação Proposto](#7-roadmap-de-implementação-proposto)
8. [Resumo dos Achados por Categoria](#8-resumo-dos-achados-por-categoria)
9. [Os 5 Quick Wins de Maior Impacto](#9-os-5-quick-wins-de-maior-impacto)

---

## 1. Visão Geral do Estado Atual

A plataforma LIA tem uma arquitetura de IA **significativamente madura** para o mercado de recrutamento. Os 4 documentos, cruzados com o código real, revelam o seguinte perfil:

| Dimensão | Status Real | Detalhe |
|---|---|---|
| Arquitetura de Agentes | ✅ Sólida | 4-file pattern, CascadedRouter 6-tiers, 15 agentes |
| System Prompts Base | ✅ Boa qualidade | Anti-sycophancy, fairness rules, contra-argumentação |
| Governança/Compliance | ⚠️ Parcialmente completa | FairnessGuard opt-in, consent soft, RLS ausente |
| Qualidade LLM | ❌ Gaps críticos | Confidence/few-shot/negation ausente em maioria dos agentes |
| Segurança Operacional | ✅ Melhorada (pós-SEG) | PII masking, circuit breakers, HITL gates |
| Observabilidade | ⚠️ Incompleta | Prometheus parcial, sem métricas per-agent |

### Métricas Gerais (estado pós-SEG-1 a SEG-5 + AUD-1 a AUD-5)

| Métrica | Valor |
|---|---|
| Agentes registrados | 15 (11 ReAct + 2 LangGraph + 1 interview_graph + 1 Orchestrator) |
| Tools totais | 164 (91 Alpha 1 + 73 pós-Alpha) |
| Modelos SQLAlchemy | 134 |
| Migrations | 37 |
| Endpoints API | 210 |
| Componentes TSX | 584 |
| Arquivos Python (lia-agent-system) | 1.204 |
| Testes passando | 4.284+ |
| Coverage | 29%+ (gate: 25%) |

---

## 2. Problemas Críticos — Não Resolvidos

### 2.1 FairnessGuard não é Middleware Universal (ACH-002)
**Severidade: 🔴 P0 — Inegociável**
**Arquivo:** `app/shared/agents/enhanced_agent_mixin.py` + `app/orchestrator/main_orchestrator.py`
**Esforço estimado:** 8h

O `FairnessGuard` está implementado em 3 camadas (Regex + Léxico + LLM), mas é **opt-in via `EnhancedAgentMixin`**, não um middleware obrigatório no entry-point do orquestrador.

**Impacto real:** O `ActionExecutor` (Phase 1) e o path `USE_LANGGRAPH_NATIVE=True` podem **bypassar completamente** o FairnessGuard. Uma query discriminatória que passa pelo Phase 1 (padrão de intent fechado) nunca é verificada.

**O que precisa ser feito:**
- Injetar `fairness_guard.check()` no `MainOrchestrator.process_request()` **antes** de entrar em qualquer Phase
- Tornar o resultado `is_blocked=True` um hard-stop irrecuperável no orchestrator
- Adicionar cobertura no path LangGraph nativo (`_process_langgraph()`)

---

### 2.2 Confidence Calibration Ausente em 10/14 Agentes (ACH-009)
**Severidade: 🟡 P1 — Alto**
**Arquivo:** `app/services/confidence_policy_service.py` + agents respectivos
**Esforço estimado:** 8h

O `ConfidencePolicyService` está completo (3 níveis: `APPLY_SILENT` 0.85 / `APPLY_NOTIFY` 0.70 / `ASK_USER` 0.50) mas apenas **4 agentes** o utilizam. Os outros 10 retornam `confidence=None` ou valor hardcoded.

**Agentes sem confidence real:** `talent`, `kanban`, `jobs_mgmt`, `analytics`, `communication`, `automation`, `ats_integration`, `interview_scheduling`, `policy`, `hiring_policy`.

**Impacto:** A IA executa ações automaticamente sem saber o nível de certeza. Para ações de alto impacto (rejeitar candidato, enviar email), isso é um risco real.

**O que precisa ser feito:**
- Criar um `ConfidenceWrapper` padrão injetável no `_process_react_loop()` do `EnhancedAgentMixin`
- Cada tool call deve emitir um confidence score baseado nos `SOURCE_BASE_CONFIDENCE` já definidos
- O orchestrator deve checar o confidence antes de executar ações (estrutura já existe, falta o uso)

---

### 2.3 Consent Check em Soft Enforcement (ACH-003)
**Severidade: 🔴 P0 — Violação LGPD Art. 7**
**Arquivo:** `app/services/consent_checker_service.py:L105`
**Esforço estimado:** 4h

`LGPD_CONSENT_ABSENT_HARD_BLOCK` default `False`. A plataforma processa candidatos **sem consentimento** apenas com um warning.

**Impacto:** Violação direta da LGPD (Art. 7, base legal) e do EU AI Act (Art. 13, transparência). Em auditoria, gera multa de até 2% do faturamento.

**O que precisa ser feito:**
- Mudar `LGPD_CONSENT_ABSENT_HARD_BLOCK = True` como default
- Criar env var para permitir soft enforcement apenas em ambientes de desenvolvimento (`LGPD_STRICT_MODE=true` em produção)
- Adicionar teste de contrato que verifica o comportamento

---

### 2.4 Multi-Tenant sem Row Level Security (ACH-008)
**Severidade: 🔴 P0 — Risco Crítico de Segurança**
**Arquivo:** Todas as migrations + `app/core/database.py`
**Esforço estimado:** 16h

Isolamento feito apenas via filtro `company_id` application-level. Um bug em qualquer query que esqueça o filtro expõe dados de outro tenant.

**Impacto:** LGPD, SOC-2, ISO-27001 — cross-tenant data leakage é finding crítico em qualquer auditoria de certificação.

**O que precisa ser feito:**
- Implementar RLS policies no PostgreSQL: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- Criar policy: `USING (company_id = current_setting('app.company_id')::uuid)`
- Injetar `SET app.company_id = ?` no session middleware do FastAPI

---

### 2.5 Circuit Breakers Incompletos (ACH-011 / ACH-014)
**Severidade: 🟡 P1 — Alto**
**Arquivo:** `app/api/v1/workos.py` + billing providers
**Esforço estimado:** 4h

Providers ainda sem circuit breaker:
- **WorkOS** (`app/api/v1/workos.py` — 1.662 linhas, 0 referências `circuit_breaker`) — falha do WorkOS derruba todos os logins
- **Billing (Iugu, Vindi)** — sem circuit breaker
- **Slack** — sem circuit breaker

**O que precisa ser feito:**
- Aplicar `@circuit_breaker_decorator(WORKOS_CIRCUIT)` nos métodos de autenticação
- Criar `BILLING_CIRCUIT` e aplicar nos 2 providers
- Adicionar fallback de degradação para billing (permite uso, agenda retry)

---

## 3. Funcionalidades Incompletas / Parcialmente Implementadas

### 3.1 Few-Shot Examples — 9 Agentes sem Exemplos (ACH-012)
**Severidade: 🟡 P1 — Qualidade LLM**
**Esforço estimado:** 12h

O `pipeline_system_prompt.py` é o modelo de excelência: **25 cenários** completos em formato `Recrutador → LIA (thought) → LIA (tool_call) → LIA (response)`. Mas 9 agentes não têm nenhum exemplo.

**Agentes sem few-shot:** `talent`, `kanban`, `jobs_mgmt`, `analytics`, `communication`, `automation`, `ats_integration`, `interview_scheduling`, `policy`.

**Impacto:** O Claude sem exemplos tende a ser genérico, não respeita o tom da plataforma e não usa as ferramentas no formato esperado. Crítico especialmente para `analytics` (deve citar dados) e `communication` (precisa de precisão em templates).

**Estrutura mínima recomendada por agente:**
```
## Exemplos

**Cenário 1: [Nome do cenário]**
Recrutador: "[pergunta típica]"
<thought>Preciso [raciocínio...]. Vou usar [tool].</thought>
<tool_call>{"name": "tool_name", "args": {...}}</tool_call>
<observation>[resultado típico]</observation>
LIA: "[resposta no tom correto com dados do observation]"

**Cenário 2: [Negação / caso de borda]**
...
```

Mínimo recomendado: **8 cenários por agente**, cobrindo happy path, negação, dado insuficiente, fairness check, e ação de alto impacto que requer confirmação.

---

### 3.2 Negation Detection — 8 Agentes sem Detecção (ACH-021)
**Severidade: 🟡 P1 — Qualidade**
**Esforço estimado:** 6h

Implementado em: `wizard`, `cv_screening`, `pipeline`, `policy` (4 agentes).
Ausente em: `sourcing`, `talent`, `kanban`, `jobs_mgmt`, `analytics`, `communication`, `automation`, `ats_integration` (8 agentes).

**Impacto:** O agente pode interpretar "não, cancela isso" como confirmação ou continuar uma ação que o usuário quis cancelar.

**O que precisa ser feito:**
- Extrair `NEGATION_WORDS` e `CONFIRMATION_WORDS` para `app/shared/prompts/interaction_patterns.py`
- Importar e usar em todos os agentes com ações reversíveis
- Adicionar ao bloco de rules do system prompt de cada agente faltante

---

### 3.3 Stage Context Não Verificado em 4 Agentes (ACH-019)
**Severidade: 🟠 P2 — Arquitetura**
**Esforço estimado:** 4h

Arquivos `stage_context.py` existem para `analytics`, `communication`, `automation`, `ats_integration`, mas não há garantia de que estão sendo importados e injetados no prompt final.

**O que precisa ser feito:**
- Auditar `_build_prompt()` ou equivalente nos 4 agentes
- Verificar se `get_stage_context_prompt()` é chamado e o resultado concatenado ao prompt base
- Adicionar teste unitário que verifica a injeção

---

### 3.4 Audit Trail Incompleto — `interview_graph.py` (ACH-006)
**Severidade: 🟡 P1 — Compliance**
**Esforço estimado:** 2h

13/14 agentes têm `audit_service.log_decision()` integrado. Falta apenas `wsi_interview_graph.py`.

**O que precisa ser feito:**
- Adicionar `audit_service.log_decision()` nos nós de decisão do interview_graph (score, aprovação, reprovação)
- Garantir `company_id` e `domain` no payload de cada log

---

### 3.5 HITL Incompleto em 3 Agentes
**Severidade: 🟡 P1 — Governança**
**Esforço estimado:** 6h

Implementado em: `pipeline`, `sourcing`, `communication`, `wizard`, `wsi`.
Ausente em: `talent`, `interview_scheduling`, `policy`.

**Impacto:** O agente de política pode criar/modificar políticas sem aprovação humana. O agente de scheduling pode agendar entrevistas sem confirmação explícita.

---

### 3.6 Bias Audit Baseline Não Estabelecido (ACH-022)
**Severidade: 🟡 P1 — Compliance**
**Arquivo:** `app/services/bias_audit_service.py`
**Esforço estimado:** 16h

`bias_audit_service.py` existe e implementa a Four-Fifths Rule em 4 dimensões. O `BiasAuditSnapshot` persiste no banco. Mas o **Golden Dataset de 100 candidatos baseline** não existe.

**Impacto:** Sem baseline, é impossível detectar drift discriminatório ao longo do tempo. Qualquer auditoria externa vai identificar isso imediatamente.

**O que precisa ser feito:**
- Criar `tests/fixtures/golden_dataset_seeder.py` com 100 candidatos sintéticos balanceados por gênero, faixa etária, PCD, região
- Rodar `bias_audit_service.save_snapshot()` com o dataset inicial para estabelecer baseline
- Documentar o baseline no relatório de compliance

---

### 3.7 PolicyEngine Alpha 1 — Regras Não Configuradas
**Severidade: 🟠 P2 — Arquitetura**
**Arquivo:** `app/services/policy_engine_service.py`
**Esforço estimado:** 8h

`policy_engine_service.py` existe com 6 setores (tech/varejo/logistica/financeiro/saude/rpo). Mas as **regras Alpha 1 específicas** — quais ações são auto-aprovadas, quais precisam HITL, thresholds por setor — não estão documentadas como configuradas.

**Impacto:** O PolicyEngine não está efetivamente governando os agentes. Cada agente usa sua própria lógica de decisão independente, sem centralização.

**O que precisa ser feito:**
- Definir e codificar regras Alpha 1 por setor no PolicyEngine
- Conectar `ConfidencePolicyService` → `PolicyEngine` para que thresholds venham da policy, não hardcoded
- Criar UI para visualizar e ajustar as regras ativas

---

## 4. Gaps de Arquitetura de IA

### 4.1 Tier 5 do CascadedRouter — LLM Cascade Subutilizado
**Oportunidade de custo e qualidade**

O Tier 5 usa `llm_cascade.py` (Haiku→Sonnet→Opus), mas o roteamento por complexidade não é explícito. Perguntas simples consomem o mesmo modelo que análises complexas.

**Proposta — Model Routing por Complexidade:**
| Tipo de Requisição | Modelo Recomendado |
|---|---|
| Perguntas simples, 1 entidade, intent claro | Haiku (custo baixo) |
| Análise de candidato, criação de vaga | Sonnet (padrão) |
| WSI scoring, FRIA, análises jurídicas | Opus (alta precisão) |

**Ação:** Implementar score de complexidade na saída do Tier 4 (FastRouter) para guiar o Tier 5. Monitorar custo por tier no Prometheus.

---

### 4.2 Memória 3 Níveis — Working/Episodic/Long-term Subutilizada
**Oportunidade de personalização**

A arquitetura tem 3 níveis de memória via `EnhancedAgentMixin`, mas o uso real é concentrado em `working memory`. `episodic_memory` e `long_term_memory` raramente são consultadas pelos agentes nos prompts.

**O que precisa ser feito:**
- Injetar histórico relevante da `episodic_memory` no contexto do agente antes de cada resposta
- Usar `long_term_memory` para personalizar tom e preferências do recrutador específico
- Criar `MemoryContextBuilder` que formata os 3 níveis em texto legível para o prompt

---

### 4.3 LearningLoop Não Conectado ao Sistema de Avaliação
**Oportunidade de melhoria contínua**

`learning_loop_service.py` existe (Like/Dislike feedback), mas não há evidência de que:
1. O feedback HITL (aprovação/rejeição) altera pesos do scoring
2. As respostas LLM são avaliadas com RAGAS
3. O model drift detection é alertado quando o LearningLoop detecta degradação

**O que precisa ser feito:**
- Conectar `HITL approval/rejection` → `learning_loop_service.record_feedback()`
- Conectar `learning_loop` → `model_drift_service.check_drift()` (trigger por score já existe)
- Implementar RAGAS evaluation para fluxos críticos (WSI scoring, CV matching)

---

### 4.4 RAG Híbrido — Alpha Blend Fixo, Não Contextual
**Oportunidade de relevância de busca**

`rag_pipeline_service.py` usa `alpha=0.5` fixo (BM25+pgvector). O contexto ideal de alpha varia por tipo de query:
- Busca por cargo específico → alpha baixo (BM25 dominante)
- Busca por perfil comportamental → alpha alto (semântico dominante)
- Busca por tech stack → alpha médio-alto

`wrf_service.py` e `wrf_dynamic_k_service.py` existem mas não estão conectados ao RAG principal.

**O que precisa ser feito:**
- Implementar **Dynamic Alpha** baseado no tipo de query detectado
- Conectar WRF (Weighted Rank Fusion) ao pipeline RAG principal
- Adicionar telemetria de relevância: registrar quais resultados o recrutador clicou/ignorou

---

### 4.5 Duplicação de Domínio: `policy` vs `hiring_policy` (ACH-016)
**Dívida técnica**

Ambos os domínios têm: system prompts, tool registry, stage context, agent.py.
**Ação:** Consolidar em um único domínio canônico.

---

### 4.6 Tools Duplicados: `app/tools/` vs `app/domains/*/tools/` (ACH-017)
**Dívida técnica**

Ambas as localizações existem com risco de divergência silenciosa.
**Ação:** Definir `app/tools/` como fonte de verdade e referenciar a partir dos domínios.

---

## 5. Gaps de Qualidade dos Prompts

### 5.1 Chain-of-Thought Estruturado Ausente em 6 Agentes

O `pipeline_system_prompt.py` tem o padrão correto (`<thought>`, `<tool_call>`, `<observation>`). Mas os system prompts de `analytics`, `communication`, `automation`, `ats_integration`, `talent`, `kanban` não têm instruções explícitas de CoT.

**Impacto:** Sem CoT explícito, o Claude vai direto para a resposta sem raciocinar, perdendo nuances que só aparecem no "thinking".

**Template a adicionar ao final de cada prompt faltante:**
```
## Formato de Raciocínio
SEMPRE raciocine antes de responder:
<thought>
1. O que o recrutador realmente precisa?
2. Quais ferramentas são relevantes?
3. Há algum risco de compliance ou fairness?
4. Qual é o próximo passo concreto?
</thought>
```

---

### 5.2 Benchmark Setorial Não Injetado nos Agentes Analíticos

`sector_benchmark_service.py` implementa injeção de benchmark anti-sycophancy no `evaluate_candidate()`. Mas `analytics` e `jobs_mgmt` — que fazem análises de performance de vagas e pipeline — não recebem o benchmark setorial.

**Impacto:** Violação da Crença #11 — o agente pode validar métricas mediocres sem comparar com o mercado.

**O que precisa ser feito:**
- Injetar `sector_benchmark_service.get_benchmark(sector)` no context do `AnalyticsReActAgent` e `JobsMgmtReActAgent`
- Adicionar instrução ao prompt: "Compare SEMPRE com o benchmark setorial antes de avaliar performance"

---

### 5.3 Prompts de Comunicação sem Templates Estruturados

O `CommunicationReActAgent` envia emails e WhatsApp, mas os prompts não incluem **templates de linguagem** para os diferentes tipos de comunicação (convite WSI, feedback de reprovação, oferta).

`gate_differentiated_feedback` existe em `candidate_feedback_service.py`, mas o `communication_system_prompt.py` não o referencia.

**O que precisa ser feito:**
- Incorporar ao `communication_system_prompt.py` os templates básicos com placeholders: `{{candidato_nome}}`, `{{vaga_titulo}}`, `{{proximo_passo}}`
- Instrução: "Use SEMPRE o template correspondente ao tipo de comunicação; personalize apenas os campos marcados"
- Garantir que FairnessGuard verifica o texto final antes do envio

---

### 5.4 System Prompt do Orchestrator sem Contexto de Tenant

O `main_orchestrator.py` processa requests multi-tenant, mas não há injeção do perfil do tenant (nome, setor, tamanho) no contexto da LIA.

**Impacto:** A LIA responde de forma genérica, sem personalização por empresa. Uma startup de tech e um banco regulado deveriam receber tratamentos completamente diferentes.

**O que precisa ser feito:**
- Criar `TenantContextBuilder`: dado `company_id`, busca nome, setor, nível de autonomia (PolicyEngine), histórico recente
- Injetar no início de cada conversa: "Você está assistindo [Nome Empresa], uma [setor] com [X] vagas abertas atualmente"
- Isso resolve também a calibração do PolicyEngine por setor

---

### 5.5 Anti-Sycophancy Injetado em Apenas 4 Prompts

O bloco `ANTI_SYCOPHANCY_OPERATIONAL` foi adicionado em: `sourcing`, `pipeline`, `communication`, `analytics`. Mas os agentes `talent`, `kanban`, `jobs_mgmt`, `automation`, `ats_integration`, `policy`, `hiring_policy` ainda não têm o bloco explícito (dependem do mixin, não do prompt).

**O que precisa ser feito:** Injetar o bloco diretamente no system prompt de todos os agentes, não só via mixin.

---

## 6. Oportunidades de Melhoria Significativa

### 6.1 Implementar RAGAS para Avaliação Contínua de Qualidade

Atualmente não há **avaliação automática da qualidade das respostas**. RAGAS mede:
- **Faithfulness:** resposta fiel às fontes (evita alucinação)
- **Answer Relevancy:** resposta responde à pergunta
- **Context Precision/Recall:** RAG usou os dados certos

**Ação:**
- Integrar RAGAS no pipeline de CI para os 5 fluxos críticos: WSI scoring, CV matching, salary benchmark, pipeline analysis, candidate search
- Criar golden queries + expected outputs para cada fluxo
- Alertar via Prometheus/LangSmith quando RAGAS score cai abaixo de threshold

---

### 6.2 Explicabilidade do LIA Score (EU AI Act Art. 13)

O `lia_score_service.py` gera score unificado, mas o recrutador não vê o breakdown. Isso viola:
- **EU AI Act Art. 13:** usuário tem direito a explicação da decisão
- **Confiança do recrutador:** score sem explicação não gera adoção

**Ação:**
- Adicionar `score_breakdown` ao `ChatResponse.structured_data`: `{technical: 0.82, behavioral: 0.71, cultural_fit: 0.68, experience: 0.90}`
- Criar componente FE `LIAScoreCard` com visualização do breakdown
- Adicionar ao prompt do `PipelineReActAgent`: "Quando apresentar LIA Score, SEMPRE explique os 4 componentes"

---

### 6.3 Personalização por Recrutador via Long-Term Memory

A `long_term_memory` existe mas não está conectada à personalização da experiência. Após N interações, é possível criar um perfil: tom preferido (direto vs. consultivo), nível de detalhe, ferramentas mais usadas.

**Ação:**
- Adaptar o system prompt dinamicamente com o perfil do recrutador
- Exemplos: Recrutador sênior → respostas curtas, dados brutos. Recrutador júnior → mais explicações, mais sugestões
- Criar `RecruiterProfileService` que armazena e recupera preferências

---

### 6.4 WSI Assíncrono — Canal Web com Timeout

`wsi_voice_orchestrator.py` existe para triagem por voz real-time, mas falta o canal **assíncrono web**:
- Candidato responde no seu tempo (chat web, sem pressão de tempo real)
- WSI processa em background via LangGraph + `PostgresSaver`
- Recrutador recebe resumo + scores quando candidato terminar

**Ação:**
- Criar `WSIAsyncSessionManager` com persistência no `PostgresSaver`
- Timeout de sessão: 48h (já documentado no roadmap como Gap B)
- Conectar com `followup_service.py` já existente para re-engajamento automático

---

### 6.5 FairnessGuard Camada 3 — Ativar com Controle de Custo

A Camada 3 (LLM semântico) está desativada (`FAIRNESS_LAYER3_ENABLED=False`) por latência. Mas o custo pode ser gerenciado:
- Ativar Layer 3 **apenas** para ações de alto impacto: rejeição, shortlist, score WSI
- Usar Haiku em vez de Sonnet para Layer 3 (redução de ~75% no custo)
- Adicionar cache Redis para patterns Layer 3 mais frequentes

---

### 6.6 Observabilidade LLM — Métricas Per-Agent

O Prometheus tem métricas para FairnessGuard e circuit breakers, mas não por agente. Sem isso, é impossível:
- Identificar qual agente está gastando mais tokens
- Detectar degradação de qualidade por domínio
- Otimizar custo por tipo de requisição

**Métricas necessárias:**
```python
# Por agente (a adicionar):
lia_agent_request_total{agent, domain, status}
lia_agent_latency_p95{agent, domain}
lia_agent_tokens_total{agent, model, type}   # input/output separados
lia_agent_confidence_avg{agent, domain}
lia_agent_fairness_blocked_total{agent, category}
lia_agent_hitl_triggered_total{agent, action_type}
```

---

### 6.7 Acessibilidade WCAG 2.1 AA — Plano de Ataque Pragmático

584 componentes. Apenas 77 com `aria-label` (13.2%). Bloqueante em auditorias SOX/ISO.

**Plano de prioridades:**
| Prioridade | Componentes | Escopo |
|---|---|---|
| 1 | ~80 | Todos os componentes de ação (botões, inputs, dropdowns) |
| 2 | ~50 | Fluxos críticos de candidato (portal, formulários WSI) |
| 3 | ~100 | Dashboard e navegação principal |

**Ação imediata:** Adicionar Axe-core ao CI como check automático — não precisa de 100% de cobertura manual.

---

## 7. Roadmap de Implementação Proposto

### Sprint I — Fundações Críticas (P0) — ~2 semanas

| Item | Severidade | Esforço | Arquivo Principal |
|---|---|---|---|
| FairnessGuard como middleware obrigatório no Orchestrator | P0 | 8h | `main_orchestrator.py` |
| `LGPD_CONSENT_ABSENT_HARD_BLOCK = True` como default | P0 | 4h | `consent_checker_service.py` |
| Circuit breakers WorkOS + Billing | P1 | 4h | `workos.py`, billing providers |
| Audit trail em `interview_graph.py` | P1 | 2h | `wsi_interview_graph.py` |
| HITL em `policy` e `interview_scheduling` | P1 | 6h | agents respectivos |

### Sprint II — Qualidade LLM (P1) — ~3 semanas

| Item | Severidade | Esforço | Arquivo Principal |
|---|---|---|---|
| Few-shot examples nos 9 agentes faltantes | P1 | 12h | system_prompts |
| Negation detection nos 8 agentes faltantes | P1 | 6h | system_prompts + mixin |
| Confidence calibration nos 10 agentes faltantes | P1 | 8h | react_agents |
| Chain-of-Thought estruturado nos 6 prompts faltantes | P1 | 4h | system_prompts |
| Anti-sycophancy direto nos prompts faltantes | P1 | 3h | system_prompts |
| Benchmark setorial em analytics e jobs_mgmt | P2 | 4h | system_prompts |

### Sprint III — Arquitetura IA (P1-P2) — ~3 semanas

| Item | Severidade | Esforço | Arquivo Principal |
|---|---|---|---|
| Tenant Context Builder + injeção no orchestrator | P2 | 8h | `main_orchestrator.py` |
| Dynamic Alpha no RAG + WRF connection | P2 | 8h | `rag_pipeline_service.py` |
| Stage context verificado nos 4 agentes faltantes | P2 | 4h | agents |
| LearningLoop → model drift connection | P2 | 6h | `learning_loop_service.py` |
| PolicyEngine com regras Alpha 1 configuradas | P2 | 8h | `policy_engine_service.py` |
| Consolidar policy vs hiring_policy | P2 | 8h | domínios |

### Sprint IV — Observabilidade e Compliance (P2) — ~2 semanas

| Item | Severidade | Esforço | Arquivo Principal |
|---|---|---|---|
| Métricas Prometheus per-agent (6 métricas) | P2 | 8h | agents + prometheus |
| Bias Audit Golden Dataset + baseline | P1 | 16h | fixtures + `bias_audit_service.py` |
| RLS PostgreSQL | P0 | 16h | migrations + middleware |
| LIA Score breakdown (explicabilidade EU AI Act) | P2 | 8h | `lia_score_service.py` + FE |
| RAGAS CI para 5 fluxos críticos | P2 | 12h | CI + golden queries |

### Sprint V — Produto e Experiência (P2-P3) — ~3 semanas

| Item | Severidade | Esforço | Arquivo Principal |
|---|---|---|---|
| WSI Assíncrono (chat web, timeout 48h) | P2 | 16h | `wsi_interview_graph.py` |
| FairnessGuard Layer 3 com controle de custo | P3 | 8h | `fairness_guard.py` |
| Personalização por recrutador via long-term memory | P3 | 12h | `enhanced_agent_mixin.py` |
| Acessibilidade WCAG — Prioridade 1 (ações críticas) | P2 | 16h | componentes FE |
| Communication templates no system prompt | P2 | 4h | `communication_system_prompt.py` |
| Memory Context Builder (3 níveis → prompt) | P3 | 8h | `enhanced_agent_mixin.py` |

---

## 8. Resumo dos Achados por Categoria

| Categoria | Total | 🔴 Críticos | 🟡 Altos | 🟠 Médios | 💡 Oportunidades |
|---|---|---|---|---|---|
| Segurança / Compliance | 6 | 3 | 2 | 1 | — |
| Qualidade LLM | 4 | — | 3 | 1 | 3 |
| Arquitetura IA | 5 | — | 3 | 2 | 4 |
| Prompts / CoT | 5 | — | 2 | 3 | 3 |
| Observabilidade | 3 | — | 1 | 2 | 2 |
| Produto / Experiência | 5 | — | 1 | 2 | 4 |
| **Total** | **28** | **3** | **12** | **11** | **16** |

### Tabela de Verificações Críticas Transversais

| Verificação | Status | Cobertura |
|---|---|---|
| Anti-Sycophancy | ✅ via mixin | 12/12 agentes |
| Anti-Sycophancy no prompt direto | ⚠️ Parcial | 4/12 agentes |
| FairnessGuard no entry-point | ❌ Opt-in | 0/1 orchestrator |
| Negation Detection | ⚠️ Parcial | 4/12 agentes |
| Confidence Calibration real | ⚠️ Parcial | 4/14 agentes |
| Circuit Breaker | ⚠️ Parcial | 13/16 providers |
| PII Masking | ✅ OK | Global + Celery + LLM |
| Consent Hard Block | ❌ Soft enforcement | padrão: False |
| Multi-Tenant RLS | ❌ Application-level | 0 tabelas com RLS |
| Audit Trail | ✅ Quase completo | 13/14 agentes |
| HITL Enforcement | ⚠️ Parcial | 5/8 agentes relevantes |
| Few-Shot Examples | ⚠️ Parcial | 5/14 agentes |
| Bias Audit Baseline | ❌ Não estabelecido | Golden Dataset ausente |

---

## 9. Os 5 Quick Wins de Maior Impacto

Se houver capacidade para apenas 5 itens imediatos, priorizar nesta ordem:

| # | Item | Esforço | Impacto |
|---|---|---|---|
| 1 | `LGPD_CONSENT_ABSENT_HARD_BLOCK = True` | 4h | Elimina violação legal imediata (LGPD Art. 7) |
| 2 | FairnessGuard no entry-point do Orchestrator | 8h | Fecha maior brecha de governança da plataforma |
| 3 | Few-shot examples nos 9 agentes | 12h | Melhoria de qualidade LLM mais visível pelo usuário final |
| 4 | Circuit breaker WorkOS | 2h | Evita outage total de login por falha de provider externo |
| 5 | Confidence calibration universal | 8h | Fundamenta todas as decisões de HITL e autonomia |

**Total estimado dos 5 quick wins: ~34 horas de desenvolvimento.**

---

## Apêndice — Arquivos Críticos por Área

### Backend — IA / Agentes
| Arquivo | Responsabilidade |
|---|---|
| `app/orchestrator/main_orchestrator.py` | CascadedRouter 6-tiers, entry-point universal |
| `app/shared/agents/enhanced_agent_mixin.py` | FairnessGuard, memória, confidence, HITL |
| `app/shared/compliance/fairness_guard.py` | Engine de detecção de viés 3 camadas |
| `app/services/confidence_policy_service.py` | Calibração de confiança, thresholds |
| `app/shared/compliance/audit_service.py` | Trilha de auditoria SOX/BCB-498 |
| `app/services/model_drift_service.py` | 4 triggers de drift detection |
| `app/services/sector_benchmark_service.py` | Benchmark setorial anti-sycophancy |
| `app/services/learning_loop_service.py` | Feedback loop Like/Dislike |
| `app/services/rag_pipeline_service.py` | RAG híbrido BM25+pgvector |
| `app/jobs/celery_tasks.py` | 10 jobs agendados |

### Backend — System Prompts
| Arquivo | Agente |
|---|---|
| `app/domains/recruiter_assistant/agents/talent_system_prompt.py` | Talent |
| `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` | Kanban |
| `app/domains/pipeline/agents/pipeline_system_prompt.py` | Pipeline (referência — 326L, 25 few-shots) |
| `app/domains/sourcing/agents/sourcing_system_prompt.py` | Sourcing |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` | Jobs Management |
| `app/domains/hiring_policy/agents/policy_system_prompt.py` | Policy (256L) |
| `app/domains/communication/agents/communication_system_prompt.py` | Communication |
| `app/domains/analytics/agents/analytics_system_prompt.py` | Analytics |
| `app/domains/automation/agents/automation_system_prompt.py` | Automation |
| `app/domains/ats_integration/agents/ats_integration_system_prompt.py` | ATS Integration |

### Frontend
| Arquivo | Responsabilidade |
|---|---|
| `src/components/pages/candidates-page.tsx` | Float Chat (Nível 1) |
| `src/components/pages/job-kanban-page.tsx` | Kanban Chat (Nível 2) |
| `src/hooks/use-float-streaming.ts` | WebSocket + HITL streaming |
| `src/hooks/use-ml-predictions.ts` | Previsões ML |
| `src/hooks/use-short-list.ts` | Short list management |

---

*Documento gerado em 13/03/2026. Próxima revisão recomendada após conclusão do Sprint I.*
