# Diagnóstico Completo: Compliance, Governança de IA e Auditoria
## Plataforma LIA / WeDO Talent

**Data:** Março 2026  
**Versão:** 1.0  
**Classificação:** Confidencial  
**Escopo:** Análise legal (LGPD, EU AI Act, PL 2338/2023, NYC LL144), técnica (auditoria, logs, observabilidade), IA (agentes, fairness, bias) e melhores práticas de mercado

---

## Sumário Executivo

A Plataforma LIA apresenta uma **arquitetura de governança de IA madura e bem estruturada** para o estágio atual de desenvolvimento. Os fundamentos estão sólidos — FairnessGuard de 3 camadas, pipeline de screening com BARS, audit trail dual, circuit breakers, autonomy engine com guardrails dinâmicos, e 100% dos agentes com EnhancedAgentMixin.

No entanto, a análise profunda revelou **gaps significativos** que precisam ser endereçados antes de:
- Homologação em bancos e instituições financeiras reguladas
- Operação com candidatos na União Europeia
- Operação com empregadores em Nova York (NYC LL144)
- Entrada em vigor do Marco Legal da IA brasileiro (PL 2338/2023)

### Números Consolidados

| Severidade | T002 (IA/Agentes) | T003 (LGPD/Dados) | T004 (Auditoria) | T005 (Fairness/DEI) | **Total** |
|-----------|:-:|:-:|:-:|:-:|:-:|
| **Crítico** | 1 | 8 | 6 | 3 | **18** |
| **Alto** | 6 | 16 | 14 | 12 | **48** |
| **Médio** | 8 | 11 | 13 | 17 | **49** |
| **Baixo** | 6 | 6 | 5 | 4 | **21** |
| **Total** | 21 | 41 | 38 | 36 | **136** |

---

## 1. Contexto Legislativo

### 1.1 Legislações Aplicáveis

| Legislação | Jurisdição | Status | Relevância para WeDO |
|-----------|-----------|--------|---------------------|
| **LGPD** (Lei 13.709/2018) | Brasil | Em vigor | Obrigatória — dados pessoais de candidatos |
| **EU AI Act** (Reg. 2024/1689) | União Europeia | Em vigor (alto risco: ago/2026) | Obrigatória se operar na UE — recruitment AI = alto risco (Anexo III) |
| **PL 2338/2023** (Marco Legal da IA) | Brasil | Em tramitação na Câmara — aprovação estimada Q3/Q4 2026 | Preparação obrigatória — abordagem baseada em risco similar ao EU AI Act |
| **NYC Local Law 144** | Nova York, EUA | Em vigor (jul/2023) | Obrigatória se clientes contratarem em NYC |
| **EEOC Guidelines** | EUA (federal) | Em vigor | Referência para Four-Fifths Rule e adverse impact |
| **BCB-498 / Resolução CMN 4893** | Brasil | Em vigor | Obrigatória para homologação bancária |
| **SOC-2 Type II** | Internacional | Certificação voluntária | Requisito de mercado para clientes enterprise/bancos |
| **SOX** | EUA | Em vigor | Requisito para clientes listados em bolsa |
| **ISO 27001** | Internacional | Certificação voluntária | Requisito para clientes enterprise |
| **ISO 42001** | Internacional | Publicada dez/2023 | Primeira certificação de AI Management System — Eightfold AI já certificada |

### 1.2 PL 2338/2023 — Marco Legal da IA (Brasil)

**Status atual (março 2026):** Aprovado no Senado (dez/2024), em tramitação na Câmara dos Deputados. Comissão Especial criada. Relator: Dep. Aguinaldo Ribeiro (PP-PB). Previsão de votação: Q1-Q2 2026. Possível sanção: Q3-Q4 2026.

**Principais pontos que impactam a plataforma:**
- Abordagem baseada em riscos (similar EU AI Act)
- IA em recrutamento provavelmente classificada como **alto risco**
- Direito à explicabilidade de decisões automatizadas
- Direito à contestação e intervenção humana
- Princípios: dignidade humana, privacidade, transparência, não-discriminação
- Autoridades setoriais com competências específicas

**Impacto:** A plataforma precisa estar preparada para compliance com o Marco Legal da IA antes da sanção. Os requisitos são largamente compatíveis com o que já está desenhado na arquitetura (FairnessGuard, HumanReviewSampling, AuditTrail), mas a implementação precisa ser completada.

### 1.3 EU AI Act — Requisitos para Alto Risco

**IA em recrutamento = Sistema de Alto Risco** (Anexo III). Requisitos aplicáveis a partir de **agosto de 2026**:

| Artigo | Requisito | Status na Plataforma |
|--------|----------|---------------------|
| Art. 6 + Anexo III | Classificação como alto risco | ✅ Reconhecido |
| Art. 9 | Sistema de gestão de risco | ✅ FairnessGuard + drift detection |
| Art. 10 | Governança de dados | ⚠️ Parcial — golden dataset existe, sem governance formal |
| Art. 11 | Documentação técnica | ⚠️ Parcial — docs existem sem formato padronizado |
| Art. 12 | Registro de logs | ✅ AIInferenceLog + audit trail |
| Art. 13 | Transparência ao usuário | ❌ Ausente — sem notificação explícita ao candidato sobre uso de IA |
| Art. 14 | Supervisão humana | ⚠️ Parcial — HumanReviewSamplingService existe mas NÃO integrado no fluxo principal (G-C1) |
| Art. 15 | Precisão e robustez | ⚠️ Parcial — sem RAGAS, sem métricas formais |
| Art. 26 | Obrigações do deployer | ⚠️ Parcial |
| Art. 52 | Transparência (obrigação de informar uso de IA) | ❌ Ausente |
| Art. 62 | Registro de incidentes graves | ⚠️ Parcial — modelo existe, sem workflow |

**Práticas proibidas desde fev/2025:** Reconhecimento de emoções, categorização biométrica, social scoring — nenhuma dessas práticas é utilizada pela plataforma (✅ conforme).

### 1.4 NYC Local Law 144

| Requisito | Status |
|----------|--------|
| Bias audit anual por auditor independente | ❌ Ausente |
| Publicação pública dos resultados | ❌ Ausente |
| Notificação prévia ao candidato (10 dias) | ⚠️ Parcial |
| Auditoria por raça/etnia e gênero | ⚠️ Parcial (gênero sim, raça/etnia não) |
| Opção de acomodação alternativa | ❌ Ausente |
| Retenção de dados 4 anos | ⚠️ Parcial |

---

## 2. Comparativo com Plataformas de Mercado

### 2.1 Benchmark de Compliance por Plataforma

| Funcionalidade | **WeDO/LIA** | Eightfold | Gupy | HireVue | Greenhouse | Paradox | Findem |
|---------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Bias Audit (Four-Fifths Rule)** | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ |
| **Auditor independente externo** | ❌ | ✅ (BABL AI) | ❌ | ✅ | ❌ | ✅ | ❌ |
| **ISO 42001 (AI Management)** | ❌ | ✅ (ago/2025) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **FairnessGuard / Bias prevention** | ✅ (3 camadas) | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **Explicabilidade de decisões** | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **Human-in-the-loop** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **PII Masking em logs** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| **Consent management granular** | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **SOC-2 Type II** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **LGPD compliance tools** | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **Model drift detection** | ✅ | ✅ | ❌ | ✅ | ❌ | ⚠️ | ❌ |
| **Red teaming** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **BARS/Rubric methodology** | ✅ | ✅ | ❌ | ✅ | ❌ | ⚠️ | ❌ |
| **Circuit breakers/resilience** | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| **LLM fallback chain** | ✅ | ✅ | ❌ | ✅ | ⚠️ | ⚠️ | ⚠️ |

### 2.2 Diferenciais WeDO vs. Concorrentes

**Onde WeDO está à frente:**
- FairnessGuard de 3 camadas (regex + léxico + semântica) — mais sofisticado que a maioria
- Model drift detection com 4 triggers — poucos concorrentes implementam
- AutonomyEngine com guardrails dinâmicos por empresa — inovador
- CascadedRouter de 6 tiers com métricas — eficiência de custo
- BARS methodology para scoring — cientificamente robusto
- LGPD compliance nativo (vs. GDPR adaptado dos concorrentes internacionais)

**Onde WeDO precisa avançar:**
- Certificação ISO 42001 — Eightfold é a referência (primeira plataforma de recrutamento certificada)
- SOC-2 Type II — requisito de mercado para enterprise, Gupy já tem
- Auditor independente externo — Eightfold/HireVue usam BABL AI (ForHumanity)
- Publicação pública de resultados de bias audit — NYC LL144 requirement
- PII masking antes do LLM — gap crítico que nenhum concorrente anuncia publicamente ter

### 2.3 Práticas de Mercado Relevantes

**Eightfold AI (referência em governance):**
- AI Ethics Council multidisciplinar
- Bias audit externo trimestral por BABL AI Inc.
- ISO 42001 + FedRAMP + SOC-2
- Publicação de resultados de audit no site

**Gupy (referência Brasil):**
- +4.000 clientes incluindo Itaú, Ambev, Vivo
- SOC-2 Type II
- Agentes de IA para pré-entrevistas no WhatsApp
- Compliance LGPD nativo

