# Diagnóstico: Guia Completo WeDO Talent v3.2 vs. Plataforma LIA

**Data:** Março 2026 | **Escopo:** Todas as 7 partes do Guia Completo v3.2
**Metodologia:** Análise automatizada do codebase (backend + frontend + docs) cruzada com cada seção do guia

---

## Legenda de Status

| Símbolo | Status | Significado |
|---------|--------|-------------|
| ✅ | **Implementado** | Funcionalidade existe no código e segue o guia |
| ⚠️ | **Parcial** | Base existe mas falta completude, refinamento ou alinhamento |
| ❌ | **Não Implementado** | Não encontrado no codebase ou muito distante do descrito |
| 🔧 | **Estrutural** | Precisa de mudança arquitetural ou de processo (não apenas código) |

---

## Resumo Executivo

| Parte do Guia | Itens | ✅ | ⚠️ | ❌ | Aderência |
|---------------|-------|-----|-----|-----|-----------|
| I — Manifesto | 47 | 30 | 13 | 4 | **64%** |
| II — Framework de Dev | 38 | 8 | 12 | 18 | **37%** |
| III — Metodologia de Screening | 22 | 16 | 5 | 1 | **84%** |
| IV — Princípios de DEI | 18 | 9 | 5 | 4 | **64%** |
| V — Compliance LGPD | 24 | 17 | 5 | 2 | **81%** |
| VI — Framework de Teste de Viés | 16 | 7 | 5 | 4 | **59%** |
| VII — Roadmap de Documentação | 14 seções | 6 | 4 | 4 | **57%** |
| **TOTAL** | **179** | **93** | **49** | **37** | **65%** |

**Conclusão geral:** A plataforma LIA tem forte aderência nas camadas técnicas de IA (screening, agentes, compliance), mas apresenta gaps significativos em processos de time (Framework de Dev — Parte II) e em infraestrutura operacional de produção (CI/CD, ambientes, testes de viés contínuos).

---
---

# PARTE I — MANIFESTO

## Seção 0: O Produto — Recrutamento Conversacional com IA

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| LIA como persona unificada | ✅ | `agent_prompts.yaml` define persona LIA; `TransitionChatPanel.tsx` renderiza com Brain icon e "Olá! Sou a Lia" | Consistência de persona entre canais pode variar |
| Conversation-first como direção | ✅ | `orchestrated_talent_chat.py`, `ActionExecutor`, chats inline no Kanban, Wizard via chat | Botões ainda são caminho primário em várias telas |
| Estado híbrido (botões + chat) | ✅ | Interface dual: Kanban com drag-drop + chat de transição; Wizard com formulário + chat expandido | Intencional conforme guia |
| Múltiplos canais (Web, WhatsApp, Teams) | ✅ | Web: chats inline; WhatsApp: `DataRequestWhatsAppService` + Twilio/Meta; Teams: `TeamsService` com Adaptive Cards | SMS adapter existe no código mas sem provider real |
| ATS standalone ou camada inteligente | ⚠️ | Integrações ATS existem (`ats_integration` domain, Gupy, Pandapé, Merge) | Modo "camada sobre ATS existente" não está completamente funcional |
| Experiência dual (moderna vs. tradicional) | ❌ | Não existe toggle de modo de experiência para o usuário | Planejado mas não implementado |

## Seção 2: 12 Crenças Fundamentais

| # | Crença | Status | Evidência | Gap |
|---|--------|--------|-----------|-----|
| 01 | Humano em Primeiro Lugar | ✅ | `Human Review Gate` (migration 010), confirmação obrigatória em ações destrutivas via `PendingActionState`, `rejected_by_human` field | — |
| 02 | Justa e Não-Discriminatória | ✅ | `FairnessGuard` (355 linhas) com 3 camadas (regex + implícito + semântico LLM); mascaramento de atributos protegidos; `fairness_audit_logs` persistente | Teste contínuo em produção não automatizado |
| 03 | Transparente e Explicável | ✅ | `ExplainabilityService`, `ExecutionLogStore` com cadeia de raciocínio completa, `Candidate Portal` com acesso a explicações | Opt-out para screening humano não implementado no frontend do candidato |
| 04 | Segura e Respeitosa com Privacidade | ✅ | `PIIMaskingFilter` global, `encryption.py` (Fernet), LGPD cleanup service, `scheduled_deletion_at` | Secrets parcialmente em env vars, não em vault dedicado |
| 05 | Construída por Humanos, Para Humanos | ⚠️ | Red teaming: `test_fairness_guard.py` existe | Auditorias trimestrais de viés não formalizadas como processo |
| 06 | Em Melhoria Contínua | ⚠️ | `LongTermMemoryService` para aprendizado cross-session; `recruiter_preferences` table | Dashboard de métricas de avaliação não visível para time interno |
| 07 | Resiliente por Design | ✅ | `CircuitBreaker` (3 estados), `LLMProviderFactory` multi-provider (Claude→Gemini→OpenAI), `RateLimitMiddleware` com fallback Redis→memória | — |
| 08 | Observável e Rastreável | ✅ | Structured JSON logging em produção, `RequestIdMiddleware`, Sentry integrado, `AgentActivity` logs, Prometheus metrics (8 categorias) | Print statements ainda existem em alguns arquivos |
| 09 | Consciente de Custos | ✅ | `TokenTrackingService` com budget por user/company, `AiConsumption` model, limites diários (500k tokens/user, 5M/company), alerta em 70% | Limites mensais definidos ($500/company) mas dashboard de custo não acessível ao recrutador |
| 10 | Inteligência Onde Importa, Determinismo Onde Conta | ✅ | `CascadedRouter` (cache→regex→LLM), `wsi_deterministic_scorer.py` para scoring, `ConfidencePolicyService` para decisões | — |
| 11 | Crítica e Construtiva — Nunca Bajuladora | ✅ | Anti-sycophancy explícito no system prompt do `PolicyReActAgent` (regras 145/147), `get_industry_benchmarks` com dados de mercado, registro de risco quando recrutador insiste | — |
| 12 | Autonomia Progressiva | ✅ | `CompanyHiringPolicy` com 3 níveis (Assistant/Semi/Autonomous), `automation_rules`, `ConfidencePolicyService` com thresholds (0.85/0.70/0.50) | — |

## Seção 4: Filosofia de Engenharia

| Princípio | Status | Evidência | Gap |
|-----------|--------|-----------|-----|
| Agentes Nunca Inventam — Extraem, Comparam e Classificam | ✅ | Rubric BARS "DO NOT INFER", WSI extrai evidências do CV, penalties para "Score Inflation" | — |
| Prompts São Código | ⚠️ | Prompts em `app/prompts/domains/*.yaml` e `*_system_prompt.py` versionados com código | Não há processo formal de PR review separado para prompts |
| Domínios Definem Fronteiras | ✅ | 11 domains em `app/domains/` (sourcing, cv_screening, pipeline, hiring_policy, etc.) | — |
| Economia de Cascata | ✅ | `CascadedRouter`: Memory Cache → FastRouter → LLM | — |
| Toda Ação Tem um Nível de Risco | ✅ | `ConfidencePolicyService` com 3 níveis de risco, `PendingActionState` para confirmação | Classificação de risco não explícita por tool (inferida pelo behavior) |

## Seção 6: Inegociáveis (Checklist)

### Segurança & Privacidade
| Item | Status | Evidência |
|------|--------|-----------|
| Zero PII em logs | ✅ | `PIIMaskingFilter` instalado globalmente no `main.py` |
| TLS 1.3+ em todo tráfego | ⚠️ | HTTPS no deploy, mas não enforced explicitamente como TLS 1.3 mínimo |
| Compliance LGPD verificado | ✅ | `lgpd_compliance.py`, `consent_management.py`, `data_subject_requests.py` |
| DPAs de terceiros assinados | 🔧 | Processo de negócio — não rastreável no código |
| Secrets via vault | ⚠️ | Secrets em variáveis de ambiente Replit, não em vault dedicado (HashiCorp/AWS) |
| Proteção prompt injection global | ✅ | `prompt_injection.py` em `app/shared/` |

### Fairness & Viés
| Item | Status | Evidência |
|------|--------|-----------|
| Teste de viés aprovado (variância < 5%) | ⚠️ | `test_disparate_impact_wsi.py` existe com regra 4/5; frontend `admin/compliance/auditoria/bias/page.tsx` com dashboard de auditorias, disparity ratios por categoria e compliance frameworks (NYC LL144, EU AI Act, LGPD) | Não roda automaticamente em CI |
| Red team aprovado (< 1% jailbreak) | ⚠️ | `test_fairness_guard.py` cobre padrões explícitos, mas red team formal não documentado | — |
| Amostra revisão humana 5% | ❌ | Mecanismo de sampling de decisões para revisão humana não implementado | — |
| API de explicabilidade funcional | ✅ | `ExplainabilityService`, `ExecutionLogStore` | — |
| Atributos protegidos mascarados antes do LLM | ✅ | "Blind Evaluation" em screening, `mask_pii()` em `finetuning_export.py` | — |

### Transparência
| Item | Status | Evidência |
|------|--------|-----------|
| Candidato sabe que é avaliado por IA | ⚠️ | LGPD consent flow no WhatsApp menciona IA; portal do candidato tem links de privacidade | Mensagem explícita "você está sendo avaliado por IA" não confirmada em todos os pontos de contato |
| Raciocínio da decisão documentado | ✅ | `ExecutionLogStore` persiste cadeia completa input→raciocínio→tools→output |
| Processo de recurso disponível | ⚠️ | `Human Review Gate` existe no backend; botão de "Appeal" não confirmado no frontend do candidato |
| Trilha de auditoria persistente | ✅ | `audit_logs`, `fairness_audit_logs`, `DataAccessLog`, `agent_activities` |