**HireVue:**
- Descontinuou análise facial em 2021 (decisão ética)
- Bias audit por ORCAA (O'Neil Risk Consulting)
- Framework de IO Psychology para validação de assessments
- Explicabilidade por assessment type

**Paradox AI:**
- NYC LL144 bias audit disponível
- Transparência de uso de IA para candidatos
- Foco em automação conversacional (chatbots)

---


## 3. Análise Detalhada: IA e Agentes

## 3.1. Arquitetura dos Agentes

### 3.1.1 Visão Geral

A plataforma utiliza uma arquitetura domain-driven com múltiplas camadas:

| Camada | Componente | Função |
|--------|-----------|--------|
| Orquestração | `Orchestrator` | Ponto de entrada, coordena routing + domínios |
| Roteamento | `CascadedRouter` (6 tiers) | Memory → Redis → Vector → FastRouter → LLM Cascade → Clarification |
| Domínios | `DomainPrompt` (ABC) | Contrato base para todos os domínios |
| Workflow | `DomainWorkflow` | Pipeline 3-nós: analyze_intent → execute → format |
| Agentes | `ReActLoop` / `LangGraphReActBase` | Loop autônomo Reason-Act-Observe |
| Mixin | `EnhancedAgentMixin` | Memória, autonomia, aprendizado |

### 3.1.2 Domínios Registrados

13 agentes ReAct identificados, todos usando `LangGraphReActBase + EnhancedAgentMixin`:

| Agente | Domínio | EnhancedAgentMixin |
|--------|---------|-------------------|
| PipelineReActAgent | cv_screening/pipeline | ✅ |
| WizardReActAgent | job_management/wizard | ✅ |
| SourcingReActAgent | sourcing | ✅ |
| CommunicationReActAgent | communication | ✅ |
| AnalyticsReActAgent | analytics | ✅ |
| ATSIntegrationReActAgent | ats_integration | ✅ |
| AutomationReActAgent | automation | ✅ |
| TalentReActAgent | recruiter_assistant/talent | ✅ |
| JobsManagementReActAgent | recruiter_assistant/jobs_mgmt | ✅ |
| KanbanReActAgent | recruiter_assistant/kanban | ✅ |
| PipelineTransitionAgent | pipeline/transition | ✅ |
| PolicyReActAgent | hiring_policy | ✅ |

**Status: ✅ Todos os 12 agentes herdam `EnhancedAgentMixin`** — cobertura 100%.

### 3.1.3 CascadedRouter — Análise

**Implementação:** 6 tiers com custo crescente (memory → redis → vector → fast → LLM → clarification).

| Aspecto | Status | Observação |
|---------|--------|-----------|
| Fallback chain | ✅ Implementado | 6 tiers com métricas Prometheus por tier |
| Clarification (fallback final) | ✅ Implementado | Retorna `needs_clarification=True` com opções |
| Cache MD5 in-process | ✅ | LRU com tamanho configurável |
| Redis hash cache | ✅ | Distribuído entre workers |
| Vector semantic cache | ✅ | pgvector com threshold 0.92 |
| LLM Cascade | ✅ | Haiku → Sonnet → Opus |
| Métricas de observabilidade | ✅ | Hit rate por tier, latência, confiança |

**Gaps identificados:**

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-R1 | Silent fallback para `recruiter_assistant` | **Médio** | No fallback final, `domain_id="recruiter_assistant"` é usado com `confidence=0.0`. Embora emita `needs_clarification=True`, o `domain_id` retornado pode levar a processamento pelo domínio errado se o caller não verificar o flag. |
| G-R2 | Cache key baseado em MD5 | **Baixo** | MD5 não é collision-resistant, mas aceitável para cache de roteamento (não é segurança). |

---

## 3.2. System Prompts e Instruções de Governança

### 3.2.1 Estrutura de Prompts

| Arquivo YAML | Conteúdo |
|-------------|----------|
| `shared/lia_persona.yaml` | Persona LIA, vocabulário HR, persistência de dados, **diretrizes éticas** |
| `shared/agent_prompts.yaml` | Prompts por tipo de agente (orchestrator, sourcing, etc.) |
| `shared/defensive.yaml` | Clarificação, out-of-scope, recuperação de erros |
| `domains/*.yaml` | Prompts específicos por domínio |

### 3.2.2 Diretrizes Éticas nos Prompts

**Status: ✅ Implementado** — `ethical_guidelines` em `lia_persona.yaml`:

- ✅ Lista explícita de critérios permitidos (hard skills, soft skills, experiência)
- ✅ Lista explícita de critérios proibidos (nome, idade, foto, instituição, gaps, estado civil, endereço, etnia)
- ✅ Instrução de linguagem inclusiva e neutra de gênero
- ✅ Requisitos de transparência e documentação de decisões

### 3.2.3 Gaps nos Prompts

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-P1 | Ausência de instrução explícita sobre EU AI Act | **Alto** | Os prompts mencionam LGPD e CLT mas não referenciam EU AI Act Art. 14 (human oversight) nem Art. 52 (transparência). |
| G-P2 | Ausência de instrução sobre explicabilidade | **Médio** | Os ethical_guidelines pedem "documenter critérios" mas não instruem o agente a gerar explicações estruturadas para cada decisão de triagem/ranking. |
| G-P3 | Persona `_LIA_SYSTEM_PROMPT` no Orchestrator é básica | **Baixo** | O fallback direto do orchestrator usa um prompt simplificado sem as diretrizes éticas completas do YAML. |

---

## 3.3. FairnessGuard — Auditoria das 3 Camadas

### 3.3.1 Camada 1: Detecção de Viés Explícito (Regex)

**Status: ✅ Implementado** — `fairness_guard.py`

9 categorias discriminatórias cobertas:

| Categoria | Padrões Regex | Status |
|-----------|--------------|--------|
| Gênero | 6 padrões (PT + EN) | ✅ |
| Raça/Etnia | 4 padrões | ✅ |
| Idade | 9 padrões (com exceção para "anos de experiência") | ✅ |
| Religião | 3 padrões | ✅ |
| Orientação Sexual | 3 padrões | ✅ |
| Estado Civil | 3 padrões | ✅ |
| Deficiência | 4 padrões | ✅ |
| Maternidade/Paternidade | 7 padrões | ✅ |
| Nacionalidade | 3 padrões | ✅ |

Mensagens educacionais com referência legislativa (CLT, Lei 10.741, Lei 8.213, etc.).

### 3.3.2 Camada 2: Detecção de Viés Implícito

**Status: ✅ Implementado** — `check_implicit_bias()`

11 termos de viés implícito cobertos (boa aparência, bairros nobres, universidades de primeira linha, etc.). Retorna `soft_warnings` (não bloqueia, mas alerta).

### 3.3.3 Camada 3: Análise Semântica via LLM

**Status: ⚠️ Parcialmente Implementado** — `check_semantic()`

- ✅ Existe o método `check_semantic()` que usa LLM para detectar vieses implícitos
- ⚠️ **NÃO é chamado automaticamente no workflow** — é async e precisa de chamada explícita
- ⚠️ O `DomainWorkflow._pre_check()` chama apenas `guard.check()` (Camada 1 + 2)

### 3.3.4 Cobertura do FairnessGuard

**Pontos de aplicação verificados:**

| Ponto | FairnessGuard | Status |
|-------|--------------|--------|
| `DomainWorkflow._pre_check()` | `guard.check()` (Camada 1+2) | ✅ Aplicado a TODOS os domínios |
| `wizard_tool_registry` | Referenciado | ✅ |
| `wizard_system_prompt` | Referenciado | ✅ |
| `jobs_mgmt_system_prompt` | Referenciado | ✅ |
| `jobs_mgmt_tool_registry` | Referenciado | ✅ |
| `talent_tool_registry` | Referenciado | ✅ |
| `wsi_interview_graph` | Referenciado | ✅ |
| `rubric_evaluation_service` | Referenciado | ✅ |
| `personalized_feedback_service` | Referenciado | ✅ |
| `candidate_report_service` | Referenciado | ✅ |
| `rag_pipeline_service` | Referenciado | ✅ |
| `toon_service` | Referenciado | ✅ |
| `fairness_reports` API | Endpoint dedicado | ✅ |

### 3.3.5 Auditoria do FairnessGuard

- ✅ Método `log_check()` para persistência em `FairnessAuditLog` (PostgreSQL)
- ✅ Query hash SHA-256 (não armazena a query original — LGPD compliant)
- ✅ Métricas Prometheus (`fairness_blocks_total` por categoria)
- ✅ Logging de bloqueios com categoria e termos

### 3.3.6 Gaps no FairnessGuard

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-F1 | Camada 3 (semântica) não integrada no workflow | **Alto** | `check_semantic()` existe mas NÃO é chamado no `DomainWorkflow._pre_check()`. Vieses sutis/reformulados podem passar sem detecção. |
| G-F2 | `log_check()` não é chamado automaticamente | **Médio** | O `DomainWorkflow._pre_check()` bloqueia mas não persiste a auditoria — precisa de `db` session. Depende de chamada explícita pelos endpoints. |
| G-F3 | Cobertura de idiomas limitada | **Baixo** | Regex cobre PT-BR e alguns termos EN, mas não espanhol ou francês (relevante se plataforma expandir). |

---

## 3.4. ConfidencePolicyService — Thresholds e Escalação Humana

### 3.4.1 Implementação

**Status: ✅ Implementado** — `confidence_policy_service.py`

Três thresholds definidos:

| Threshold | Valor | Ação |
|-----------|-------|------|
| `silent_apply` | ≥ 0.85 | Auto-aplica sem notificação |
| `apply_notify` | ≥ 0.70 | Auto-aplica com notificação visual |
| `ask_user` | ≥ 0.50 | Apresenta como sugestão |
| < 0.50 | — | Também `ASK_USER` (escalação) |

**Nota importante:** Este serviço é focado no **Job Wizard** (auto-preenchimento de campos de vaga), NÃO é um sistema genérico de escalação humana para decisões de IA.

### 3.4.2 HumanReviewSamplingService — Escalação Humana

**Status: ✅ Implementado** — `human_review_sampling_service.py`

- Sampling determinístico de 5% das decisões (hash MD5 do decision_id)
- Decisões que SEMPRE requerem revisão humana: `finalize_hiring`, `mass_rejection`, `fairness_flagged`
- Conforme EU AI Act Art. 14 e LGPD Art. 20

### 3.4.3 Gaps na Escalação

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-C1 | Sem escalação humana no ReAct loop por baixa confiança | **Alto** | O `DomainWorkflow` pede clarificação quando `confidence < 0.5`, mas NÃO escala para revisão humana. O `HumanReviewSamplingService` existe mas não está integrado no fluxo principal de decisões do agente. |
| G-C2 | Confidence scoring é heurístico, não calibrado | **Médio** | `ConfidenceNode.compute_confidence()` usa heurísticas simples (comprimento da resposta, número de tools). Não há calibração estatística ou validação contra ground truth. |
| G-C3 | `ConfidencePolicyService` limitado ao Wizard | **Médio** | O serviço de confiança com thresholds de auto-apply é usado apenas no wizard de criação de vagas. Decisões de triagem/ranking de candidatos não passam por política de confiança equivalente. |

---

## 3.5. Mascaramento de Atributos Protegidos antes do LLM

### 3.5.1 PII Masking em Logs

**Status: ✅ Implementado** — `pii_masking.py`

| Padrão | Cobertura | Status |
|--------|----------|--------|
| CPF | `\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}` | ✅ |
| Email | Padrão completo | ✅ |
| Telefone BR | Com/sem +55 e DDD | ✅ |
| Nomes em logs | `name=`, `candidato=`, etc. | ✅ |

Instalado globalmente via `install_global_pii_masking()` no `main.py`.

### 3.5.2 PII Masking em Prompts Enviados ao LLM

**Status: ⚠️ PARCIAL — Gap Significativo**

| Aspecto | Status | Descrição |
|---------|--------|-----------|
| Masking em logs | ✅ | `PIIMaskingFilter` no root logger |
| Masking em prompts ao LLM | ❌ | **NÃO há masking de PII antes de enviar ao LLM** |
| TOON Service (anonymize mode) | ✅ | Anonimização de candidatos quando `anonymize=True` |
| Blind review / attribute masking | ❌ | **NÃO há remoção de atributos protegidos (nome, idade, foto) antes do prompt ao LLM** |

### 3.5.3 Gaps no Mascaramento

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-M1 | PII não mascarada nos prompts ao LLM | **Crítico** | O `PIIMaskingFilter` protege apenas logs. Dados de candidatos (nome, CPF, email) podem ser enviados ao LLM nos prompts. Violação LGPD Art. 6 (necessidade) e risco de dados em training data do provider. |
| G-M2 | Sem blind review pré-LLM | **Alto** | Os ethical_guidelines instruem o LLM a "ignorar nome do candidato", mas o nome é enviado no prompt. A proteção depende do LLM seguir a instrução, não de mascaramento técnico. |
| G-M3 | Busca por `protected_attributes`/`anonymize_candidate` vazia | **Alto** | Não existe função/módulo dedicado a remover atributos protegidos (nome, idade, gênero) antes de construir o prompt do LLM para decisões de triagem/ranking. |

---

## 3.6. Circuit Breakers e Resiliência

### 3.6.1 Implementação

**Status: ✅ Implementado** — `circuit_breaker.py`

Duas implementações coexistentes (class-based e functional decorator):

| Circuit Breaker | Serviço | Failure Threshold | Recovery Timeout | Request Timeout |
|-----------------|---------|-------------------|-----------------|-----------------|
| ANTHROPIC_CIRCUIT | Claude API | 5 | 30s | 60s |
| OPENAI_CIRCUIT | OpenAI API | 5 | 30s | 60s |
| GEMINI_CIRCUIT | Gemini API | 5 | 30s | 60s |
| PEARCH_CIRCUIT | Pearch Search | 3 | 60s | 30s |
| WORKOS_CIRCUIT | Auth (WorkOS) | 5 | 30s | 15s |
| MERGE_CIRCUIT | ATS Merge | 5 | 45s | 30s |
| GOOGLE_CALENDAR_CIRCUIT | Calendar | 5 | 60s | 30s |

**Pontos de uso verificados:**
- `llm_factory.py` / `llm_claude.py` — LLM calls protegidos
- `pearch_service.py` — Busca de candidatos
- `google_calendar_client.py` — Agendamento
- `openmic_service.py` — Voice screening
- `deepgram_service.py` — Transcrição

### 3.6.2 Funcionalidades

| Funcionalidade | Status |
|----------------|--------|
| 3 estados (CLOSED → OPEN → HALF_OPEN) | ✅ |
| Métricas Prometheus | ✅ (`circuit_breaker_state` gauge) |
| Reset manual | ✅ |
| Fallback configurável | ✅ (no decorator) |
| Timeout por serviço | ✅ |
| Stats endpoint | ✅ (`get_all_circuit_stats()`) |

### 3.6.3 Gaps

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-CB1 | Sem alerting automático quando circuit abre | **Médio** | O circuit breaker loga warning mas não dispara alerta (email/Slack/webhook) quando um serviço abre o circuito. Existe `agent_health_alert_service` mas não é usado nos circuit breakers de LLM. |
| G-CB2 | Duas implementações coexistentes | **Baixo** | Existem tanto a classe `CircuitBreaker` (async, class-based) quanto o decorator funcional `@circuit_breaker`. Não há risco, mas aumenta complexidade de manutenção. |

---

## 3.7. ReAct Loop — Governança e Controles

### 3.7.1 Controles Implementados

| Controle | Status | Detalhes |
|----------|--------|---------|
| Max iterations | ✅ | Configurável por domínio (default via settings) |
| Token budget | ✅ | Hard limit por sessão, estimado via chars/4 |
| Duplicate detection | ✅ | Threshold configurável para tool calls repetidas |
| Failed tool retry prevention | ✅ | `failed_tool_calls` list impede re-chamada |
| Guardrails (confirmação de usuário) | ✅ | Lista dinâmica via `AutonomyEngine` |
| AuditCallback injetado | ✅ | Captura automática de LLM calls + tool calls |
| LangSmith tracing | ✅ | `@traceable` decorator |
| Health alerts | ✅ | `agent_health_alert_service` em caso de erro |
| Token tracking | ✅ | `token_tracking_service` para billing |
| Observer pattern | ✅ | `ReActObserver` para telemetria detalhada |

### 3.7.2 AutonomyEngine — Guardrails Dinâmicos

**Status: ✅ Implementado**

3 níveis de autonomia por empresa:

| Nível | Tools que requerem confirmação |
|-------|-------------------------------|
| Low (default) | move_candidate, batch_move, reject_candidate, schedule_interview, generate_offer, finalize_hiring, create_job, update_job, delete_job, send_message, bulk_send |
| Medium | batch_move, reject_candidate, generate_offer, finalize_hiring, delete_job, bulk_send |
| High | finalize_hiring, delete_job |

Fallback em 3 camadas: AutonomyEngine → GuardrailRepository (DB) → lista estática.

### 3.7.3 Gaps

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-RL1 | ReAct loop não integra FairnessGuard | **Alto** | O `FairnessGuard` é aplicado no `DomainWorkflow._pre_check()` ANTES do ReAct loop. Mas respostas GERADAS pelo loop (reasoning + tool results) não passam por verificação de fairness na saída. |
| G-RL2 | `_generate_response` não aplica PII masking | **Alto** | A resposta final gerada pelo LLM no ReAct loop não tem PII scrubbing antes de retornar ao usuário. Se um tool retorna dados de candidato, esses dados podem aparecer na resposta. |
| G-RL3 | Sem rate limiting por sessão | **Médio** | O token budget controla custo, mas não há rate limiting para evitar abuso (ex: loop requests em paralelo). O `PolicyEngine` verifica daily limits mas não por sessão. |

---

## 3.8. FactChecker — Post-Response Validation

### 3.8.1 Implementação

**Status: ✅ Implementado** — `fact_checker.py`

Verificações implementadas:

| Tipo | Verificação | Status |
|------|------------|--------|
| Salários | Range razoável (R$1.500 - R$200.000) + desvio do esperado | ✅ |
| Contagem de candidatos | Máximo 50.000, desvio do esperado | ✅ |
| Percentagens | Range 0-100 | ✅ |
| Datas | Validação de data + range 2020-2030 | ✅ |
| Top-N candidates | Range razoável 1-20 | ✅ |

Integrado no `DomainWorkflow._post_check()` — aplicado a TODOS os domínios.

### 3.8.2 Gaps

| # | Gap | Severidade | Descrição |
|---|-----|-----------|-----------|
| G-FC1 | FactChecker não consulta banco de dados | **Médio** | Verificações são contra ranges estáticos, não contra dados reais do banco. Se o LLM diz "5 candidatos na etapa X", não valida contra a contagem real. |
| G-FC2 | Sem fact-checking no ReAct loop | **Médio** | O FactChecker roda apenas no `DomainWorkflow._post_check()`. Respostas do ReAct loop via `LangGraphReActBase` não passam por FactChecker. |

---

## 3.9. DomainWorkflow — Pipeline de Processamento

### 3.9.1 Pipeline Completo

```
PRE_CHECK (FairnessGuard) →
  RESOLVE_REFERENCES (pronomes/contexto) →
    SMART_EXTRACT (regex params) →
      ANALYZE_INTENT (domínio classifica) →
        EXECUTE (ReAct agent ou heurística) →
          FORMAT (metadata + sugestões) →
            POST_CHECK (FactChecker)
```

### 3.9.2 Características

| Aspecto | Status |
|---------|--------|
| FairnessGuard na entrada | ✅ |
| FactChecker na saída | ✅ |
| Learning loop (record_interaction) | ✅ |
| Reference resolution (pronomes) | ✅ |
| Smart extraction (regex) | ✅ com cache |
| Dual-path: ReAct agent ou heurística | ✅ |
| Execution log completo | ✅ |

---

## 3.10. Observabilidade dos Agentes

### 3.10.1 AuditCallback

**Status: ✅ Implementado** — `lia_audit/audit_callback.py`

- Compatível com LangGraph, LangChain e ReAct loop custom
- Captura: LLM calls (prompt/response preview, tokens, latência), tool calls (input/output, latência, sucesso), nós visitados
- Gera `ExecutionAuditRecord` para persistência

### 3.10.2 ReActObserver

- Telemetria detalhada por iteração do ReAct loop
- Logs de reasoning, tool calls, decisions, stage transitions
- Integrado em todos os agentes ReAct

### 3.10.3 Métricas Prometheus

- `router_tier_hit_total` — hits por tier do CascadedRouter
- `router_latency_ms` — latência por tier
- `router_confidence_histogram` — distribuição de confiança
- `fairness_blocks_total` — bloqueios por categoria
- `agent_iterations_total` — iterações por domínio/ação
- `circuit_breaker_state` — estado dos circuit breakers

---

## 3.11. Resumo de Gaps — Classificação por Severidade

### Crítico (1)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-M1 | PII não mascarada nos prompts ao LLM | PII Masking | Dados de candidatos (nome, CPF, email) enviados ao provider LLM. Violação LGPD Art. 6. |

### Alto (6)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-P1 | Ausência de instrução EU AI Act nos prompts | Prompts | Não-conformidade com EU AI Act para clientes europeus. |
| G-F1 | Camada 3 semântica não integrada no workflow | FairnessGuard | Vieses reformulados/sutis podem passar. |
| G-C1 | Sem escalação humana no fluxo principal | Confiança | EU AI Act Art. 14 requer human oversight; o sampling service existe mas não está no fluxo. |
| G-M2 | Sem blind review pré-LLM | PII/Fairness | Atributos protegidos (nome, idade) no prompt — proteção depende do LLM. |
| G-M3 | Sem módulo de remoção de atributos protegidos | PII/Fairness | Nenhuma função dedicada para anonymizar candidato antes do prompt de triagem. |
| G-RL1 | ReAct loop não aplica FairnessGuard na saída | FairnessGuard | Respostas geradas pelo loop podem conter linguagem enviesada. |

### Médio (8)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-R1 | Silent fallback para recruiter_assistant | Router | Roteamento potencialmente incorreto. |
| G-P2 | Ausência de instrução de explicabilidade | Prompts | Decisões de IA sem justificativa estruturada. |
| G-F2 | `log_check()` não chamado automaticamente | FairnessGuard | Auditoria de fairness incompleta. |
| G-C2 | Confidence scoring heurístico | Confiança | Scores de confiança não calibrados. |
| G-C3 | ConfidencePolicyService limitado ao Wizard | Confiança | Decisões de triagem sem política de confiança. |
| G-CB1 | Sem alerting quando circuit abre | Resiliência | Operações podem degradar sem notificação. |
| G-RL2 | Resposta do ReAct sem PII scrubbing | PII | Dados de candidato podem aparecer na resposta. |
| G-FC1 | FactChecker não consulta dados reais | FactChecker | Verificação contra ranges estáticos, não dados do banco. |

### Baixo (4)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-R2 | Cache key MD5 | Router | Risco teórico de colisão. |
| G-P3 | Persona do Orchestrator simplificada | Prompts | Fallback sem diretrizes éticas completas. |
| G-F3 | Cobertura de idiomas limitada | FairnessGuard | Relevante apenas para expansão internacional. |
| G-CB2 | Duas implementações de circuit breaker | Resiliência | Complexidade de manutenção. |
| G-FC2 | FactChecker ausente no ReAct loop direto | FactChecker | Respostas do LangGraph nativo sem fact-check. |
| G-RL3 | Sem rate limiting por sessão | ReAct Loop | Potencial abuso por sessão. |

---

## 3.12. Pontos Fortes Identificados

1. **Arquitetura domain-driven madura** — Separação clara entre orquestração, roteamento, domínios e agentes.
2. **100% dos agentes com EnhancedAgentMixin** — Memória, autonomia e aprendizado uniformes.
3. **FairnessGuard com 9 categorias e 42+ padrões regex** — Cobertura ampla de viés explícito.
4. **AutonomyEngine com 3 níveis de guardrails** — Configurável por empresa.
5. **CascadedRouter com 6 tiers e métricas** — Roteamento sofisticado com observabilidade.
6. **AuditCallback automático** — Agentes não precisam saber que estão sendo auditados.
7. **HumanReviewSamplingService** — 5% de decisões com sampling determinístico.
8. **Circuit breakers para 7 serviços** — Resiliência robusta.
9. **Token budget por sessão** — Controle de custos no ReAct loop.
10. **Dual-path LangGraph nativo / ReAct custom** — Migração incremental sem risco.

---

## 3.13. Recomendações Priorizadas

### Prioridade 1 — Crítico (Implementar imediatamente)

| # | Recomendação | Esforço |
|---|-------------|---------|
| R1 | Implementar PII masking nos prompts enviados ao LLM (G-M1). Criar módulo `prompt_pii_filter` que remove/mascara CPF, email, telefone antes de montar o prompt. | Médio |

### Prioridade 2 — Alto (Implementar em 30 dias)

| # | Recomendação | Esforço |
|---|-------------|---------|
| R2 | Implementar blind review: criar `candidate_anonymizer` que remove nome, idade, foto e gênero inferido antes de prompts de triagem/ranking (G-M2, G-M3). | Médio |
| R3 | Integrar `check_semantic()` no `DomainWorkflow._pre_check()` para queries com soft_warnings (G-F1). | Baixo |
| R4 | Integrar `HumanReviewSamplingService.should_flag_for_review()` no `DomainWorkflow._execute()` para decisões de triagem/ranking/rejeição (G-C1). | Médio |
| R5 | Adicionar FairnessGuard check na SAÍDA do ReAct loop (G-RL1). Aplicar `check_implicit_bias()` na resposta final. | Baixo |
| R6 | Adicionar instruções EU AI Act nos prompts éticos (G-P1). Referenciar Art. 14, 52, Anexo III. | Baixo |

### Prioridade 3 — Médio (Implementar em 60 dias)

| # | Recomendação | Esforço |
|---|-------------|---------|
| R7 | Automatizar `FairnessGuard.log_check()` dentro do `DomainWorkflow` (G-F2). | Baixo |
| R8 | Expandir `ConfidencePolicyService` para decisões de triagem (G-C3). | Médio |
| R9 | Adicionar alerting via webhook/email quando circuit breaker abre (G-CB1). | Baixo |
| R10 | Conectar FactChecker a dados reais do banco para validação de contagens (G-FC1). | Médio |
| R11 | Adicionar PII scrubbing na resposta do ReAct loop antes de retornar ao usuário (G-RL2). | Baixo |

---

## 4. Análise Detalhada: LGPD e Proteção de Dados

## 4.1. PII Masking Filter

**Arquivo**: `lia-agent-system/app/shared/pii_masking.py`

### Status: Parcialmente Implementado

**O que existe:**
- Regex patterns para CPF, email, telefone BR, nomes em logs
- `PIIMaskingFilter` como logging.Filter aplicável a loggers
- `install_global_pii_masking()` para instalação no root logger
- Instalação global confirmada em `app/main.py`, `apps/api-funil/main.py`, `apps/api-vagas/main.py`, `apps/api-onboarding/main.py`
- Usado no `celery_tasks.py` e `streaming_callback.py`

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| PII-1 | Cobertura limitada de padrões PII | Alto | Faltam patterns para: RG, CNH, CNPJ, passaporte, endereço completo, data de nascimento, número de cartão. A LGPD Art. 5 define dados pessoais de forma ampla. |
| PII-2 | Sem proteção para dados sensíveis (Art. 11) | Crítico | Dados sensíveis (origem racial, opinião política, religião, saúde, vida sexual, dado genético/biométrico) não possuem mascaramento. O modelo `Candidate` armazena `diversity_race_ethnicity`, `diversity_disability`, `diversity_lgbtqia` sem mascaramento em logs. |
| PII-3 | NAME_IN_LOG_PATTERN é frágil | Médio | O regex de nomes só captura padrões `name="valor"` — nomes em texto livre (ex: "Processando João Silva") não são mascarados. |
| PII-4 | Sem mascaramento em exception tracebacks | Alto | `logger.error(f"Error: {e}", exc_info=True)` em vários endpoints expõe PII nas stack traces. O filtro PII atua em `record.msg` e `record.args`, mas não em `record.exc_info`. |
| PII-5 | Sem mascaramento de PII em payloads JSON/dicts | Médio | O filtro só processa strings. Structured logging com dicts no `extra={}` não é mascarado recursivamente. |
| PII-6 | Sem proteção contra PII em prompts LLM | Alto | O `pii_masking.py` é somente para logs. Não há evidência de mascaramento de PII antes de enviar prompts para LLMs (OpenAI/Anthropic). Dados como nome, email, CPF do candidato podem ser enviados ao LLM. |

---

## 4.2. Consent Management

**Arquivos**: `consent_management.py`, `consent_checker_service.py`, modelos `ConsentVersion`, `ConsentEvent`, `ConsentRecord`, `LGPDConsent`

### Status: Substancialmente Implementado

**O que existe:**
- Consent versionado com hash SHA256 do conteúdo
- Proof hash SHA256 por evento de consentimento (IP, timestamp, email, tipo)
- Eventos de consentimento: granted, revoked, renewed, expired
- Canais: web, whatsapp, email, api
- Renovação com período configurável
- Revogação com criação de evento revoked
- ConsentCheckerService com soft enforcement (ausente → aviso, revogado → bloqueio)
- HTTP 451 mencionado na docstring do ConsentCheckerService mas **NÃO implementado de fato** — o bloqueio retorna `ConsentCheckResult(allowed=False)` sem gerar HTTP 451

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| CON-1 | HTTP 451 (Unavailable For Legal Reasons) não implementado | Alto | O ConsentCheckerService documenta HTTP 451 para consentimento revogado, mas retorna apenas `allowed=False`. O código chamador deveria retornar HTTP 451, mas não há evidência de uso real do ConsentCheckerService nos endpoints de IA/screening. |
| CON-2 | Dois sistemas de consent paralelos sem integração | Alto | Existem dois modelos de consent independentes: (1) `ConsentRecord` (observability.py) e (2) `ConsentVersion`+`ConsentEvent` (consent_management.py) e (3) `LGPDConsent` (communication_settings.py). O ConsentCheckerService usa `LGPDConsent`, enquanto a API `/consent/` usa `ConsentVersion`+`ConsentEvent`. Não há sincronização entre eles. |
| CON-3 | ConsentCheckerService não integrado em endpoints de IA | Crítico | Não há evidência de que o `ConsentCheckerService.check_candidate_consent()` é chamado antes de operações de scoring, screening ou ranking. O serviço existe mas parece não estar wired nos endpoints reais. |
| CON-4 | Sem consent para processamento de dados pelo LLM | Alto | Não existe tipo de consentimento específico para "envio de dados pessoais a provedores de IA terceirizados" (OpenAI, Anthropic). A LGPD Art. 33 (transferência internacional) e Art. 7 (bases legais) exigem isso. |
| CON-5 | Sem mecanismo de re-consent automático | Médio | Quando uma nova versão de termos é publicada, não há workflow automático para solicitar re-consent dos candidatos. O campo `renewal_period_days` existe mas o workflow de notificação de expiração não está implementado. |
| CON-6 | Granularidade de consentimento insuficiente | Médio | O `ConsentCheckerService` mapeia 4 purposes (ai_screening, ai_scoring, ai_video_analysis, ai_comparison) todas para "SCREENING". A granularidade real é baixa — candidato não pode consentir para scoring mas recusar video_analysis. |

---

## 4.3. LGPD Cleanup Service (Data Retention)

**Arquivo**: `lgpd_cleanup_service.py`

### Status: Implementado com Gaps

**O que existe:**
- Períodos de retenção configuráveis: rejected/withdrawn (90 dias), interview_notes (180 dias), screening/ai_logs (365 dias)
- Dry-run mode para validação
- Scoped por company_id (multi-tenant)
- Exclusão de: Candidates, VacancyCandidate, AiConsumption
- Monitoramento com `get_pending_deletions_count()`

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| RET-1 | Sem exclusão de dados relacionados em tabelas auxiliares | Alto | O cleanup deleta `Candidate` mas não deleta explicitamente: `CandidateExperience`, `CandidateEducation`, `ViewedCandidate`, `CandidateFavorite`, `CandidateHidden`, `CandidateSearch`, `CreditsUsage`, `ExternalCandidateProfile`. Depende de CASCADE do banco — verificação necessária. |
| RET-2 | Sem exclusão de dados em storage externo | Crítico | `resume_url`, `avatar_url`, `cover_letter`, `diversity_documents` podem apontar para arquivos no object storage (S3/GCS). O cleanup não remove esses arquivos — dados pessoais ficam residuais no storage. |
| RET-3 | Sem anonimização como alternativa à exclusão | Alto | A LGPD Art. 16 permite anonimização como alternativa à exclusão. O serviço só implementa hard delete. Para analytics e compliance, dados anonimizados deveriam ser preservados. |
| RET-4 | Sem agendamento automatizado do cleanup job | Médio | `run_cleanup()` existe mas não há evidência de agendamento via cron/celery beat. O job precisa ser executado manualmente. |
| RET-5 | Audit log do cleanup é via logger, não persistido | Médio | Cada exclusão é logada via `logger.info()`, mas não há registro em tabela de auditoria persistente (audit_logs). Para compliance, o registro de exclusão deveria ser imutável. |
| RET-6 | Sem notificação ao titular sobre exclusão | Baixo | A LGPD não exige notificação de exclusão ao titular, mas é boa prática. Não há workflow de notificação pós-exclusão. |
| RET-7 | Sem exclusão de ConsentEvent e ConsentRecord | Alto | Os registros de consentimento (`consent_events`, `consent_records`) não são incluídos no cleanup. Após exclusão do candidato, registros de consentimento ficam órfãos com PII (email, identifier). |

---

## 4.4. Data Subject Requests (DSR) — Portal do Titular

**Arquivos**: `data_subject_requests.py`, `schemas/data_subject_requests.py`, modelo `DataSubjectRequest`

### Status: Substancialmente Implementado

**O que existe:**
- 7 direitos LGPD Art. 18: access, correction, deletion, portability, objection, restriction, explanation
- SLA de 15 dias úteis com cálculo de deadline (excluindo fins de semana)
- Workflow completo: create → assign → verify-identity → process → complete/reject
- Portal público (sem autenticação) para criação e tracking de requests
- Audit trail em JSON por request
- Multi-tenant via X-Company-ID
- Verificação de identidade do titular
- Estatísticas (overdue, SLA compliance rate, by type, by channel)
- Multi-canal: portal, email, whatsapp, phone, in_person, api

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| DSR-1 | Sem execução automatizada dos direitos | Alto | O endpoint `/complete` registra a resposta textual, mas não executa a ação de fato (ex: deletion não deleta dados, portability não gera export, correction não atualiza dados). Tudo é manual. |
| DSR-2 | Endpoint público sem rate limiting | Alto | O endpoint `POST /data-subject-requests/` é público (sem autenticação). Não há rate limiting específico — vulnerável a abuse/DoS. |
| DSR-3 | Sem verificação de identidade antes de tracking | Médio | O endpoint `GET /track/{request_id}` retorna status sem verificação — qualquer pessoa com o UUID pode acompanhar. Deveria exigir email ou CPF para confirmar identidade. |
| DSR-4 | Audit trail como JSON mutável | Alto | O `audit_trail` é um campo JSON na mesma row do request — pode ser alterado via UPDATE direto. Para compliance, deveria ser uma tabela separada com registros imutáveis (INSERT-only). |
| DSR-5 | Sem notificação automática ao titular | Médio | Mudanças de status (assigned, processing, completed) não enviam notificação por email/WhatsApp ao titular. O titular precisa consultar manualmente via tracking. |
| DSR-6 | SLA não considera feriados | Baixo | O cálculo de SLA (`calculate_sla_deadline`) exclui fins de semana mas não feriados nacionais/regionais. Para cálculo preciso de 15 dias úteis, deveria usar calendário de feriados. |
| DSR-7 | Sem suporte a GDPR Art. 17 (erasure transfronteiriço) | Baixo | Para empresas que operam na EU, não há mecanismo para propagar exclusão para subprocessadores internacionais. |

---

## 4.5. Criptografia (Encryption)

**Arquivo**: `app/shared/encryption.py`

### Status: Parcialmente Implementado

**O que existe:**
- Fernet (AES-128-CBC) para criptografia simétrica at-rest
- Chave via env var `ENCRYPTION_KEY`
- Proteção em produção: raise RuntimeError se ENCRYPTION_KEY não definida
- Usado para: credenciais de ATS (api_key, api_secret), credenciais Google Calendar

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| ENC-1 | Dados pessoais de candidatos não são criptografados at-rest | Crítico | Campos como `cpf`, `email`, `phone`, `date_of_birth`, `resume_text`, `diversity_*` são armazenados em texto plano no banco. Apenas credenciais de integração são criptografadas. |
| ENC-2 | Sem rotação de chave de criptografia | Alto | Fernet usa chave fixa. Não há mecanismo de rotação de chave (re-encrypt com nova chave). |
| ENC-3 | Chave efêmera em desenvolvimento | Médio | Em dev, uma chave efêmera é gerada a cada restart — dados criptografados anteriormente se tornam irrecuperáveis. |
| ENC-4 | Decryption fallback silencioso | Alto | `decrypt_value()` retorna o ciphertext original em caso de erro — falha silenciosa pode expor dados criptografados em contextos onde se espera texto plano. |
| ENC-5 | Sem criptografia de campo no modelo Candidate | Crítico | O modelo `Candidate` armazena `cpf`, `date_of_birth`, `diversity_race_ethnicity`, `diversity_disability`, `diversity_lgbtqia` etc. sem nenhuma criptografia. São dados sensíveis (Art. 11 LGPD). |
| ENC-6 | Sem TLS enforcement no código | Médio | Não há verificação de TLS/HTTPS nas conexões de banco ou APIs externas no código. Depende de configuração de infra. |

---

## 4.6. Data Access Logging

**Modelo**: `DataAccessLog` em `observability.py`

### Status: Modelo Existe, Uso Limitado

**O que existe:**
- Modelo `DataAccessLog` com campos: user_id, data_subject_id, data_type, operation, pii_fields, purpose, legal_basis, ip_address
- Suporte a tipos: view, export, delete, update, create, anonymize
- Tipos de dados rastreados: cv, score, parecer, personal_info, contact_info, interview_notes, assessment_results

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| DAL-1 | Data Access Logging não integrado nos endpoints | Crítico | O modelo `DataAccessLog` existe mas não há chamadas para registrar acessos nos endpoints de candidatos, CVs, scores. Não há middleware de data access logging. |
| DAL-2 | Sem logging automático de acesso a dados pessoais | Crítico | Quando um recrutador visualiza perfil de candidato (`GET /candidates/{id}`), não é registrado no DataAccessLog. Violação do princípio de accountability (LGPD Art. 6, VIII). |
| DAL-3 | Sem logging de export/download de dados | Alto | Downloads de CVs, exports de candidatos em bulk não são rastreados. |
| DAL-4 | Sem purpose tracking nas queries | Alto | Queries de candidatos não registram finalidade (purpose) do acesso. A LGPD exige que o tratamento de dados tenha finalidade específica (Art. 6, I). |

---

## 4.7. Multi-tenancy Isolation

### Status: Implementado via X-Company-ID Header

**O que existe:**
- Todos os endpoints LGPD usam `X-Company-ID` header para isolamento
- Queries sempre filtram por `company_id`
- Validação de formato UUID no header
- `VacancyCandidate.company_id` para isolamento de candidatos por vaga

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| MT-1 | X-Company-ID header sem validação de ownership | Crítico | O header X-Company-ID é validado apenas como UUID. Não há verificação de que o usuário autenticado pertence àquela empresa. Um usuário pode acessar dados de outra empresa forjando o header. |
| MT-2 | Sem Row-Level Security (RLS) no banco | Alto | O isolamento é feito na camada de aplicação (WHERE company_id = X). Sem RLS no PostgreSQL, um bug no código pode causar data leak cross-tenant. |
| MT-3 | DPO list endpoint sem filtro por company_id | Médio | O endpoint `GET /lgpd/dpo` lista TODOS os DPOs (sem filtro por company_id do header, usa apenas filtros opcionais). Um admin pode ver DPOs de todas as empresas. |
| MT-4 | Candidate model sem company_id obrigatório | Alto | O modelo `Candidate` não tem campo `company_id` diretamente — o isolamento é feito via `VacancyCandidate.company_id`. Um candidato compartilhado entre empresas pode ter dados acessados cross-tenant. |

---

## 4.8. DPO Management

**Endpoints**: `/lgpd/dpo`

### Status: Implementado

**O que existe:**
- CRUD completo para DPO Registry
- Campos: nome, email, telefone, data de nomeação, URL de contato público, status ativo
- Constraint unique por company_id

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| DPO-1 | Sem notificação de DPO em eventos de breach | Médio | Quando um breach é reportado, o DPO não é notificado automaticamente. O workflow de breach e DPO não estão integrados. |
| DPO-2 | Sem validação de obrigatoriedade | Médio | Não há validação de que toda empresa tem um DPO registrado. A LGPD exige nomeação de DPO (Art. 41). |
| DPO-3 | URL público do DPO não exposta ao candidato | Baixo | O `public_contact_url` existe no modelo mas não há endpoint público para candidatos encontrarem o DPO da empresa. |

---

## 4.9. Breach Notification Workflow

**Endpoints**: `/lgpd/breaches`

### Status: Substancialmente Implementado

**O que existe:**
- Workflow completo: detected → investigating → notified → resolved
- Tracking de notificação ANPD com deadline de 48h
- Tracking de notificação a titulares afetados
- Severidade: low, medium, high, critical
- Campos: affected_data_types, affected_count, remediation_actions
- Cálculo de horas desde detecção para verificar deadline de 48h

**Gaps identificados:**

| # | Gap | Severidade | Detalhe |
|---|-----|-----------|---------|
| BRE-1 | Sem notificação automática ANPD | Alto | O workflow marca que ANPD foi notificada, mas não envia notificação real (email, API). É apenas um registro manual. |
| BRE-2 | Sem alerta de deadline de 48h | Alto | Não há job/alerta automático quando o deadline de 48h está se aproximando ou foi excedido. A verificação é retroativa (ao marcar ANPD notified). |
| BRE-3 | Sem integração com DPO | Médio | Breach criado não notifica automaticamente o DPO registrado da empresa. |
| BRE-4 | Sem template de comunicação ANPD | Baixo | Não há template padrão para comunicação à ANPD conforme formato exigido pela autoridade. |
| BRE-5 | Sem categorização de tipos de dados afetados | Baixo | `affected_data_types` é free-text JSON. Deveria usar taxonomia padronizada (dados pessoais, sensíveis, financeiros). |

---

### 4.10. Resumo de Gaps LGPD por Severidade

| Severidade | Quantidade | IDs |
|-----------|-----------|-----|
| **Crítico** | 8 | PII-2, CON-3, RET-2, ENC-1, ENC-5, DAL-1, DAL-2, MT-1 |
| **Alto** | 16 | PII-1, PII-4, PII-6, CON-1, CON-2, CON-4, RET-1, RET-3, RET-7, DSR-1, DSR-2, DSR-4, ENC-2, ENC-4, DAL-3, DAL-4, MT-2, MT-4, BRE-1, BRE-2 |
| **Médio** | 11 | PII-3, PII-5, CON-5, CON-6, RET-4, RET-5, DSR-3, DSR-5, ENC-3, ENC-6, MT-3, DPO-1, DPO-2, BRE-3 |
| **Baixo** | 6 | RET-6, DSR-6, DSR-7, DPO-3, BRE-4, BRE-5 |

### 4.11. Top 5 Recomendações Prioritárias LGPD

1. **[CRÍTICO] Implementar criptografia at-rest para dados pessoais sensíveis** (ENC-1, ENC-5): CPF, dados de diversidade, data de nascimento devem ser criptografados no banco.

2. **[CRÍTICO] Integrar ConsentCheckerService nos endpoints de IA** (CON-3): O serviço existe mas não é chamado antes de scoring/screening. Wire o checker em todos os endpoints de decisão automatizada.

3. **[CRÍTICO] Implementar Data Access Logging nos endpoints de candidatos** (DAL-1, DAL-2): Criar middleware que registre automaticamente acessos a dados pessoais com purpose e legal basis.

4. **[CRÍTICO] Validar ownership do X-Company-ID contra usuário autenticado** (MT-1): O header pode ser forjado. Implementar validação de que o usuário pertence à empresa informada.

5. **[CRÍTICO] Ampliar PII masking para dados sensíveis e prompts LLM** (PII-2, PII-6): Mascarar dados de diversidade em logs e implementar PII scrubbing antes de enviar dados ao LLM.

---

## 5. Análise Detalhada: Auditoria, Logs e Observabilidade

## 5.1. Audit Writer — Persistência Dual (PostgreSQL + Object Storage)

### Status: Implementado

**Arquitetura encontrada** (`libs/audit/lia_audit/`):
- `AuditWriter` com persistência dual: metadados leves em PostgreSQL (`audit_execution_metadata`) e payload completo em Object Storage (Local/S3).
- `AuditCallback` integrado ao LangChain/LangGraph via `BaseCallbackHandler` — captura automática de LLM calls, tool calls e transições de nós sem que agentes precisem saber.
- API manual (`on_chain_start_manual`, `on_llm_call`, `on_tool_call`, `on_chain_end_manual`) para loops ReAct custom.
- `ExecutionAuditRecord` com campos: execution_id, session_id, user_id, company_id, domain, agent_type, timestamps, duration, tools_used, nodes_visited, confidence, error, entries (payload completo).

**Storage**:
- `LocalFileStorage` para dev/staging: arquivos JSON em `./audit_logs/{domain}/{date}/{company_id}/{exec_id}.json`
- `S3Storage` para produção: `s3://{bucket}/{prefix}/{path}` com `ServerSideEncryption=AES256`
- Factory pattern via `get_audit_storage()` configurado por `AUDIT_STORAGE_TYPE` (file|s3)

**Lifecycle Policy S3**:
- Hot: 0-90 dias (S3 Standard)
- Warm: 90-365 dias (Glacier Instant Retrieval)
- Cold: 365-2555 dias (Glacier Deep Archive)
- Delete: após 2555 dias (7 anos — SOX compliance)

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| A1 | **Sem proteção contra adulteração (WORM/immutability)**: O S3Storage usa `put_object` padrão. Não há Object Lock, versionamento obrigatório, ou hash de integridade nos registros. Registros podem ser sobrescritos ou deletados. | **Crítico** | SOX, BCB-498, SOC-2 |
| A2 | **Erros de persistência silenciados**: `AuditWriter.persist()` captura exceções e apenas loga — nunca propaga. Se ambos destinos (PG + S3) falharem, a execução do agente prossegue sem registro de auditoria, sem alerta. | **Alto** | SOX, SOC-2 |
| A3 | **Sem assinatura digital/hash de integridade** nos registros de auditoria. Não há campo de hash SHA-256 ou assinatura que prove que o registro não foi alterado após gravação. | **Alto** | SOX, BCB-498, ISO 27001 |
| A4 | **Lifecycle policy não aplicada automaticamente**: `apply_lifecycle_policy()` existe mas não é chamado durante startup ou deploy. Requer ação manual. | **Médio** | SOX |
| A5 | **`ON CONFLICT DO NOTHING`** no INSERT de metadados: se um execution_id colidir (improvável com UUID4), o registro é silenciosamente descartado. | **Baixo** | SOC-2 |
| A6 | **Sem batch/retry para persistência**: a persistência é fire-and-forget via `loop.create_task`. Não há retry com backoff, dead-letter queue, ou buffering em caso de indisponibilidade temporária do PostgreSQL/S3. | **Alto** | BCB-498, SOC-2 |

---

## 5.2. Structured Logging Middleware

### Status: Implementado

**Componentes encontrados**:
- `StructuredLoggingMiddleware` (`app/core/logging_middleware.py`): emite um log JSON por request com request_id, method, path, status_code, duration_ms, company_id, user_id, tier.
- `RequestIdMiddleware` (`app/middleware/request_id.py`): gera UUID por request, aceita `X-Request-ID` do cliente, retorna no response header.
- `JSONFormatter` (`app/core/logging_config.py`): formata logs em JSON para produção com timestamp, level, logger, message, request_id, user_id, exception.
- Tier classification: agent | management | data.
- Middlewares registrados em `main.py`: RequestIdMiddleware + StructuredLoggingMiddleware + RateLimitMiddleware.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| L1 | **Sem correlação request_id nos logs de auditoria de agentes**: O `AuditCallback` e `AuditWriter` não recebem/propagam `request_id`. Impossível correlacionar um request HTTP com a execução de auditoria de agente que ele disparou. | **Alto** | SOC-2, BCB-498 |
| L2 | **company_id e user_id extraídos após call_next**: No `StructuredLoggingMiddleware`, `user_id` e `company_id` são lidos de `request.state` após `call_next`, mas se auth falhar, ficam como "-". Não há indicação de que a auth dependency popula request.state antes do response. | **Médio** | LGPD |
| L3 | **Sem log de request body para endpoints sensíveis**: Apenas path/method/status são logados. Para auditoria SOX/BCB-498, endpoints que alteram dados (POST/PUT/DELETE em pipelines, candidatos, configurações) deveriam ter log do payload de entrada (sanitizado). | **Alto** | SOX, BCB-498 |
| L4 | **Sem log centralizado para stderr/stdout**: Sem evidência de integração com plataforma de log centralizado (ELK, CloudWatch Logs, Datadog). JSONFormatter envia para stdout, mas sem configuração de sink externo. | **Médio** | SOC-2, ISO 27001 |

---

## 5.3. AI Inference Logging (Explainability)

### Status: Implementado

**Componentes encontrados**:
- `AIInferenceLog` model (`libs/models/lia_models/observability.py`): tabela `ai_inference_logs` com campos agent_type, candidate_id, vacancy_id, model_version, input_hash, input_preview, output_summary, decision_type, confidence_score, latency_ms, tokens_used, human_override, feature_attributions, bias_flags.
- `AuditLog` model (`libs/models/lia_models/audit_log.py`): tabela `audit_logs` para decisões de agentes com reasoning (lista de razões), criteria_used, criteria_ignored (protected criteria), human_review tracking, retention_until.
- `AuditService` (`app/shared/compliance/audit_service.py`): service que registra decisões com mapeamento de tipo, protected criteria auto-ignorados, retention periods configuráveis por tipo (730-1825 dias).
- `ExecutionLogStore` + `/explainability` endpoints (`app/api/v1/agent_explainability.py`): timeline de execução, session summary, tool usage stats.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| E1 | **Dois sistemas de auditoria paralelos sem integração**: `AuditLog` (audit_service.py) e `ExecutionAuditRecord` (libs/audit) coexistem sem referência cruzada. Impossível ligar uma decisão de triagem a sua execução de agente detalhada. | **Alto** | SOC-2, EU AI Act |
| E2 | **input_preview limitado a 500 chars sem full payload indexável**: Para explainability completa (EU AI Act Art. 14), o preview de 500 chars pode ser insuficiente. O payload completo vai para object storage mas sem busca estruturada. | **Médio** | EU AI Act |
| E3 | **feature_attributions definido como JSON default=dict mas sem pipeline para populá-lo**: O campo existe no modelo mas não há evidência de que seja preenchido automaticamente por nenhum agente. Explainability incompleta. | **Alto** | EU AI Act, PL 2338/2023 |
| E4 | **Sem versionamento de modelo/prompt**: `model_version` é String(20) mas não há mecanismo automático para capturar qual versão de prompt/modelo foi usada em cada inferência. | **Alto** | EU AI Act, SOC-2 |

---

## 5.4. Data Access Logging

### Status: Implementado

**Componentes encontrados**:
- `DataAccessLog` model: tabela `data_access_logs` com user_id, data_subject_id, data_type (CV, score, personal_info, etc.), operation (view, export, delete, etc.), pii_fields (array), purpose, legal_basis, ip_address, user_agent.
- Tipos de dados rastreados: CV, Score, Parecer, Personal Info, Contact Info, Interview Notes, Assessment Results.
- Operações: View, Export, Delete, Update, Create, Anonymize.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| D1 | **Sem evidência de interceptação automática**: O modelo `DataAccessLog` existe mas não há middleware ou decorator que automaticamente logue acessos a dados pessoais. Depende de chamada manual em cada endpoint. | **Crítico** | LGPD Art. 37, BCB-498 |
| D2 | **Sem campo request_id para correlação**: `DataAccessLog` não tem referência ao request_id do middleware. Impossível correlacionar acesso a dados com o request HTTP. | **Médio** | SOC-2 |
| D3 | **Sem retenção automática/cleanup de DataAccessLog**: Diferente do AuditLog que tem `retention_until`, DataAccessLog não tem política de retenção. | **Médio** | LGPD, SOX |

---

## 5.5. Admin Audit Logs

### Status: Implementado

**Componentes encontrados**:
- `AdminAuditLog` model (`app/models/admin_settings.py`): logs de ações administrativas com company_id, user_id, action, resource_type, resource_id.
- `SOXAuditLog` model (`app/models/audit_logs.py`): logs SOX-compliant com action_category, client_id, user_id, status, evidence.
- API endpoints: `/audit-logs` com filtros (action, resource_type, user_id, date range), paginação, stats, CSV export.
- Retention policies configuráveis com seed de defaults.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| AD1 | **Três modelos de audit log separados sem unificação**: `AuditLog` (decisões IA), `AdminAuditLog` (admin), `SOXAuditLog` (SOX). Auditores precisariam consultar três tabelas/APIs diferentes para ter visão completa. | **Alto** | SOX, SOC-2 |
| AD2 | **AdminAuditLog não tem campo de IP/User-Agent**: Para auditoria bancária, precisa rastrear de onde a ação administrativa foi feita. | **Médio** | BCB-498, SOC-2 |
| AD3 | **Sem imutabilidade nos admin audit logs**: Tabelas regulares em PostgreSQL sem proteção contra UPDATE/DELETE por DBAs ou queries maliciosas. | **Crítico** | SOX, BCB-498 |

---

## 5.6. Sentry Integration e PII Scrubbing

### Status: Implementado

**Componentes encontrados** (`app/core/sentry.py`):
- `init_sentry()` com fallback gracioso (sem DSN → log INFO, sem SDK → log WARNING).
- `send_default_pii=False` — nunca envia PII automaticamente.
- `before_send` hook com PII scrubbing: email, CPF, telefone brasileiro.
- Integrations: FastApiIntegration + StarletteIntegration.
- `traces_sample_rate=0.1` (10% de traces).

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| S1 | **PII scrubbing incompleto**: Padrões cobrem email, CPF, telefone. Faltam: RG, CNH, número de passaporte, endereço, nome completo (mais difícil). | **Médio** | LGPD |
| S2 | **Scrubbing não cobre extra data/tags**: `before_send` scruba exception.values e breadcrumbs.messages, mas não scruba `event.extra`, `event.tags`, `event.contexts`, `event.request.data`. PII pode vazar por esses caminhos. | **Alto** | LGPD |
| S3 | **Inicialização duplicada**: `main.py` inicializa Sentry duas vezes — diretamente via `sentry_sdk.init()` e depois via `init_sentry()`. A segunda chamada é ignorada pelo SDK mas indica inconsistência. A primeira chamada NÃO usa o `before_send` hook de PII scrubbing. | **Crítico** | LGPD |
| S4 | **traces_sample_rate=0.1 pode ser insuficiente** para debugging em produção, mas é aceitável para performance. | **Baixo** | — |

---

## 5.7. Prometheus Metrics

### Status: Implementado

**Componentes encontrados** (`app/observability/metrics.py`):
- 12 métricas estratégicas:
  - LLM: `llm_requests_total` (provider, status), `llm_latency_seconds` (provider), `llm_cost_usd_total` (model, domain)
  - Agent: `agent_iterations_total` (domain, action_type), `agent_tool_failures_total` (domain, tool)
  - Compliance: `fairness_blocks_total` (category)
  - Resilience: `circuit_breaker_state` (service)
  - HTTP: `http_request_duration_seconds` (method, endpoint, status_code)
  - Business: `pipeline_transitions_total`, `candidates_evaluated_total`
  - Router: `router_tier_hit_total`, `router_latency_ms`, `router_confidence_histogram`
- `generate_latest_metrics()` para endpoint `/metrics`

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| P1 | **Sem métricas de audit trail**: Não há contadores para falhas de persistência de auditoria, volume de audit logs gerados, latência de gravação. Se a auditoria falhar silenciosamente, não há alerta Prometheus. | **Alto** | SOX, BCB-498 |
| P2 | **Sem métricas de data access**: Não há contadores para acessos a dados pessoais, DSR (Data Subject Requests) pendentes, ou SLA compliance. | **Médio** | LGPD, BCB-498 |
| P3 | **Sem métricas de consent**: Não há gauge para consentimentos ativos/expirados/revogados. | **Médio** | LGPD |
| P4 | **Sem dashboard Grafana para compliance**: Há diretório `grafana/provisioning/` mas sem dashboards pré-configurados para as métricas de compliance. | **Médio** | SOC-2 |
| P5 | **High cardinality risk**: `http_request_duration_seconds` tem label `endpoint` que pode gerar alta cardinalidade com path params dinâmicos. | **Baixo** | — |

---

## 5.8. Request ID Tracking e Correlação

### Status: Parcialmente Implementado

**Componentes encontrados**:
- `RequestIdMiddleware`: gera UUID4 ou aceita `X-Request-ID` do cliente, salva em `request.state.request_id`, retorna no response header.
- `StructuredLoggingMiddleware`: inclui `request_id` no log JSON por request.
- `JSONFormatter`: propaga `request_id` quando presente em `record`.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| R1 | **request_id não propagado para audit systems**: `AuditCallback`, `AuditWriter`, `AuditService`, `AIInferenceLog`, `DataAccessLog` — nenhum recebe ou armazena request_id. Quebra de rastreabilidade end-to-end. | **Crítico** | SOX, SOC-2, BCB-498 |
| R2 | **request_id não propagado para chamadas inter-serviço**: Se houver comunicação entre microserviços, o request_id não é injetado automaticamente nos headers de saída. | **Médio** | SOC-2 |
| R3 | **Sem trace_id/span_id para distributed tracing**: Apenas request_id simples (UUID). Sem integração com OpenTelemetry ou W3C Trace Context para tracing distribuído. | **Médio** | SOC-2 |

---

## 5.9. Health Check Endpoints

### Status: Implementado

**Componentes encontrados**:
- `/health` (`app/api/v1/system_health.py`): verifica DB, rate_limiter, task_manager, multi_channel, external_services (Anthropic, OpenAI, WorkOS). Retorna 200/503.
- `/health-check/*` (`app/api/v1/health_check.py`): compliance health check com items por framework (SOX, SOC2, ISO27001, LGPD, BCB498, EUAI, NYC144), status tracking, history, export CSV/JSON, seed, sync-from-library.
- `/health/langgraph`: health check específico para LangGraph.

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| H1 | **Health check não verifica subsistema de auditoria**: `/health` verifica DB, rate limiter, task manager, mas não verifica se o AuditWriter consegue gravar em S3/local, se o Prometheus está exportando métricas, ou se o Sentry está conectado. | **Alto** | SOC-2, BCB-498 |
| H2 | **Sem health check dedicado para S3/storage de auditoria**: Se o bucket S3 de auditoria estiver inacessível, não há alerta até que um agente tente gravar. | **Alto** | SOX, BCB-498 |
| H3 | **Sem readiness vs liveness probe separation**: Apenas um endpoint `/health`. Para Kubernetes, deveria ter `/health/ready` (pode receber tráfego) e `/health/live` (processo está rodando). | **Baixo** | — |

---

## 5.10. Imutabilidade da Trilha de Auditoria

### Status: Ausente

### Gaps Identificados

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| I1 | **Nenhuma garantia de imutabilidade em PostgreSQL**: Tabelas `audit_logs`, `audit_execution_metadata`, `ai_inference_logs`, `data_access_logs`, `sox_audit_logs` são tabelas regulares. DBAs com acesso podem UPDATE/DELETE registros. Sem triggers de proteção, sem audit de audit. | **Crítico** | SOX, BCB-498, SOC-2 |
| I2 | **S3 sem Object Lock/WORM**: `S3Storage.save()` usa `put_object` padrão. Não configura S3 Object Lock (Governance ou Compliance mode). Registros podem ser deletados. | **Crítico** | SOX, BCB-498 |
| I3 | **LocalFileStorage completamente mutável**: Em dev/staging, arquivos JSON podem ser editados ou deletados livremente. | **Baixo** | — (apenas dev) |
| I4 | **Sem chain hashing (blockchain-style)**: Não há hash encadeado entre registros consecutivos que detectaria inserção, remoção ou alteração de registros intermediários. | **Alto** | SOX, BCB-498 |

---

## 5.11. Adequação para Homologação Bancária

### Avaliação por Framework

#### BCB-498 (Resolução CMN 4893/Circular BCB)
| Requisito | Status | Gap Ref |
|-----------|--------|---------|
| Trilha de auditoria imutável | Ausente | I1, I2 |
| Rastreabilidade end-to-end | Parcial | R1, L1 |
| Log de acesso a dados pessoais (automático) | Ausente | D1 |
| Retenção mínima 5 anos | Implementado (7 anos no S3) | — |
| Health monitoring de componentes críticos | Parcial | H1, H2 |
| Alertas para falhas de auditoria | Ausente | P1, A2 |
| Segregação de ambientes de auditoria | Implementado (dev/prod) | — |

#### SOC-2 Type II
| Requisito | Status | Gap Ref |
|-----------|--------|---------|
| Logging de todas as ações administrativas | Implementado | — |
| Correlação de eventos | Parcial | R1, L1 |
| Integridade dos logs | Ausente | I1, I2, A3 |
| Monitoramento de anomalias em logs | Ausente | P1 |
| Retenção configurável | Implementado | — |
| Export para auditores externos | Implementado (CSV/JSON) | — |

#### SOX
| Requisito | Status | Gap Ref |
|-----------|--------|---------|
| Imutabilidade de registros financeiros/decisórios | Ausente | I1, I2 |
| Retenção 7 anos | Implementado | — |
| Segregation of duties (audit trail) | Parcial (modelo existe, sem enforcement) | AD3 |
| Change management audit trail | Parcial | AD1 |

---

## 5.12. Resumo de Gaps por Severidade

### Críticos (6)
1. **D1** — Sem interceptação automática de data access logging
2. **I1** — Sem imutabilidade em PostgreSQL para audit logs
3. **I2** — S3 sem Object Lock/WORM
4. **R1** — request_id não propagado para audit systems
5. **S3** — Sentry inicializado sem PII scrubbing na primeira chamada
6. **AD3** — Sem imutabilidade nos admin audit logs

### Altos (10)
1. **A2** — Erros de persistência de auditoria silenciados
2. **A3** — Sem hash de integridade nos registros
3. **A6** — Sem retry/buffering para persistência
4. **L1** — Sem correlação request_id nos audit de agentes
5. **L3** — Sem log de request body para endpoints sensíveis
6. **E1** — Dois sistemas de auditoria paralelos sem integração
7. **E3** — feature_attributions não populado automaticamente
8. **E4** — Sem versionamento automático de modelo/prompt
9. **P1** — Sem métricas Prometheus para falhas de auditoria
10. **AD1** — Três modelos de audit log sem unificação
11. **I4** — Sem chain hashing entre registros
12. **H1** — Health check não verifica subsistema de auditoria
13. **H2** — Sem health check para S3/storage de auditoria
14. **S2** — PII scrubbing do Sentry não cobre extra/tags/contexts

### Médios (10)
1. **A4** — Lifecycle policy não aplicada automaticamente
2. **L2** — company_id/user_id extraídos pós-call_next
3. **L4** — Sem integração com log centralizado (ELK/CloudWatch)
4. **E2** — input_preview limitado a 500 chars
5. **D2** — DataAccessLog sem request_id
6. **D3** — DataAccessLog sem retenção automática
7. **AD2** — AdminAuditLog sem IP/User-Agent
8. **P2** — Sem métricas de data access
9. **P3** — Sem métricas de consent
10. **P4** — Sem dashboards Grafana para compliance
11. **R2** — request_id não propagado inter-serviço
12. **R3** — Sem OpenTelemetry/distributed tracing
13. **S1** — PII scrubbing incompleto (falta RG, CNH, etc.)

### Baixos (4)
1. **A5** — ON CONFLICT DO NOTHING pode descartar registros
2. **S4** — traces_sample_rate pode ser insuficiente
3. **P5** — High cardinality risk em HTTP metrics
4. **H3** — Sem separação readiness/liveness probes
5. **I3** — LocalFileStorage mutável (apenas dev)

---

## 5.13. Recomendações Priorizadas

### Prioridade 1 — Bloqueadores para Homologação Bancária
1. **Implementar S3 Object Lock (Compliance Mode)** para bucket de auditoria
2. **Criar triggers PostgreSQL para proteger tabelas de audit** contra UPDATE/DELETE
3. **Implementar data access logging automático** via middleware/decorator
4. **Propagar request_id** para todos os sistemas de auditoria (AuditCallback, AuditService, AIInferenceLog)
5. **Corrigir inicialização do Sentry** em main.py para usar `before_send` com PII scrubbing

### Prioridade 2 — Melhorias para SOC-2/SOX
6. **Unificar modelos de audit log** ou criar view materializada que consolide AuditLog + AdminAuditLog + SOXAuditLog
7. **Adicionar hash SHA-256** a cada registro de auditoria para prova de integridade
8. **Implementar retry com backoff** para persistência de auditoria (dead-letter queue)
9. **Adicionar métricas Prometheus** para falhas de auditoria, volume, latência
10. **Health check para subsistema de auditoria** (S3 connectivity, write test)

### Prioridade 3 — Melhorias de Observabilidade
11. **Integrar OpenTelemetry** para distributed tracing
12. **Implementar dashboards Grafana** para métricas de compliance
13. **Adicionar log de request body** (sanitizado) para endpoints sensíveis
14. **Popular feature_attributions** automaticamente nos agentes de decisão
15. **Implementar versionamento automático de prompts** com registro no audit log

---

## 6. Análise Detalhada: Fairness, Bias e DEI

## 6.1. Bias Audit Service (Four-Fifths Rule)

### 6.1.1 Status: Implementado — Parcial

**Arquivo**: `lia-agent-system/app/services/bias_audit_service.py`

**O que está implementado**:
- Cálculo de adverse impact ratio (Four-Fifths Rule) com threshold 0.80
- 4 dimensões demográficas auditadas: gênero, faixa etária, PCD, região
- Dados reais via `RubricEvaluation JOIN Candidate`
- Retorno apenas de estatísticas agregadas (LGPD-safe, sem PII)
- Persistência de snapshot para rastreabilidade histórica (`BiasAuditSnapshot`)
- Histórico de snapshots com isolamento multi-tenant (`company_id`)
- API endpoint: `GET /api/v1/bias-audit/job/{job_id}` e `GET /api/v1/bias-audit/job/{job_id}/history`

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| B01 | **Dimensão raça/etnia ausente**: O Bias Audit Service audita apenas gênero, faixa etária, PCD e região. Raça/etnia NÃO é uma dimensão auditada, apesar de ser protegida pela Constituição Federal Art. 5º, Lei 7.716/89, NYC LL144, e EU AI Act. O modelo `Candidate` pode não ter campo de raça/etnia, mas a ausência dessa dimensão é um gap crítico para compliance. | **Crítico** | NYC LL144, EEOC, CF Art. 5º, EU AI Act |
| B02 | **Faixas etárias inconsistentes entre Bias Audit e Golden Dataset**: O Bias Audit Service usa `<30, 30-44, 45+`. O Golden Dataset usa `25-35, 35-50, 50+`. Essa inconsistência pode mascarar adverse impact em faixas específicas. | **Médio** | Estatuto do Idoso (Lei 10.741/03) |
| B03 | **Ausência de threshold mínimo de amostra**: O cálculo de adverse impact é feito mesmo com 1 candidato por grupo (`count > 0`). Sem tamanho mínimo de amostra, os resultados podem ser estatisticamente insignificantes e gerar falsos alarmes ou falsa segurança. NYC LL144 recomenda mínimo de 30 candidatos por grupo. | **Alto** | NYC LL144, EEOC Guidelines |
| B04 | **Alert level apenas "ok" ou "warning"**: Não existe nível "critical" para ratios extremamente baixos (ex: < 0.50). Ausência de escalação automática para revisão humana quando adverse impact é severo. | **Médio** | EU AI Act Art. 14 |
| B05 | **Auditoria não é periódica/automatizada**: O bias audit é executado on-demand via API. Não há job agendado (cron/Celery) para auditoria periódica automática. NYC LL144 exige auditoria anual por auditor independente. | **Alto** | NYC LL144 (annual bias audit) |
| B06 | **Sem auditor externo/independente**: O bias audit é inteiramente interno. NYC LL144 exige que o bias audit anual seja conduzido por auditor independente externo. | **Crítico** | NYC LL144 §20-871(b) |
| B07 | **Sem publicação obrigatória dos resultados**: NYC LL144 exige que resultados do bias audit sejam publicados no site do empregador. Não há mecanismo de publicação/exportação pública dos resultados. | **Alto** | NYC LL144 §20-871(c) |

---

## 6.2. FairnessGuard — Cobertura em Endpoints de Decisão

### 6.2.1 Status: Implementado — Parcial

**Arquivo**: `lia-agent-system/app/shared/compliance/fairness_guard.py`

**O que está implementado**:
- **Camada 1 (Regex)**: 9 categorias discriminatórias (gênero, raça/etnia, idade, religião, orientação sexual, estado civil, deficiência, maternidade/paternidade, nacionalidade)
- **Camada 2 (Viés implícito)**: 11 termos de viés implícito com mensagens educativas
- **Camada 3 (Semântica via LLM)**: `check_semantic()` usa LLM para detecção semântica avançada
- Audit logging para EU AI Act: `log_check()` persiste resultados em `FairnessAuditLog`
- Métricas Prometheus: `fairness_blocks_total` por categoria
- LGPD-safe: logs não expõem conteúdo do texto avaliado (apenas contagem e tamanho)

**Integração em endpoints/agentes** (23 pontos de uso identificados):
- `rubric_evaluation_service.py` — avaliação de CV
- `main_orchestrator.py` — orquestrador principal
- `toon_service.py` — geração de toon
- `rag_pipeline_service.py` — pipeline RAG
- `personalized_feedback_service.py` — feedback personalizado
- `candidate_report_service.py` — relatório de candidato
- `wsi_interview_graph.py` — entrevista WSI
- `interview_notes.py` — notas de entrevista
- `rubric_evaluation.py` — API de avaliação
- Agentes ReAct: wizard, kanban, talent, jobs_mgmt, pipeline, policy

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| F01 | **Camada 3 (Semântica) depende de importação dinâmica do LLMService**: Se o LLMService falhar, a análise semântica é silenciosamente ignorada (`except (ImportError, Exception)`). Não há fallback robusto nem alerta quando a camada semântica está indisponível. | **Médio** | EU AI Act Art. 9 |
| F02 | **check() loga query[:60] na Camada 1**: Esse fragmento pode conter PII do candidato se o texto avaliado vier de dados do candidato. O teste `test_hard_block_check_does_not_log_full_query` documenta esse comportamento mas não o corrige. | **Médio** | LGPD Art. 46 |
| F03 | **FairnessGuard não é chamado em endpoints de sourcing/busca**: O guard é integrado em agentes e avaliação, mas não foi encontrado no fluxo de busca de candidatos (`search/candidates`). Queries de busca discriminatórias podem passar sem checagem. | **Alto** | LGPD, EU AI Act |
| F04 | **Sem rate limiting por recrutador**: Um recrutador pode tentar múltiplas variações de queries discriminatórias. Não há contagem de tentativas bloqueadas por recrutador para escalação automática (ex: treinamento obrigatório após N bloqueios). | **Médio** | EU AI Act Art. 26 (deployer obligations) |
| F05 | **Cobertura de viés implícito limitada**: Apenas 11 termos de viés implícito. Não cobre vieses socioeconômicos como "domínio do inglês nativo" (pode discriminar contra não-nativos) ou "disponibilidade para viagens frequentes" (pode discriminar contra pessoas com filhos/PCD). | **Baixo** | Best practices |
| F06 | **Ausência de interseccionalidade**: O FairnessGuard avalia categorias isoladamente. Não detecta discriminação interseccional (ex: "mulheres acima de 50 anos" combinando gênero + idade). | **Médio** | EU AI Act, EEOC |

---

## 6.3. Framework de Teste de Viés (4 Níveis)

### 6.3.1 Status: Implementado — Parcial

**Arquivos**:
- `tests/fairness/test_four_fifths_rule.py` — 12 testes de Four-Fifths Rule
- `tests/fairness/test_red_teaming.py` — 12 cenários de red teaming (6 classes)
- `tests/fixtures/golden_dataset.py` — 60 candidatos sintéticos

**Nível 1 — Four-Fifths Rule (EEOC)**: ✅ Implementado
- Testa adverse_impact_ratio >= 0.80 em 4 dimensões
- Cobre todos os pares de grupos dentro de cada dimensão
- Verificações específicas: idosos vs jovens, interior vs SP, PCD vs sem PCD

**Nível 2 — Red Teaming**: ✅ Implementado (6 cenários)
1. Bias Elicitation — LLM output com discriminação
2. Prompt Injection — viés embutido em texto maior
3. Jailbreak — contorno de regras
4. Score Manipulation — reasoning não afeta score
5. Data Exfiltration — PII não vaza via logs
6. Privilege Escalation / Falso Positivo — texto limpo não é bloqueado

**Nível 3 — Golden Dataset**: ✅ Implementado
- 60 candidatos sintéticos com distribuição equilibrada
- 3 tiers de performance (alta/média/baixa × 20 cada)
- Scores determinísticos independentes de dados demográficos
- Validação de integridade do dataset (7 testes)

**Nível 4 — Regression Testing com dados reais**: ❌ Ausente

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| T01 | **Ausência de testes com dados reais (Nível 4)**: Todos os testes usam golden dataset sintético. Não há regression tests com dados de produção anonimizados para validar que o sistema real não produz adverse impact. | **Alto** | NYC LL144, EU AI Act Art. 10 |
| T02 | **Golden dataset não cobre raça/etnia**: O dataset sintético tem gênero, faixa etária, PCD e região, mas NÃO raça/etnia. Isso alinha com o gap B01 do Bias Audit. | **Crítico** | NYC LL144, EEOC, CF Art. 5º |
| T03 | **Red teaming não cobre viés interseccional**: Os cenários testam categorias isoladas. Não há testes para discriminação que combine múltiplas dimensões protegidas. | **Médio** | EU AI Act |
| T04 | **Sem testes de adversarial robustness com unicode/encoding**: O FairnessGuard normaliza NFD, mas não há testes com tentativas de bypass via caracteres invisíveis, homóglifos, ou encoding alternativo. | **Baixo** | Best practices |
| T05 | **Sem benchmark de falso-positivo quantificado**: O teste de falso positivo (Cenário 6) usa apenas 2 exemplos. Não há benchmark com corpus grande para medir taxa de falso positivo em escala. | **Médio** | Best practices |

---

## 6.4. Red Teaming Scenarios

### 6.4.1 Status: Implementado — Parcial

Detalhado na seção 3.1 acima. Cobertura dos 6 cenários obrigatórios:

| Cenário | Status | Critério | Resultado |
|---------|--------|----------|-----------|
| Bias Elicitation | ✅ | Bloqueio de output com viés | Passa |
| Prompt Injection | ✅ | Detecção de viés em texto maior | Passa |
| Jailbreak | ✅ | Taxa bypass = 0% | Passa (para padrões conhecidos) |
| Score Manipulation | ✅ | Score independente de reasoning | Passa |
| Data Exfiltration | ✅ | Data leak = 0% via logs | Passa |
| Privilege Escalation | ✅ | Falsos positivos = 0% | Passa (amostra pequena) |

**Gaps adicionais**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| R01 | **Red teaming não é executado periodicamente**: Os testes existem mas não há evidência de execução periódica em CI/CD como gate de qualidade. | **Médio** | EU AI Act Art. 9(7) |
| R02 | **Sem red teaming externo**: Todos os cenários são internos. EU AI Act e NYC LL144 recomendam avaliação por terceiros independentes. | **Alto** | EU AI Act, NYC LL144 |
| R03 | **Sem testes de prompt injection avançado**: Os testes cobrem injeção simples. Não há testes com técnicas avançadas (DAN, jailbreak chains, encoding attacks). | **Médio** | Best practices |

---

## 6.5. Model Drift Detection

### 6.5.1 Status: Implementado — Completo

**Arquivos**:
- `app/services/model_drift_service.py` — 4 triggers de drift
- `app/services/drift_alert_service.py` — alertas automáticos (Bell + Teams)
- `app/api/v1/drift.py` — API endpoints
- `app/jobs/drift_job.py` — batch job para todas as empresas

**O que está implementado**:
- **4 triggers**: score_drift (>0.5), approval_drift (>10pp), cost_drift (>20%), latency_drift (>50% P95)
- Comparação janela recente (7 dias) vs baseline (7 dias anteriores)
- Alert levels: ok / warning (1 trigger) / critical (2+ triggers)
- Notificações automáticas via Bell + Teams
- Endpoints: `GET /api/v1/drift/status`, `POST /api/v1/drift/run-batch`
- Avaliação de saúde dos agentes por domínio

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| D01 | **Drift por dimensão demográfica não implementado**: O drift detection monitora score médio global, mas NÃO detecta drift diferencial por grupo demográfico. Ex: score médio pode permanecer estável enquanto score de candidatos 50+ cai significativamente. | **Alto** | EU AI Act Art. 9(4), EEOC |
| D02 | **Sem persistência de histórico de drift**: O `DriftStatus` é calculado on-demand e retornado via API, mas não é persistido no banco. Ausência de série temporal para análise de tendências de longo prazo. | **Médio** | SOX, ISO 27001 |
| D03 | **Score drift queries não filtram por company_id**: As queries `_score_drift` e `_approval_drift` não incluem `company_id` no filtro WHERE, o que quebra isolamento multi-tenant. Cost e latency drift filtram corretamente. | **Alto** | Multi-tenancy, LGPD |
| D04 | **Janela fixa de 7 dias**: Não permite configuração por empresa ou período sazonal. Picos em períodos de contratação intensiva podem gerar falsos alarmes. | **Baixo** | Best practices |

---

## 6.6. Taxonomia de Incidentes de IA

### 6.6.1 Status: Implementado — Parcial

**Arquivo**: `lia-agent-system/libs/models/lia_models/observability.py`

**O que está implementado**:
- `IncidentType` enum: 7 tipos (DATA_BREACH, UNAUTHORIZED_ACCESS, SYSTEM_FAILURE, BIAS_DETECTED, SLA_VIOLATION, POLICY_VIOLATION, PRIVACY_VIOLATION)
- `IncidentSeverity` enum: 4 níveis (LOW, MEDIUM, HIGH, CRITICAL)
- `IncidentReport` model com campos de tracking completo
- `EvaluationDimension` enum: 11 dimensões de viés (alinhado com Tezi AI)
- `BiasComplianceFramework` enum: 5 frameworks (NYC_LL144, CO_SB205, EU_AI_ACT, CA_FEHA, LGPD_BRAZIL)

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| I01 | **Ausência de tipo de incidente para "Hallucination/Fabrication"**: O enum IncidentType não inclui "AI_HALLUCINATION" ou "FACTUAL_ERROR". Fabricação de qualificações de candidatos pelo LLM é um risco real que deve ter tipo próprio para tracking. | **Médio** | EU AI Act Art. 15 |
| I02 | **Ausência de tipo para "Discriminatory Decision"**: BIAS_DETECTED indica detecção, mas não há tipo para quando uma decisão discriminatória efetivamente ocorreu e foi identificada post-hoc. | **Médio** | EU AI Act Art. 62 |
| I03 | **Sem workflow de resposta a incidente de IA**: O modelo existe mas não há evidência de workflow automatizado de resposta (notificação DPO, quarentena de decisões afetadas, re-avaliação). | **Alto** | EU AI Act Art. 62, LGPD Art. 48 |

---

## 6.7. RAGAS Evaluation Framework

### 6.7.1 Status: Ausente

**Busca realizada**: Nenhuma referência a RAGAS (Retrieval Augmented Generation Assessment) encontrada no codebase.

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| RA01 | **Framework RAGAS não implementado**: Não há avaliação automatizada de qualidade das respostas do RAG pipeline (faithfulness, answer relevancy, context precision, context recall). O `rag_pipeline_service.py` existe mas sem métricas de qualidade. | **Alto** | EU AI Act Art. 15 (accuracy), Art. 9 (risk management) |
| RA02 | **Sem métricas de "groundedness"**: Não há verificação automatizada de que as avaliações de candidatos estão fundamentadas em evidências do CV (vs. alucinações do LLM). O `fact_checker.py` existe em `app/shared/compliance/` mas não há integração com RAGAS. | **Médio** | EU AI Act Art. 15 |

---

## 6.8. Golden Dataset para Regression Testing

### 6.8.1 Status: Implementado — Parcial

**Arquivo**: `tests/fixtures/golden_dataset.py`

**O que está implementado**:
- 60 candidatos sintéticos
- Distribuição equilibrada por 4 dimensões demográficas
- 3 tiers de performance (20 alta, 20 média, 20 baixa)
- Scores determinísticos independentes de demografia
- Funções helper: `get_group()`, `selection_rate()`, `adverse_impact_ratio()`
- Validação de integridade (7 testes dedicados)

**Gaps identificados**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| G01 | **Dataset pequeno (60 candidatos)**: Para validação estatística robusta, o dataset deveria ter pelo menos 200-300 candidatos para representar todas as combinações interseccionais de grupos. | **Médio** | Best practices estatísticas |
| G02 | **Sem variação de CV/texto**: O golden dataset contém apenas scores numéricos. Não inclui textos de CV para testar o pipeline completo (LLM → score → decisão). | **Alto** | EU AI Act Art. 10 |
| G03 | **Ausência de raça/etnia no dataset**: Conforme gap T02. | **Crítico** | NYC LL144, EEOC |
| G04 | **Sem cenários edge-case**: Não inclui candidatos com dados faltantes, campos nulos, ou combinações atípicas que podem expor falhas no pipeline. | **Médio** | Best practices |
| G05 | **Sem versionamento/changelog do dataset**: Alterações no golden dataset podem invalidar baselines anteriores. Não há mecanismo de versionamento. | **Baixo** | SOX (change management) |

---

## 6.9. Cobertura contra NYC LL144

### 6.9.1 Status: Parcial

| Requisito NYC LL144 | Status | Detalhe |
|---------------------|--------|---------|
| Bias audit anual por auditor independente | ❌ Ausente | Audit é interno e on-demand |
| Publicação dos resultados no site | ❌ Ausente | Sem mecanismo de publicação pública |
| Notificação aos candidatos sobre uso de AEDT | ⚠️ Parcial | Existem templates de comunicação mas sem evidência de notificação obrigatória pré-AEDT |
| Auditoria por raça/etnia e gênero | ⚠️ Parcial | Gênero coberto, raça/etnia ausente |
| Auditoria por interseccionalidade | ❌ Ausente | Análise apenas por dimensão isolada |
| Opção de acomodação alternativa | ❌ Ausente | Sem processo documentado para candidatos que recusam avaliação automatizada |
| Retenção de dados de audit por 4 anos | ⚠️ Parcial | Snapshots persistidos mas sem política de retenção de 4 anos |

---

## 6.10. Cobertura contra EU AI Act

### 6.10.1 Status: Parcial

| Requisito EU AI Act | Artigo | Status | Detalhe |
|---------------------|--------|--------|---------|
| Sistema de gestão de risco | Art. 9 | ✅ Implementado | FairnessGuard 3 camadas + drift detection |
| Governança de dados de treino | Art. 10 | ⚠️ Parcial | Golden dataset existe, mas sem governance de dados de treino do LLM |
| Documentação técnica | Art. 11 | ⚠️ Parcial | Docs existem mas sem formato padronizado EU AI Act |
| Registro de logs | Art. 12 | ✅ Implementado | AIInferenceLog, FairnessAuditLog, audit trail |
| Transparência | Art. 13 | ⚠️ Parcial | Explainability via feature_attributions, mas sem notificação explícita ao candidato |
| Supervisão humana | Art. 14 | ✅ Implementado | HumanReviewSamplingService (5% sampling + always_review para decisões críticas) |
| Precisão e robustez | Art. 15 | ⚠️ Parcial | Caching e calibração, mas sem RAGAS e sem métricas de accuracy formais |
| Obrigações do deployer | Art. 26 | ⚠️ Parcial | FairnessGuard + audit, mas sem processo de notificação a candidatos |
| Registro de incidentes graves | Art. 62 | ⚠️ Parcial | IncidentReport model existe, mas sem workflow de notificação automatizada |

---

## 6.11. Human Oversight (Supervisão Humana)

### 6.11.1 Status: Implementado — Bom

**Arquivo**: `app/services/human_review_sampling_service.py`

**O que está implementado**:
- Sampling determinístico de 5% de decisões de IA
- Decisões que SEMPRE requerem revisão: `finalize_hiring`, `mass_rejection`, `fairness_flagged`
- Idempotência via hash MD5 do decision_id
- Registro de revisão humana no banco

**Gaps**:

| # | Gap | Severidade | Legislação |
|---|-----|-----------|------------|
| H01 | **5% pode ser insuficiente para decisões de alto impacto**: O sampling rate é fixo. Para candidatos em fase final (shortlist), a taxa deveria ser 100%. | **Médio** | EU AI Act Art. 14, LGPD Art. 20 |
| H02 | **Sem métricas de concordância humano-IA**: Não há tracking da taxa de concordância entre decisão da IA e revisão humana. Essa métrica é essencial para calibração e para demonstrar confiabilidade do sistema. | **Alto** | EU AI Act Art. 9 |

---

## 6.12. Resumo de Gaps por Severidade

### Crítico (3)
1. **B01** — Dimensão raça/etnia ausente no Bias Audit
2. **B06** — Sem auditor externo/independente (NYC LL144)
3. **T02/G03** — Raça/etnia ausente no golden dataset

### Alto (10)
1. **B03** — Ausência de threshold mínimo de amostra
2. **B05** — Auditoria não é periódica/automatizada
3. **B07** — Sem publicação obrigatória dos resultados
4. **F03** — FairnessGuard ausente em endpoints de sourcing/busca
5. **T01** — Ausência de testes com dados reais
6. **D01** — Drift por dimensão demográfica não implementado
7. **D03** — Score drift queries sem filtro de company_id (multi-tenancy)
8. **I03** — Sem workflow de resposta a incidente de IA
9. **RA01** — Framework RAGAS não implementado
10. **G02** — Golden dataset sem textos de CV
11. **H02** — Sem métricas de concordância humano-IA
12. **R02** — Sem red teaming externo

### Médio (12)
1. **B02** — Faixas etárias inconsistentes
2. **B04** — Apenas 2 níveis de alert
3. **F01** — Camada semântica sem fallback robusto
4. **F02** — Log de query[:60] pode conter PII
5. **F04** — Sem rate limiting por recrutador
6. **F06** — Ausência de interseccionalidade
7. **T03** — Red teaming sem interseccionalidade
8. **T05** — Sem benchmark de falso-positivo quantificado
9. **D02** — Sem persistência de histórico de drift
10. **I01** — Sem tipo de incidente para hallucination
11. **I02** — Sem tipo para discriminatory decision
12. **G01** — Dataset pequeno
13. **G04** — Sem cenários edge-case
14. **H01** — 5% pode ser insuficiente
15. **RA02** — Sem métricas de groundedness
16. **R01** — Red teaming não periódico
17. **R03** — Sem prompt injection avançado

### Baixo (4)
1. **F05** — Cobertura de viés implícito limitada
2. **T04** — Sem testes adversarial com unicode
3. **D04** — Janela fixa de 7 dias
4. **G05** — Sem versionamento do golden dataset

---

## 6.13. Pontos Fortes Identificados

1. **Arquitetura de 3 camadas do FairnessGuard** é sólida (regex → viés implícito → semântica LLM)
2. **Ampla integração** do FairnessGuard em agentes e serviços (23+ pontos de uso)
3. **Golden dataset** com design estatístico correto (scores independentes de demografia)
4. **Red teaming formal** com 6 cenários cobrindo os vetores de ataque mais relevantes
5. **Model drift detection com 4 triggers** e alertas automáticos
6. **Human review sampling** determinístico com bypass para decisões críticas
7. **Audit logging** de checagens de fairness para compliance trail
8. **LGPD-safe**: Bias audit retorna apenas estatísticas agregadas, sem PII
9. **Modelos de observabilidade** com taxonomia de incidentes e frameworks de compliance
10. **Calibração com feedback de recrutador** via `CalibrationFeedback` para loop de melhoria

---

## 7. Gaps Críticos — Detalhamento

Os 18 gaps críticos que exigem atenção imediata:

### 7.1 Camada de IA e Agentes (1 Crítico)

| ID | Gap | Legislação | Impacto |
|----|-----|-----------|---------|
| G-M1 | **PII não mascarada nos prompts enviados ao LLM** — dados de candidatos (nome, CPF, email) podem ser enviados aos providers (Anthropic, OpenAI, Google) | LGPD Art. 6, EU AI Act | Dados pessoais transitam para terceiros sem necessidade. Risco de dados em training data do provider. Violação do princípio da necessidade (LGPD). |

### 7.2 LGPD e Proteção de Dados (8 Críticos)

| ID | Gap | Legislação | Impacto |
|----|-----|-----------|---------|
| PII-2 | **Dados sensíveis (Art. 11 LGPD) sem mascaramento em logs** — campos diversity_race_ethnicity, diversity_disability, diversity_lgbtqia logados em texto claro | LGPD Art. 11 | Dados sensíveis expostos em logs — categoria mais protegida pela LGPD. |
| CON-3 | **ConsentCheckerService não integrado nos endpoints de IA** — screening/scoring executam sem verificar consentimento | LGPD Art. 7, Art. 8 | Processamento de dados sem base legal verificada. |
| RET-2 | **Sem exclusão de arquivos associados (CVs, docs)** — LGPD cleanup exclui registros do banco mas CVs ficam no filesystem/S3 | LGPD Art. 16 | Dados pessoais permanecem após "exclusão". |
| ENC-1 | **CPF, data de nascimento e dados de diversidade armazenados sem criptografia** no PostgreSQL | LGPD Art. 46, BCB-498 | Dados sensíveis acessíveis a qualquer pessoa com acesso ao banco. |
| ENC-5 | **Fernet encryption key pode estar em .env ou variável de ambiente simples** sem rotação | LGPD Art. 46, ISO 27001 | Comprometimento da chave compromete todos os dados. |
| DAL-1 | **Data Access Logging não implementado nos endpoints** — modelo existe mas middleware/interceptor ausente | LGPD Art. 37, BCB-498 | Impossível rastrear quem acessou dados de candidatos. |
| DAL-2 | **Sem log automático de acesso a dados pessoais** | LGPD Art. 37 | Violação direta de requisito LGPD. |
| MT-1 | **X-Company-ID header sem validação de ownership** — pode ser forjado | LGPD, Multi-tenancy | Vazamento de dados entre empresas (cross-tenant). |

### 7.3 Auditoria e Observabilidade (6 Críticos)

| ID | Gap | Legislação | Impacto |
|----|-----|-----------|---------|
| I1 | **Sem imutabilidade em PostgreSQL para audit logs** — tabelas regulares, DBAs podem UPDATE/DELETE | SOX, BCB-498, SOC-2 | Trilha de auditoria adulterável — bloqueador para homologação bancária. |
| I2 | **S3 sem Object Lock/WORM** — registros de auditoria podem ser deletados | SOX, BCB-498 | Sem garantia de preservação — bloqueador para SOX. |
| R1 | **request_id não propagado para sistemas de auditoria** — quebra de rastreabilidade end-to-end | SOX, SOC-2, BCB-498 | Impossível correlacionar request HTTP com execução de agente. |
| S3 | **Sentry inicializado sem PII scrubbing** na primeira chamada em main.py | LGPD | PII pode vazar para Sentry (terceiro) antes do hook de scrubbing. |
| D1 | **Data access logging sem interceptação automática** — depende de chamada manual | LGPD Art. 37, BCB-498 | Auditores não conseguem verificar quem acessou dados. |
| AD3 | **Admin audit logs mutáveis** | SOX, BCB-498 | Ações administrativas podem ser apagadas. |

### 7.4 Fairness e DEI (3 Críticos)

| ID | Gap | Legislação | Impacto |
|----|-----|-----------|---------|
| B01 | **Raça/etnia ausente no Bias Audit** — dimensão protegida não auditada | NYC LL144, EEOC, CF Art. 5º | Adverse impact racial não detectado. |
| B06 | **Sem auditor independente externo** | NYC LL144 §20-871(b) | Non-compliance com NYC LL144. |
| T02/G03 | **Raça/etnia ausente no golden dataset** | NYC LL144, EEOC | Testes de fairness incompletos. |

---

## 8. Análise por Dimensão Regulatória

### 8.1 Adequação LGPD

| Requisito LGPD | Artigo | Status | Gap(s) |
|---------------|--------|--------|--------|
| Base legal para tratamento | Art. 7 | ⚠️ Parcial | CON-3 (consent checker não integrado em endpoints IA) |
| Consentimento granular | Art. 8 | ⚠️ Parcial | 7 tipos com SHA256 proof, porém 3 sistemas paralelos sem integração (CON-2) |
| Dados sensíveis | Art. 11 | ❌ Insuficiente | PII-2 (sem masking), ENC-1 (sem criptografia) |
| Direitos do titular | Art. 18 | ⚠️ Parcial | DSR-1 (sem execução automática) |
| Revisão de decisão automatizada | Art. 20 | ✅ Implementado | HumanReviewSamplingService |
| Minimização | Art. 6, III | ⚠️ Parcial | G-M1 (PII enviada ao LLM sem necessidade) |
| Segurança | Art. 46 | ⚠️ Parcial | ENC-1 (dados sem criptografia), ENC-5 (key rotation) |
| Registro de tratamento | Art. 37 | ❌ Insuficiente | DAL-1, DAL-2 (data access log não funcional) |
| DPO nomeado | Art. 41 | ✅ Implementado | Modelo e API existem |
| Notificação de incidente | Art. 48 | ⚠️ Parcial | BRE-1, BRE-2 (sem automação) |
| Retenção/exclusão | Art. 16 | ⚠️ Parcial | RET-2 (CVs não excluídos) |

**Score LGPD: 4/11 requisitos plenamente atendidos (36%)** — consentimento granular degradado pela existência de 3 sistemas paralelos sem integração (CON-2)

### 8.2 Adequação EU AI Act (Alto Risco)

| Requisito | Artigo | Status | Gap(s) |
|----------|--------|--------|--------|
| Sistema de gestão de risco | Art. 9 | ✅ | FairnessGuard + drift detection |
| Governança de dados | Art. 10 | ⚠️ | Golden dataset parcial, sem governance formal |
| Documentação técnica | Art. 11 | ⚠️ | Sem formato padronizado EU AI Act |
| Registro de logs | Art. 12 | ✅ | AIInferenceLog + audit trail |
| Transparência | Art. 13 | ❌ | Sem notificação ao candidato sobre uso de IA |
| Supervisão humana | Art. 14 | ⚠️ Parcial | HumanReviewSamplingService existe mas NÃO integrado no fluxo principal (G-C1) |
| Precisão e robustez | Art. 15 | ⚠️ | Sem RAGAS, sem métricas formais |
| Obrigações do deployer | Art. 26 | ⚠️ | Parcial |
| Práticas proibidas | Art. 5 | ✅ | Nenhuma prática proibida implementada |

**Score EU AI Act: 3/9 requisitos plenamente atendidos (33%)**

### 8.3 Adequação NYC Local Law 144

| Requisito | Status | Gap(s) |
|----------|--------|--------|
| Bias audit anual independente | ❌ | B06 |
| Publicação pública dos resultados | ❌ | B07 |
| Notificação prévia ao candidato | ⚠️ | Parcial |
| Auditoria por raça/etnia | ❌ | B01 |
| Auditoria por gênero | ✅ | Implementado |
| Opção de alternativa | ❌ | Ausente |

**Score NYC LL144: 1/6 requisitos plenamente atendidos (17%)**

### 8.4 Adequação para Homologação Bancária

| Requisito BCB-498 / CMN 4893 | Status | Gap(s) |
|------------------------------|--------|--------|
| Trilha de auditoria imutável | ❌ | I1, I2, AD3 |
| Rastreabilidade end-to-end | ❌ | R1, L1 |
| Log de acesso a dados pessoais | ❌ | D1, DAL-1 |
| Retenção mínima 5 anos | ✅ | 7 anos no S3 |
| Health monitoring | ⚠️ | H1, H2 |
| Alertas para falhas | ⚠️ | P1, A2 |
| Segregação de ambientes | ✅ | Dev/prod |
| Criptografia at-rest | ❌ | ENC-1 |
| Multi-tenancy seguro | ⚠️ | MT-1 |
| Gestão de incidentes | ⚠️ | I03 |

**Score Homologação Bancária: 2/10 requisitos plenamente atendidos (20%)**

---

## 9. Pontos Fortes — O Que Já Está Bem Feito

A plataforma tem fundamentos sólidos que colocam o WeDO à frente de muitos concorrentes:

1. **FairnessGuard de 3 camadas** (regex + léxico + LLM semântico) — arquitetura mais sofisticada que Gupy, InHire e Tezi
2. **100% dos agentes com EnhancedAgentMixin** — memória, autonomia e aprendizado uniformes
3. **Pipeline WSI com BARS methodology** — avaliação cientificamente fundamentada (Dreyfus, Bloom, Big Five)
4. **AutonomyEngine com guardrails dinâmicos** por empresa — inovador no mercado brasileiro
5. **CascadedRouter de 6 tiers** — eficiência de custo sem sacrificar qualidade
6. **Model drift detection com 4 triggers** e alertas automáticos
7. **Circuit breakers para 7 serviços** com métricas Prometheus
8. **HumanReviewSamplingService** — 5% sampling + always-review para decisões críticas
9. **AuditCallback automático** — agentes auditados sem saber
10. **LLM fallback chain** (Claude → Gemini → OpenAI) com circuit breakers
11. **Consent management granular** com 7 tipos e prova SHA256
12. **LGPD cleanup service** com retenção configurável por tipo
13. **Taxonomia de incidentes de IA** com 7 tipos e 4 severidades
14. **Anti-bajulação** nos prompts — IA que discorda construtivamente
15. **Dual-path execution** — LangGraph nativo + ReAct custom para migração incremental

---

## 10. Roadmap de Remediação Priorizado

### Fase 1 — Bloqueadores Críticos (0-30 dias)

Sem estes itens, a plataforma tem risco jurídico imediato.

| # | Ação | Gaps | Legislação | Esforço |
|---|------|------|-----------|---------|
| 1 | **PII masking nos prompts enviados ao LLM** — criar `PromptPIIFilter` que remove CPF, email, telefone, nome dos dados de candidato antes de construir prompts | G-M1, PII-6 | LGPD Art. 6 | Médio |
| 2 | **Criptografia at-rest para dados sensíveis** — implementar Fernet encryption para CPF, data de nascimento, dados de diversidade no PostgreSQL | ENC-1, ENC-5 | LGPD Art. 46, BCB-498 | Alto |
| 3 | **Validação de ownership do X-Company-ID** — verificar que usuário autenticado pertence à empresa informada no header | MT-1 | LGPD, Multi-tenancy | Baixo |
| 4 | **Integrar ConsentCheckerService nos endpoints de IA** — wire antes de scoring/screening/ranking | CON-3 | LGPD Art. 7 | Médio |
| 5 | **Corrigir inicialização do Sentry** — remover `sentry_sdk.init()` direto no main.py, usar apenas `init_sentry()` com PII scrubbing | S3 | LGPD | Baixo |
| 6 | **Mascaramento de dados sensíveis em logs** — adicionar patterns para diversity fields no PIIMaskingFilter | PII-2 | LGPD Art. 11 | Baixo |

### Fase 2 — Habilitadores de Homologação Bancária (30-90 dias)

Sem estes itens, homologação bancária será negada.

| # | Ação | Gaps | Legislação | Esforço |
|---|------|------|-----------|---------|
| 7 | **Imutabilidade da trilha de auditoria** — S3 Object Lock (Compliance Mode) + triggers PostgreSQL contra UPDATE/DELETE em tabelas de audit | I1, I2, AD3 | SOX, BCB-498 | Alto |
| 8 | **Hash de integridade SHA-256** em cada registro de auditoria | A3 | SOX, BCB-498 | Médio |
| 9 | **Propagar request_id end-to-end** — do middleware HTTP até AuditWriter, AuditService, AIInferenceLog | R1, L1 | SOC-2, BCB-498 | Médio |
| 10 | **Data access logging automático** — middleware/decorator que loga automaticamente acessos a endpoints de dados pessoais | D1, DAL-1, DAL-2 | LGPD Art. 37, BCB-498 | Alto |
| 11 | **Health check do subsistema de auditoria** — verificar S3 connectivity, write test, Sentry status | H1, H2 | SOC-2, BCB-498 | Médio |
| 12 | **Retry com backoff para persistência de auditoria** — dead-letter queue quando PG/S3 estiverem indisponíveis | A2, A6 | SOC-2 | Médio |
| 13 | **Exclusão de arquivos associados na LGPD cleanup** — CVs, documentos no filesystem/S3 | RET-2 | LGPD Art. 16 | Médio |

### Fase 3 — Compliance EU AI Act e Fairness (90-180 dias)

Para operar na UE e mercado americano.

| # | Ação | Gaps | Legislação | Esforço |
|---|------|------|-----------|---------|
| 14 | **Blind review pré-LLM** — criar `CandidateAnonymizer` que remove nome, idade, foto, gênero antes de prompts de triagem | G-M2, G-M3 | EU AI Act, LGPD | Alto |
| 15 | **Adicionar raça/etnia ao Bias Audit** — nova dimensão na Four-Fifths Rule | B01, T02, G03 | NYC LL144, EEOC | Médio |
| 16 | **Integrar Camada 3 (semântica) no workflow** — chamar `check_semantic()` quando Camadas 1+2 retornarem soft_warnings | G-F1 | EU AI Act | Baixo |
| 17 | **Integrar HumanReviewSamplingService no fluxo principal** — decisões de triagem/ranking/rejeição passam por sampling | G-C1 | EU AI Act Art. 14 | Médio |
| 18 | **FairnessGuard na saída do ReAct loop** — verificar resposta gerada antes de retornar ao usuário | G-RL1 | EU AI Act | Baixo |
| 19 | **Notificação de uso de IA ao candidato** — informar explicitamente que IA é usada na avaliação, com opt-out | Art. 13, 52 EU AI Act | EU AI Act | Médio |
| 20 | **Implementar RAGAS evaluation framework** — métricas de qualidade para o RAG pipeline | RA01 | EU AI Act Art. 15 | Alto |
| 21 | **Métricas de concordância humano-IA** — tracking de override rate | H02 | EU AI Act Art. 9 | Médio |
| 22 | **Drift detection por dimensão demográfica** | D01 | EU AI Act, EEOC | Médio |
| 23 | **FairnessGuard em endpoints de sourcing/busca** — queries de busca discriminatórias podem passar sem checagem | F03 | LGPD, EU AI Act | Baixo |
| 24 | **Corrigir filtro company_id no drift detection** — score_drift e approval_drift queries quebram isolamento multi-tenant | D03 | LGPD, Multi-tenancy | Baixo |
| 25 | **Unificar sistemas de consentimento** — consolidar ConsentRecord, ConsentVersion+ConsentEvent, LGPDConsent em sistema único | CON-2 | LGPD Art. 8 | Alto |
| 26 | **NYC LL144 — obrigações operacionais**: notificação 10 dias antes do uso de AEDT, processo de acomodação alternativa, retenção de audit por 4 anos | NYC LL144 | NYC LL144 | Médio |

### Fase 4 — Certificações e Maturidade (6-12 meses)

Para competir com Eightfold e HireVue.

| # | Ação | Gaps | Referência | Esforço |
|---|------|------|-----------|---------|
| 27 | **Preparar SOC-2 Type II** — implementar controles restantes, contratar auditor | Múltiplos | SOC-2 | Muito Alto |
| 28 | **Contratar auditor independente para bias audit** — ex: BABL AI, ORCAA | B06 | NYC LL144 | Médio |
| 29 | **Preparar ISO 42001** — AI Management System certification | Benchmark | ISO 42001 | Muito Alto |
| 30 | **Publicação pública de resultados de bias audit** | B07 | NYC LL144 | Baixo |
| 31 | **Unificar modelos de audit log** — consolidar AuditLog + AdminAuditLog + SOXAuditLog | AD1, E1 | SOX, SOC-2 | Alto |
| 32 | **Implementar OpenTelemetry** para distributed tracing | R3 | SOC-2 | Alto |
| 33 | **FRIA (Fundamental Rights Impact Assessment)** — documento formal para EU AI Act | Art. 27 EU AI Act | EU AI Act | Médio |
| 34 | **Golden dataset expandido** — 200+ candidatos, textos de CV, raça/etnia, edge cases | G01-G04 | Best practices | Médio |

---

## 11. Matriz de Risco

### 11.1 Risco por Jurisdição

| Risco | Probabilidade | Impacto | Nível | Mitigação |
|-------|:---:|:---:|:---:|-----------|
| Sanção ANPD por dados sensíveis sem proteção | Alta | Alto | **Crítico** | Fase 1 (itens 1, 2, 6) |
| Vazamento cross-tenant (MT-1) | Média | Muito Alto | **Crítico** | Fase 1 (item 3) |
| Rejeição em homologação bancária | Alta | Alto | **Crítico** | Fase 2 (itens 7-12) |
| Non-compliance EU AI Act (ago/2026) | Média | Alto | **Alto** | Fase 3 (itens 14-22) |
| Non-compliance NYC LL144 | Média | Médio | **Alto** | Fase 3 (itens 15, 19) + Fase 4 (24, 26) |
| PL 2338/2023 quando sancionado | Média | Alto | **Alto** | Fases 1-3 cobrem maioria dos requisitos |
| Perda de deal enterprise sem SOC-2 | Alta | Alto | **Alto** | Fase 4 (item 23) |
| Incidente de viés discriminatório | Baixa | Muito Alto | **Alto** | Fase 3 (itens 15, 16, 22) |
| Dados de candidato em training data de LLM | Média | Alto | **Alto** | Fase 1 (item 1) |

### 11.2 Risco de Não-Ação

Se nenhum gap for corrigido:
- **LGPD:** Multa de até 2% do faturamento (teto R$50M/infração)
- **EU AI Act:** Multa de até 3% do faturamento global
- **NYC LL144:** $500-$1.500/dia de violação
- **BCB-498:** Inabilitação para operar com bancos regulados
- **Reputacional:** Dano irreversível se incidente de viés for publicizado

---

## 12. Recomendações Estratégicas

### 12.1 Para o Curto Prazo (30 dias)
1. Executar Fase 1 do roadmap — são os bloqueadores jurídicos mais urgentes
2. Documentar formalmente a posição de DPO e canal de comunicação ANPD
3. Criar processo de notificação de uso de IA ao candidato (mesmo antes do EU AI Act)

### 12.2 Para o Médio Prazo (90 dias)
4. Executar Fase 2 — preparar para homologação bancária
5. Iniciar processo de contratação de auditor independente para bias audit
6. Documentar FRIA (Fundamental Rights Impact Assessment) para EU AI Act

### 12.3 Para o Longo Prazo (6-12 meses)
7. Iniciar processo de certificação SOC-2 Type II
8. Avaliar certificação ISO 42001 (diferencial competitivo forte)
9. Implementar RAGAS para monitoramento contínuo de qualidade do LLM
10. Expandir FairnessGuard para interseccionalidade

### 12.4 Diferencial Competitivo
A arquitetura atual da plataforma é **sólida e bem pensada**. Com as correções das Fases 1-3, o WeDO estará em posição competitiva forte — especialmente no mercado brasileiro onde poucos concorrentes têm:
- FairnessGuard de 3 camadas
- Model drift detection
- BARS methodology
- AutonomyEngine com guardrails
- LLM fallback chain com circuit breakers

A oportunidade é transformar a "dívida de compliance" em vantagem competitiva, implementando os gaps antes que a regulação os exija — e usar isso como argumento de vendas para bancos e enterprises.

---

## Anexos

### Anexo A — Arquivos de Referência por Área

| Área | Arquivos-Chave |
|------|---------------|
| IA/Agentes | `app/orchestrator/orchestrator.py`, `app/domains/base.py`, `app/domains/workflow.py`, `app/shared/agents/react_loop.py` |
| Compliance | `app/shared/compliance/fairness_guard.py`, `app/shared/pii_masking.py`, `app/services/bias_audit_service.py` |
| Auditoria | `libs/audit/lia_audit/audit_writer.py`, `app/core/logging_middleware.py`, `libs/models/lia_models/observability.py` |
| LGPD | `app/api/v1/lgpd_compliance.py`, `app/services/lgpd_cleanup_service.py`, `app/api/v1/consent_management.py` |
| Screening | `app/domains/cv_screening/services/rubric_evaluation_service.py`, `app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| Resiliência | `app/shared/resilience/circuit_breaker.py` |

### Anexo B — Legislação de Referência

| Legislação | Link |
|-----------|------|
| PL 2338/2023 (Senado) | https://www25.senado.leg.br/web/atividade/materias/-/materia/157233 |
| PL 2338/2023 (Câmara) | https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2487262 |
| EU AI Act (texto oficial) | Regulation (EU) 2024/1689 |
| NYC Local Law 144 | Int. No. 1894-A |
| LGPD | Lei 13.709/2018 |
| BCB-498 | Resolução BCB nº 498/2025 |
| CMN 4893 | Resolução CMN nº 4893/2021 |
| ISO 42001 | ISO/IEC 42001:2023 |

### Anexo C — Plataformas de Referência

| Plataforma | País | Diferencial | Referência |
|-----------|------|------------|-----------|
| Eightfold AI | EUA | ISO 42001, FedRAMP, bias audit por BABL AI | eightfold.ai/trust |
| Gupy | Brasil | SOC-2, líder de mercado BR, +4.000 clientes | gupy.io |
| HireVue | EUA | IO Psychology framework, descontinuou facial analysis | hirevue.com/why-hirevue/ai-ethics |
| Paradox | EUA | NYC LL144 compliance, automação conversacional | paradox.ai |
| Greenhouse | EUA | SOC-2, structured hiring framework | greenhouse.io/trust |
| Findem | EUA | 750M+ talent database, diversity hiring | findem.ai |
| InHire | Brasil | Crescimento 300% em 2024, spin-off Intera | inhire.com.br |
| Tezi | Brasil | IA para recrutamento BR | tezi.io |
| Popp AI | Brasil | IA conversacional para recrutamento | popp.ai |