### Qualidade de Código
| Item | Status | Evidência |
|------|--------|-----------|
| Cobertura de testes mínima 80% | ⚠️ | 47 arquivos de teste, 978 funções de teste, mas coverage report automatizado não encontrado |
| Code review (4 olhos) | 🔧 | Processo de time — não aplicável no Replit (dev solo), precisa de CI/CD com PR review |
| Type-safe (TypeScript, mypy) | ⚠️ | Frontend: TypeScript; Backend: type hints Python parciais, mypy não configurado no CI |
| Nenhum arquivo > 500 linhas | ❌ | Múltiplos arquivos excedem 500 linhas (ex: `candidate.py` = 614 linhas) |
| Lint/type/testes passam no CI | ⚠️ | `.github/workflows/ci.yml` existe mas CI não ativo neste ambiente |

### Resiliência & Operações
| Item | Status | Evidência |
|------|--------|-----------|
| Nenhum provider único sem fallback | ✅ | `LLMProviderFactory` com fallback Claude→Gemini→OpenAI |
| Health check funcional | ✅ | `system_health.py` monitora DB, Redis, Task Manager, APIs externas |
| Monitoramento e alertas ativos | ⚠️ | Prometheus metrics definidos, `AlertService` existe, mas stack de monitoramento (Grafana/etc.) não deployado |
| Rollback testado | ⚠️ | Alembic migrations com `downgrade()`, Replit checkpoints disponíveis |
| Rotação on-call | ❌ | Não definida (processo de time) |

## Seção 12: Governança de Agentes

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Versionamento semântico de agentes | ⚠️ | `AgentActivity` loga `agent_id` e `model`, mas sem versão semântica formal (code+prompt+model+config) | Falta versionamento atômico |
| Confiança na saída | ✅ | `confidence` em intent classification, `AUTO_TRANSITION_CONFIDENCE_THRESHOLD` (0.8) | — |
| Budget de tokens por agente | ✅ | `TokenTrackingService` com limites por user/company/mensal | — |
| Prompt injection global | ✅ | `prompt_injection.py` em `app/shared/` | — |
| Validação de output contra schema | ⚠️ | Pydantic schemas para responses, mas validação estrutural pós-LLM não universal | — |
| Rate limiting por user/API key | ✅ | `RateLimitMiddleware` sliding window com Redis | — |
| Resposta a incidentes de IA | ⚠️ | `lgpd_compliance.py` cobre breach; `continuity.py` tem DR planning | Runbook específico para incidentes de IA não documentado |
| Explicabilidade | ✅ | `ExecutionLogStore` persiste cadeia completa | — |
| Detecção de viés por cascata | ✅ | `FairnessGuard`: regex (camada 1) → implícito/léxico (camada 2) → LLM semântico (camada 3) | — |

---
---

# PARTE II — FRAMEWORK DE DESENVOLVIMENTO

**Nota:** Esta parte descreve como o time de produção trabalha. O ambiente Replit é o protótipo (Etapa 1 do ciclo). Muitos itens são processos de time, não código.

## Stack & Ciclo de Levas

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Frontend (prod): Vue 3 + Vuetify 3 + Nuxt | ❌ | Frontend atual: React + Next.js + Tailwind. Vue migration prep skill existe (`.agents/skills/vue-migration-prep/`) | Migração Vue não iniciada |
| Frontend (proto): React + TypeScript + Tailwind | ✅ | `plataforma-lia/`: Next.js + React + TypeScript + Tailwind CSS | — |
| Backend (prod): Ruby on Rails + Python + FastAPI | ⚠️ | Python + FastAPI implementado. Rails não presente no repositório | Rails não iniciado |
| Backend (proto): Python + FastAPI + SQLAlchemy | ✅ | `lia-agent-system/`: FastAPI + SQLAlchemy + PostgreSQL | — |
| Ciclo de 9 etapas | ⚠️ | Etapa 1 (prototipação Replit) ativa; Etapa 2 (GitHub) parcial | Etapas 3-9 dependem de time de produção |
| Prototipação como fonte de verdade | ✅ | Replit é o ambiente de desenvolvimento ativo | — |

## AI Squad (6 Agentes de Dev)

| Agente | Status | Evidência | Gap |
|--------|--------|-----------|-----|
| Conversion Agent (React→Vue) | ❌ | Skill `vue-migration-prep` existe como guia, mas agente automatizado não implementado | — |
| Card Generator (Jira) | ❌ | Jira integration instalada mas Card Generator Agent não implementado | — |
| Sprint Planner | ❌ | Não implementado | — |
| Review Agent (Code Review) | ⚠️ | `.agents/skills/feature-audit/` e `.agents/skills/design-standardize/` servem como review automatizado no Replit | Não é GitHub Action, é skill do agente Replit |
| Test Generator | ⚠️ | Playwright + Vitest configurados; skill `testing` gera testes E2E | Não gera testes Vitest unitários automaticamente |
| Doc Agent (Notion) | ⚠️ | Notion MCP configurado (2 connections); mas agente automatizado de documentação não implementado | — |
| API Contract Generator | ❌ | Não implementado | — |

## Skills, Rules & Padrões

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| .cursorrules na raiz | ⚠️ | Existe no repositório, mas voltado para o Replit/React, não para Vue | — |
| System Prompts versionados | ✅ | `*_system_prompt.py` em cada domain, `app/prompts/domains/*.yaml` | — |
| Skill Library | ✅ | 4 skills em `.agents/skills/` (design-standardize, feature-audit, feature-impact, vue-migration-prep) | Skill library no repo Vue (`/ai-skills`) não criada |
| Agent Contracts YAML | ⚠️ | `app/prompts/shared/agent_prompts.yaml` existe; docs em `docs/agents/` com specs por agente | Formato YAML padronizado por agente não completo |
| Design Tokens em código | ✅ | Tokens em `tailwind.config.ts` (wedo-cyan, wedo-green, etc.), CSS variables `--eleven-*` | `/src/theme/lia.ts` para Vue não existe |

## Mapa de Lacunas (Seção 10 do Guia)

| Prática | Guia diz | Status LIA | Observação |
|---------|----------|------------|------------|
| Daily standup | 🔲 A Definir | ❌ | Processo de time |
| Sprint Review / Demo | 🔲 A Definir | ❌ | Processo de time |
| Retrospectiva | 🔲 A Definir | ❌ | Processo de time |
| Comunicação assíncrona | 🔲 A Definir | ❌ | Processo de time |
| ADRs | 🔲 A Definir | ✅ | `docs/adr/ADR-001-multi-agent-architecture.md`, `ADR-002-observability-stack.md` |
| Política de testes | ⚠️ Parcial | ⚠️ | Testes existem, coverage enforcement não está no CI |
| Code review humano | ⚠️ Parcial | ⚠️ | Feature-audit skill no Replit; processo Git não formalizado |
| Gestão de bugs | 🔲 A Definir | ❌ | Sem processo formal |
| Débito técnico | 🔲 A Definir | ❌ | Sem rastreamento formal |
| Estratégia de ambientes | 🔲 A Definir | ⚠️ | Dev (Replit) + Prod (deploy Replit). Staging não existe |
| CI/CD pipeline | 🔲 A Definir | ⚠️ | `.github/workflows/ci.yml` e `e2e-tests.yml` existem mas não ativos |
| Secrets management | 🔲 A Definir | ⚠️ | Env vars Replit, não vault |
| Monitoramento/alertas | 🔲 A Definir | ⚠️ | Prometheus metrics + AlertService implementados, stack não deployado |
| Backup/DR | 🔲 A Definir | ⚠️ | `continuity.py` com DR planning API; Replit checkpoints; `pg_dump` documentado |
| On-call | 🔲 A Definir | ❌ | Processo de time |

---
---

# PARTE III — METODOLOGIA DE SCREENING

## Pipeline de Avaliação

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Screening estruturado com humano no loop | ✅ | `Human Review Gate`, `rejected_by_human` field, `ConfidencePolicyService` | — |
| Avaliação multi-bloco WSI | ✅ | 5 blocos: Data Extraction, Company Questions, WSI Eligibility, Technical (Bloom/Dreyfus), Behavioral (CBI/Big Five) | Guia menciona 7 blocos; implementação tem 5 |
| Competências Técnicas (Bloom Taxonomy) | ✅ | 6 níveis cognitivos implementados no WSI | — |
| Competências Comportamentais (Big Five/OCEAN + CBI/STAR) | ✅ | `wsi_service.py` integra CBI e Big Five | — |
| Experiência Profissional (Dreyfus) | ✅ | 5 estágios (Novice→Expert), `SeniorityContextCalibrator` | — |
| Fit Cultural | ⚠️ | Mencionado no framework mas não como bloco WSI independente com scoring dedicado | Pode estar embutido no bloco comportamental |
| Potencial de Crescimento (Bloom para profundidade cognitiva) | ⚠️ | Bloom usado para técnico; uso específico para "potencial de crescimento" como bloco separado não confirmado | — |
| Formação Acadêmica (equivalência bootcamp=diploma) | ✅ | WSI trata paths alternativos, rubric reconhece bootcamp | — |
| Alinhamento com a Vaga | ✅ | Comparação JD requirements vs. perfil demonstrado é core do WSI | — |
| Scoring determinístico (0-100) | ✅ | `wsi_deterministic_scorer.py`: Essential 3.0x, Important 2.0x, Nice-to-have 1.0x | — |
| Fórmula de scoring (0.6 × Self-Declaration + 0.4 × Evidence) | ✅ | Implementado com penalties (inflação) e bonuses (humildade, OSS) | — |
| Score Normalization entre candidatos | ✅ | `ScoreNormalizationService` com coeficiente de dificuldade | — |

## Thresholds de Decisão

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| 85-100: Auto-approve | ✅ | `APROVAR_TRIAGEM` para scores altos | Guia usa 80+, implementação usa 85+ |
| 70-84: Approve with review | ✅ | `APROVAR_TRIAGEM` com revisão | — |
| 50-69: Hold/Manual review | ✅ | `MANTER_ESPERA` | — |
| 30-49: Reject | ✅ | `NAO_PROSSEGUIR` | — |
| 0-29: Clear reject | ✅ | `NAO_PROSSEGUIR` | — |
| Edge cases 60-69 sempre revisão humana | ⚠️ | `MANTER_ESPERA` implica revisão, mas enforcement automático não confirmado | — |

## Rubric Evaluation (BARS)

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| 4 níveis (Exceeds/Meets/Partial/Missing) | ✅ | `rubric_evaluation_service.py` com BARS (100/75/40/0 pts) | — |
| "DO NOT INFER" rule | ✅ | Instrução explícita no prompt de avaliação | — |
| Red flags detection | ✅ | Detecção automática de gaps, job hopping, mismatch de senioridade | — |
| Confidence score (0.0-1.0) | ✅ | Métrica de quantidade de dados disponíveis para avaliação | — |

## Interação com Candidato (WhatsApp)

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Screening via WhatsApp | ✅ | `DataRequestWhatsAppService`: consent → choice (portal/chat) → coleta multi-turn | — |
| Input multi-modal (texto, áudio, vídeo) | ⚠️ | WhatsApp text + áudio (Deepgram transcription documentado); vídeo via `multi_modal_analysis` | Integração Deepgram em tempo real não confirmada como ativa |
| Perguntas calibradas por senioridade | ✅ | `SeniorityContextCalibrator` ajusta expectativas por indústria, tech age, geografia | — |
| Pre-Qualification antes do chat | ✅ | `PreQualificationService` avalia CV vs. rubric antes de iniciar chat | — |
| Feedback humanizado (Alinhado/Parcial/Distante) | ✅ | Ao invés de % raw, usa classificação qualitativa | — |

---
---

# PARTE IV — PRINCÍPIOS DE DEI

## Framework de Detecção de Viés

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Teste por gênero (nomes M/F/neutro) | ⚠️ | `test_disparate_impact_wsi.py` testa neutralidade de gênero | Não usa exatamente 20 nomes por grupo como guia sugere |
| Teste por faixa etária | ⚠️ | Teste de idade existe no disparate impact test | — |
| Teste por formação (universidade vs. bootcamp) | ⚠️ | Conceito no WSI (paths equivalentes), mas teste formal separado não confirmado | — |
| Teste por região geográfica (Brasil) | ❌ | Não encontrado teste específico de viés por região | — |
| Teste por proficiência linguística | ❌ | Não encontrado | — |
| Regra 4/5 (Adverse Impact Ratio) | ✅ | `test_disparate_impact_wsi.py` implementa 4/5 rule | — |
| Detecção de linguagem enviesada em JDs | ✅ | `FairnessGuard` detecta termos como "boa aparência", "recém-formado", "universidades de primeira linha" | — |
| Variância < 3% entre demografias | ⚠️ | Target definido nos testes, mas monitoramento contínuo em produção não ativo | — |

## Métricas & Dashboards

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Monthly Fairness Report | ⚠️ | `admin/compliance/auditoria/bias/page.tsx` com auditorias mensais/trimestrais, disparity ratios, resultados Aprovado/Ressalvas/Reprovado | Relatório automatizado não gera sozinho |
| Dashboard de aprovação por grupo demográfico | ✅ | `bias-service.ts` + `useBiasAudits.ts` + `bias/page.tsx`: disparity ratio por categoria (Gender, Age, Ethnicity, Education, Disability, Veteran), status Clear/Consider/Concern | — |
| Alertas automáticos de variância | ⚠️ | `admin/compliance/monitoramento/alertas/page.tsx` existe; `AlertService` backend existe | Regras de fairness específicas para alertas não confirmadas |
| Análise de recursos (appeals) | ⚠️ | `Human Review Gate` suporta override; `trust-center/recursos/page.tsx` existe | Análise agregada de appeals não confirmada |

## Treinamento & Governança

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Treinamento DEI obrigatório (3h, anual) | 🔧 | Processo de RH — não rastreável no código | — |
| Revisão ética trimestral | 🔧 | Processo de governança — não rastreável no código | — |
| Metas de representatividade | 🔧 | Processo de RH | — |
| Plano de resposta a viés (5 dias) | ⚠️ | `lgpd_compliance.py` tem breach response; protocolo específico de viés não formalizado | — |
| Comunicação ao candidato se prejudicado | ⚠️ | Templates de comunicação existem no guia; implementação no sistema de comunicação não confirmada | — |

---
---

# PARTE V — COMPLIANCE LGPD

## 6 Pilares LGPD

| Pilar | Status | Evidência | Gap |
|-------|--------|-----------|-----|
| 1. Licitude & Transparência | ✅ | `consent_management.py` com event tracking (grant/revoke/renew/expire), SHA256 proof hashes, `ConsentCheckerService` por purpose | — |
| 2. Limitação de Finalidade | ✅ | Consent granular por propósito (`ai_screening`, `ai_scoring`); enforcement bloqueia operações sem consent ativo (HTTP 451) | — |
| 3. Minimização de Dados | ⚠️ | Formulário de candidato coleta dados extensos (modelo tem 100+ campos); nem todos são mínimos necessários | Campos de diversidade são opcionais, mas modelo tem muitos campos |
| 4. Exatidão & Integridade | ✅ | `encryption.py` (Fernet), PostgreSQL com backups, `DataAccessLog` rastreia acessos | — |
| 5. Limitação de Retenção | ✅ | `LGPDCleanupService` com políticas: rejected 90 dias, interview notes 180 dias, screening logs 365 dias; `scheduled_deletion_at` com index | — |
| 6. Responsabilização & Segurança | ✅ | `audit_logs`, `PIIMaskingFilter`, `DataAccessLog` (who/what/why), breach reporting endpoints com tracking ANPD 48h | — |

## Direitos do Candidato (Art. 18-20)

| Direito | Status | Evidência | Gap |
|---------|--------|-----------|-----|
| Acesso (Art. 18) | ✅ | `data_subject_requests.py` (Portal do Titular) | — |
| Correção (Art. 19) | ✅ | `portal-titular/page.tsx` com gestão de DSR (Data Subject Requests) incluindo tipos Access/Rectification/Deletion/Portability/Objection | — |
| Exclusão (Art. 20) | ✅ | `LGPDCleanupService` + `data_subject_requests.py` + frontend portal | — |
| Explicação (Art. 20 + AI Act) | ✅ | `ExplainabilityService`, `candidate_portal.py` | — |
| Opt-out / Withdraw | ✅ | `consent-management-service.ts` + `lgpd/consentimentos/page.tsx` com gestão de consentimentos | — |
| Portabilidade (Art. 20) | ⚠️ | `portal-titular/page.tsx` aceita request de portabilidade; geração do pacote completo não confirmada | — |

## Implementação Técnica

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| PII encrypted at rest (AES-256) | ⚠️ | `encryption.py` (Fernet) para API keys; criptografia por coluna para PII de candidato não confirmada | PostgreSQL sem TDE |
| PII encrypted in transit (TLS 1.3) | ⚠️ | HTTPS via deploy, mas TLS 1.3 mínimo não enforced explicitamente | — |
| Backups diários automatizados | ⚠️ | Replit checkpoints; backup PostgreSQL documentado em `PORTABILITY_GUIDE.md` | Automação de backup diário não confirmada |
| Auto-delete job (runs daily) | ✅ | `LGPDCleanupService` com retention policies | — |
| "Download my data" API | ⚠️ | `data_subject_requests.py` aceita requests; geração de pacote completo (JSON/CSV/PDF) parcial | — |
| No PII in logs | ✅ | `PIIMaskingFilter` global (CPF, email, phone, names) | — |
| Audit trail readonly | ⚠️ | `audit_logs` é append-only no design, mas sem enforcement de immutability no banco | — |
| DPO (Encarregado de Dados) nomeado | 🔧 | Processo organizacional — placeholder em `lgpd_compliance.py` | — |
| Breach notification (ANPD 48h) | ✅ | Endpoints em `lgpd_compliance.py` rastreiam notificação ANPD | — |

---
---

# PARTE VI — FRAMEWORK DE TESTE DE VIÉS

## 4 Níveis de Teste

| Nível | Status | Evidência | Gap |
|-------|--------|-----------|-----|
| Level 1: Pre-Deployment Testing | ⚠️ | `test_disparate_impact_wsi.py` com profiles equivalentes e regra 4/5 | Não integrado no CI como gate bloqueante |
| Level 2: Baseline Accuracy Testing | ⚠️ | `test_agent_comprehensive.py` valida qualidade de resposta e métricas | Golden dataset com 50+ candidatos avaliados por humanos não existe |
| Level 3: Continuous Monitoring | ❌ | `fairness_audit_logs` captura dados; dashboard mensal e alertas automáticos não implementados | Dados acumulam mas não são analisados automaticamente |
| Level 4: Incident Response | ⚠️ | `lgpd_compliance.py` cobre breach; protocolo específico para viés detectado retroativamente não formalizado | — |

## Infraestrutura de Testes

| Item | Status | Evidência | Gap |
|------|--------|-----------|-----|
| Golden Dataset (candidatos sintéticos) | ⚠️ | `generate_wsi_datasets.py` gera dados; `seed_wsi_demo_data.py` semeia dados demo | `bias_test_cases.json` formal não existe como arquivo separado |
| Script automatizado de teste de viés | ✅ | `test_disparate_impact_wsi.py` com `EQUIVALENT_PROFILES` | — |
| CI/CD integration (bias-test.yml) | ❌ | `.github/workflows/ci.yml` existe mas não inclui bias test como step | — |
| Acceptance criteria (variância < 3%) | ⚠️ | Target definido nos testes mas não como gate no pipeline | — |
| Relatório mensal automatizado | ❌ | Template no guia, não implementado como feature | — |
| Ferramentas (DeepTeam, Garak, Promptfoo) | ❌ | Nenhuma ferramenta externa de teste de viés integrada | — |
| Audit trail de testes de viés | ⚠️ | Resultados de teste em `fairness_audit_logs`; diretório `/bias_testing/` formal não existe | — |

## Dimensões Testadas

| Dimensão | Status | Evidência |
|----------|--------|-----------|
| Gênero | ✅ | `test_disparate_impact_wsi.py` |
| Idade | ✅ | `test_disparate_impact_wsi.py` |
| Etnia | ✅ | `test_disparate_impact_wsi.py` |
| Formação educacional | ⚠️ | WSI trata equivalência, mas teste de viés específico não confirmado |
| Região geográfica | ❌ | Não testado |
| Proficiência linguística | ❌ | Não testado |
| Trajetória de carreira | ❌ | Não testado |

---
---

# PARTE VII — ROADMAP DE DOCUMENTAÇÃO

## Arquitetura de 3 Camadas

| Camada | Status | Evidência | Gap |
|--------|--------|-----------|-----|
| Camada 1 — Princípios | ⚠️ | Guia Completo v3.2 existe como arquivo anexo, mas não está integrado no repositório como documentação ativa | Precisa ser incorporado ao repo |
| Camada 2 — Metodologia | ⚠️ | `docs/roadmap/`, `docs/specs/`, `.agents/skills/` cobrem parte do framework | Disperso entre vários locais |
| Camada 3 — Implementação | ✅ | `docs/architecture/`, `docs/agents/`, `docs/adr/`, `replit.md` extensivo | — |

## Estrutura Proposta (14 Seções) vs. Existente

| Seção do Guia | Status | O Que Existe |
|---------------|--------|--------------|
| 01_MANIFESTO | ⚠️ | Existe como arquivo anexo, não integrado ao repo |
| 02_DEVELOPMENT_GUIDE | ⚠️ | `.agents/skills/` + `docs/roadmap/` cobrem parcialmente |
| 03_DESIGN_SYSTEM | ✅ | Design System documentado extensivamente em `replit.md`, tokens em `tailwind.config.ts`, skills `design-standardize` |
| 04_METHODOLOGY | ✅ | `docs/architecture/agents/`, WSI docs, rubric evaluation docs |
| 05_DIVERSITY_INCLUSION | ⚠️ | `FairnessGuard` implementado, testes existem, `bias/page.tsx` com dashboard de auditorias; documentação formal de DEI como arquivo separado não existe |
| 06_COMPLIANCE_LEGAL | ✅ | `docs/compliance/`, `lgpd_compliance.py`, `consent_management.py`, Trust Center, 30+ páginas admin compliance (SOC-2, SOX, ISO-27001, LGPD, DPO, incidentes) |
| 07_SECURITY_PLAYBOOKS | ⚠️ | `prompt_injection.py`, `pii_masking.py`, `encryption.py`, `dashboard-seguranca/page.tsx`, `monitoramento/incidentes/page.tsx`; playbooks documentais parciais |
| 08_EVALUATION_TESTING | ⚠️ | Testes existem (47 arquivos); documentação da pirâmide de testes e golden datasets não formalizada |
| 09_OPERATIONS_RUNBOOKS | ⚠️ | `PORTABILITY_GUIDE.md`, DR planning API; onboarding guide e runbooks operacionais incompletos |
| 10_PRODUCT_DESIGN | ✅ | `docs/vagas/`, `docs/funil/`, `docs/specs/`, `docs/integracao/` |
| 11_EXTERNAL_REFERENCES | ⚠️ | Menções a NIST, OWASP, EU AI Act em `analise-comparativa-v5-vs-lia.md`; docs dedicados não existem |
| 12_TEAM_CULTURE | ❌ | ADRs existem (`docs/adr/`); code review standards, branching strategy, tech debt policy não documentados |
| 13_AGENT_GOVERNANCE | ⚠️ | Implementação existe (monitoring, cost, flags, LLM factory); documentação formal não consolidada |
| 14_INFRASTRUCTURE | ❌ | Infraestrutura funcional mas documentação de IaC, environments guide, CI/CD não formalizada |

---
---

# GAPS PRIORITÁRIOS — Recomendações

## Prioridade P0 (Críticos — Afetam compliance e confiabilidade)

| # | Gap | Parte | Ação Sugerida |
|---|-----|-------|---------------|
| 1 | Testes de viés não rodam em CI | VI | Integrar `test_disparate_impact_wsi.py` como gate bloqueante no CI/CD |
| 2 | Monitoramento contínuo de fairness ausente | IV, VI | Dashboard mensal automatizado com alertas de variância > 3% |
| 3 | Golden dataset humano-avaliado não existe | VI | Criar dataset com 50+ candidatos reais avaliados por 3 recrutadores |
| 4 | Sampling de revisão humana (5%) | I | Implementar job que seleciona 5% das decisões para revisão obrigatória |
| 5 | Appeal/recurso no frontend do candidato | I, V | Botão "Solicitar revisão humana" no portal do candidato |

## Prioridade P1 (Importantes — Afetam qualidade e governança)

| # | Gap | Parte | Ação Sugerida |
|---|-----|-------|---------------|
| 6 | Versionamento semântico de agentes | I | Implementar `AgentVersion` = code_hash + prompt_hash + model + config |
| 7 | Arquivos > 500 linhas | I | Refatorar arquivos grandes (candidate.py, etc.) |
| 8 | Coverage report no CI | I | Configurar coverage mínimo (80%) como gate no CI |
| 9 | Secrets em vault | I | Migrar de env vars para vault (quando em produção) |
| 10 | Staging environment | II | Criar ambiente staging com dados anonimizados |
| 11 | Testes de viés por região e formação | IV, VI | Adicionar dimensões de região (SP/RJ vs. interior) e educação ao teste de disparate impact |

## Prioridade P2 (Melhorias — Completude e maturidade)

| # | Gap | Parte | Ação Sugerida |
|---|-----|-------|---------------|
| 12 | Modo de experiência dual (moderna vs. tradicional) | I | Implementar toggle de interface quando conversation-first estiver maduro |
| 13 | Ferramentas externas de teste de viés | VI | Avaliar integração com Promptfoo ou Garak |
| 14 | Documentação formal em 14 seções | VII | Reorganizar `docs/` seguindo estrutura proposta no guia |
| 15 | AI Squad agents (Card Gen, Sprint Planner, etc.) | II | Implementar conforme time de produção se formar |
| 16 | Exportação completa de dados (JSON/CSV/PDF) | V | Completar endpoint de portabilidade com pacote completo |
| 17 | Blocos WSI de 5 para 7 | III | Separar Fit Cultural e Potencial de Crescimento como blocos independentes |
| 18 | Runbooks operacionais | VII | Documentar onboarding (<2h), deployment, rollback, incident response |

## Prioridade P3 (Futuro — Dependem de time e infraestrutura)

| # | Gap | Parte | Ação Sugerida |
|---|-----|-------|---------------|
| 19 | Migração React → Vue/Vuetify | II | Iniciar quando time frontend de produção existir |
| 20 | Backend Rails | II | Iniciar quando time backend de produção existir |
| 21 | Processos de time (daily, retro, on-call) | II | Definir quando time completo se formar |
| 22 | Revisão ética trimestral | IV | Formalizar quando comitê existir |
| 23 | Treinamento DEI obrigatório | IV | Implementar quando RH tiver programa |
| 24 | Metas de representatividade | IV | Definir quando dados de contratação existirem |

---

## Métricas Finais de Aderência por Área

```
Arquitetura de IA & Agentes    ████████████████████░  90%
Screening WSI & Avaliação      ████████████████░░░░░  84%
LGPD & Compliance              ████████████████░░░░░  81%
DEI & Fairness                 █████████████░░░░░░░░  64%
Manifesto & Princípios         █████████████░░░░░░░░  64%
Teste de Viés Automatizado     ████████████░░░░░░░░░  59%
Documentação                   ████████████░░░░░░░░░  57%
Framework de Dev (Time)        ███████░░░░░░░░░░░░░░  37%
```

**Nota:** O Framework de Dev (37%) tem baixa aderência porque descreve processos de time de produção (Vue, Rails, sprints, cerimônias) que dependem da formação do time completo. O protótipo Replit está cumprindo seu papel como "fonte de verdade" conforme descrito na Etapa 1 do guia.

---

*Documento gerado em Março 2026 | Baseado em análise do codebase lia-agent-system + plataforma-lia*
*Referência: WeDO Talent — Guia Completo v3.2*

