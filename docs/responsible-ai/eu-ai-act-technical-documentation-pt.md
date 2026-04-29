# Documentação Técnica EU AI Act Art. 11 — Plataforma LIA WeDOTalent

> **Versão:** 1.0
> **Data:** 2026-04-23
> **Provider:** WeDOTalent
> **Sistema:** LIA (Learning Intelligence Assistant) — plataforma de recrutamento com IA
> **Classificação:** Sistema de IA de Alto Risco — EU AI Act Anexo III, categoria 4 (recrutamento)
> **Status:** Pronto para revisão jurídica externa antes de publicação pública e registro no EU AI Act database (quando ativo)

---

## Sumário

1. Descrição Geral do Sistema
2. Descrição dos Componentes de IA
3. Dados de Treinamento, Validação e Teste
4. Avaliação Pré-Deploy (riscos e mitigações)
5. Monitoramento Pós-Deploy
6. Métricas Consolidadas
7. Supervisão Humana (Art. 14)
8. Accuracy, Robustez, Cibersegurança (Art. 15)
9. Direitos do Titular (LGPD + EU AI Act Art. 86)
10. Benchmark de Mercado e Comparação com Concorrentes
11. Roadmap Público de Publicações e Implementações
12. Governança e Responsabilidades
13. Declaração de Conformidade
Apêndices

---

## 1. Descrição Geral do Sistema

### 1.1 Propósito e contexto de uso

A LIA é uma assistente de recrutamento baseada em modelos de linguagem de grande porte (LLMs), operada pela WeDOTalent e utilizada por clientes enterprise para apoiar processos de recrutamento e seleção. Sua função é assistir recrutadores humanos na triagem de currículos, avaliação comportamental (WSI — Workplace Science Index), busca ativa de candidatos, comunicação com candidatos, e gestão de pipeline.

A LIA **não toma decisões autônomas de contratação** — toda decisão final permanece com o recrutador humano. O sistema aplica Supervisão Humana (HITL — Human-in-the-Loop) em toda ação de alto impacto, conforme EU AI Act Art. 14.

### 1.2 Pessoas/entidades afetadas

- **Usuários diretos (operadores):** recrutadores e gestores de RH do cliente
- **Afetados indiretamente (sujeitos da decisão):** candidatos a vagas de emprego

### 1.3 Categoria de risco

Enquadramento legal: **EU AI Act Anexo III, categoria 4** (sistemas de IA usados em recrutamento ou seleção, incluindo avaliação de candidatos, filtragem de candidaturas, decisões de promoção).

A partir de 02/08/2026, esta classificação passa a ser obrigatória para sistemas operando na UE ou processando candidatos europeus.

### 1.4 Provider e Deployer

- **Provider:** WeDOTalent — desenvolve e mantém a plataforma LIA
- **Deployer:** cada cliente enterprise — configura políticas, critérios e uso operacional

---

## 2. Descrição dos Componentes de IA

### 2.1 Modelos LLM utilizados

- **Modelo de raciocínio principal:** `claude-sonnet-4-5` (Anthropic)
- **Modelo de classificação semântica (FairnessGuard Layer 3):** `claude-haiku-4-5-20251001` (Anthropic)
- **Modelo de profundidade consultiva (opcional, por agente):** `claude-opus-4-7` (Anthropic, 1M context)

Todos os modelos são acessados via API Anthropic, sem fine-tuning proprietário. O comportamento especializado é obtido via camada de prompt injection (§2.3).

### 2.2 Arquitetura LIA (resumo)

Arquitetura de microagentes orquestrada pelo `MainOrchestrator` em 4 fases. Detalhes completos em `docs/reconstruction-guides/INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`.

- **15 agentes ativos** com AgentType enum
- **ReAct loop** (Reason-Act-Observe) em `LangGraphReActBase`
- **CascadedRouter** em 8 tiers para roteamento inteligente
- **Multi-tenant** com isolamento por `company_id` (validado via JWT, enforced por `TenantGuard`)

### 2.3 Camada de prompt injection

Documentada em detalhe em `docs/reconstruction-guides/LIA_PERSONA_RECONSTRUCTION_GUIDE.md` Parte 9.

Ordem real de injeção no `SystemPromptBuilder.build()` (9 passos):
1. `_IDENTITY_OVERRIDE` (hardcoded — "REGRA ZERO: SEU NOME É LIA")
2. `lia_persona.yaml` (292 linhas — identidade + princípios éticos)
3. `_PLATFORM_KNOWLEDGE` (conhecimento declarativo da plataforma)
4. `agent_prompts.yaml`[agent_type] (especialização por tipo — 11 variantes)
5. Contexto dinâmico (tenant + recruiter + user + page + summary + state)
6. Regras anti-repetição (se conversa em andamento)
7. Roteamento (intent + entities)
8. REACT_INSTRUCTIONS (para todos os agentes exceto orchestrator)
9. Instruções adicionais injetadas pelo caller

Em paralelo, outras classes injetam:
- `ComplianceDomainPrompt` → `compliance_block.yaml` (4 variantes contextuais)
- `GuardrailsDomainPrompt` → `guardrails_block.yaml` (7 seções)
- `CustomAgentRuntime` → `intelligence_floor.yaml` (piso de qualidade em custom agents)

### 2.4 Oito camadas de defesa compliance

Documentação completa em `docs/reconstruction-guides/COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.2.

| Camada | Mecanismo | Tipo | Blocking |
|--------|-----------|------|----------|
| C1 | `FairnessGuard.check()` — regex 19 categorias | Computacional | ✅ |
| C2 | `check_implicit_bias()` — 43 termos PT/EN | Computacional | Soft warning |
| C3 | `check_semantic()` — LLM Haiku (FAIRNESS_LAYER3_ENABLED=true em prod desde 2026-04-23) | Inferencial | Condicional |
| C4 | `compliance_block.yaml` — prompt guidance (4 variantes) | Inferencial | Diretivo |
| C5 | `guardrails_block.yaml` — behavioral limits | Inferencial | Diretivo |
| C6 | `protected_attributes.yaml` — 14 atributos SSOT | Computacional | ✅ |
| C7 | `fairness_post_check.yaml` — output monitoring | Computacional | ✅ |
| C8 | `audit_service.log_decision` — rastreabilidade | Computacional | Observação |

---

## 3. Dados de Treinamento, Validação e Teste

### 3.1 Modelos de terceiros

A LIA **não treina modelos próprios**. Utiliza modelos LLM via API da Anthropic. Governança de dados de treinamento dos modelos base é de responsabilidade do provider terceiro:

- **Anthropic Claude (claude-sonnet-4-5 + claude-haiku-4-5 + claude-opus-4-7):** model cards públicos em https://www.anthropic.com/claude

### 3.2 Fine-tuning interno

**Nenhum.** O sistema opera 100% prompt-based. Comportamento especializado é obtido via prompts declarativos em YAML (§2.3), não via ajuste de pesos de modelo.

### 3.3 Dados operacionais

- `AuditLog` + `fairness_audit_log` — tabelas internas anonimizadas (somente IDs, sem PII)
- Registros de decisão mantêm `criteria_used`, `score_breakdown`, `subject_id`, `timestamp`
- Retenção conforme política LGPD do cliente-deployer (configurável)

### 3.4 Proveniência e governança

- Infraestrutura: Replit (produção), PostgreSQL (dados operacionais), Redis (cache)
- Multi-tenant: `company_id` injetado via JWT, validado por `TenantGuard` — um cliente nunca acessa dados de outro
- Anonimização para auditoria: `audit_service` não registra PII (sem nome, sem foto, sem CPF)

---

## 4. Avaliação Pré-Deploy (riscos e mitigações)

| Risco | Mitigação |
|-------|-----------|
| **Discriminação por atributos protegidos** | `FairnessGuard` L1+L2+L3 + `protected_attributes.yaml` (14 atributos SSOT) + `compliance_block.yaml` (diretivo) |
| **PII leak em logs ou respostas** | `pii_masking.py` + `guardrails_block.yaml` seção `data_safety` + `ADR-006` (no PII em logs) |
| **Prompt injection / manipulação** | `PROMPT_INJECTION_PATTERNS` (12 regex) em `interaction_patterns.py` + `DEFENSIVE_BLOCK` + `SecurityPatterns` |
| **Decisão automatizada sem supervisão humana** | HITL em `cv_screening.yaml`, `wsi_evaluation.yaml`, `pipeline_transition.yaml` + `guardrails_block.yaml` seção `autonomy` (3 níveis) |
| **Multi-tenant data leak (IDOR)** | `TenantGuard` — `company_id` sempre do JWT, nunca do payload |
| **Sycophancy (IA concorda com pedidos inadequados)** | `anti_sycophancy_block.py` (3 variantes) — regra ativa em todo agente operacional |
| **Contornamento de compliance via "preconceito positivo"** | `hiring_policy.yaml` seção `counter_argumentation` + citação de Lei 9.029/95 |
| **Proxy de viés em cultural fit** | `culture_analysis.yaml` atualizado 2026-04-23 com bloco `<compliance_hr>` |

---

## 5. Monitoramento Pós-Deploy

### 5.1 `fairness_post_check.yaml`

Monitoramento de outputs em 7 domínios de decisão: `cv_screening`, `wsi_evaluation`, `pipeline_transition`, `hiring_policy`, `sourcing`, `autonomous`, `talent_pool`. Monitora 6 campos de score e 5 campos de ranking.

### 5.2 Endpoints de explicabilidade

| Endpoint | Auth | Audiência | Compliance |
|----------|------|-----------|------------|
| `GET /api/v1/decisions/candidates/{candidate_id}/explain` | JWT recrutador (`get_current_user`) | Operador | LGPD Art. 20 (revisão interna) |
| `GET /api/v1/candidate/decisions/explain` | JWT candidato (`candidate_token`) | **Candidato** | **EU AI Act Art. 86 + LGPD Art. 20** (direto-ao-candidato) |

O endpoint direto-ao-candidato foi implementado em 2026-04-23 (§11.1 deste documento) e sanitiza o output para não expor `wsi_score`, `lia_score`, `confidence`, `weights` ou flags de fairness internas.

### 5.3 Audit trail

- Tabela `fairness_audit_log` (Alembic migration 015) — `company_id`, `subject_id`, `decision_type`, `criteria_used`, `score_breakdown`, `timestamp`
- `candidate_portal_audit_logs` — registra acessos do candidato ao portal (tools_called, fairness_triggered)

### 5.4 Dashboards internos

- Agent Quality Dashboard (`app/api/v1/agent_quality_dashboard.py`)
- Fairness Reports (`app/api/v1/fairness_reports.py`)

---

## 6. Métricas Consolidadas

### 6.1 Atributos protegidos cobertos — 14

Fonte: `app/config/protected_attributes.yaml` (versão 6):

1. Idade
2. Gênero
3. Raça / Etnia
4. Cor
5. Religião
6. Orientação sexual
7. Estado civil
8. Situação familiar / maternidade / paternidade / gravidez
9. Deficiência
10. Aparência física / foto
11. Nacionalidade / sotaque
12. Antecedentes criminais (sem base legal específica)
13. Saúde / doença
14. Filiação sindical / origem geográfica como proxy

### 6.2 FairnessGuard — cobertura técnica

- **Layer 1 (regex):** 19 categorias compiladas em tempo de inicialização (13 PT-BR + 6 EN) — `_PATTERNS_VERSION = 8`
- **Layer 2 (viés implícito):** 43 termos PT-BR + termos EN em `IMPLICIT_BIAS_TERMS`
- **Layer 3 (semântico LLM):** `claude-haiku-4-5-20251001`, ativado para `HIGH_IMPACT_ACTIONS`, cache Redis 1h, `FAIRNESS_LAYER3_ENABLED=true` em produção desde 2026-04-23

### 6.3 Métricas de disparate impact por feature

**Metodologia:** four-fifths rule (NYC Local Law 144) — DI ratio ≥ 0.80 por grupo protegido, calculado como:

```
DI ratio = (taxa de seleção grupo protegido) / (taxa de seleção grupo de referência)
```

**Status atual (2026-04-23):** infraestrutura parcial (`fairness_audit_log` coletando dados desde Alembic migration 015), **aguardando bias audit independente Q3/2026** (ver §11).

| Feature | Grupo monitorado | DI ratio | Status |
|---------|------------------|---------|--------|
| CV Screening | Gênero × Raça/Etnia | Pendente | Aguarda auditoria Q3/2026 |
| WSI Evaluation | Gênero × Idade | Pendente | Aguarda auditoria Q3/2026 |
| Pipeline Transition | Todos os 14 atributos | Pendente | Aguarda auditoria Q3/2026 |
| Ranking / Shortlist | Gênero × Raça/Etnia × Deficiência | Pendente | Aguarda auditoria Q3/2026 |
| Sourcing Boolean | Queries com proxies | Em coleta via `fairness_audit_log` | Agregação prévia à auditoria |

### 6.4 Frequência de atualização

- Bias audit independente: **anual** (próximo ciclo Q3/2026)
- Relatório interno de métricas: **trimestral** pós-auditoria
- Atualização deste documento: **anual + triggered** por mudança arquitetural significativa

---

## 7. Supervisão Humana (Art. 14)

### 7.1 HITL declarativo por domínio

| Domain YAML | HITL | Explicabilidade | Score compliance |
|-------------|------|-----------------|------------------|
| `hiring_policy.yaml` | ✅ `escalation` | ✅ `reasoning_rules` | 5/5 |
| `cv_screening.yaml` | ✅ confirmação dupla para rejeição em massa | ✅ reasoning auditável | 3/5 |
| `wsi_evaluation.yaml` | ✅ FairnessGuard mandated | Parcial | 3/5 |
| `pipeline_transition.yaml` | ✅ ações irreversíveis confirmadas | ✅ `communication_transparency` | 3/5 |
| `autonomous.yaml` (fix 2026-04-23) | ✅ `hitl_escalation` | ✅ audit trail declarativo | ▲ melhorado |
| `culture_analysis.yaml` (fix 2026-04-23) | ✅ `<compliance_hr>` block | ▲ melhorado | ▲ melhorado |
| `orchestrator.yaml` (fix 2026-04-23) | ✅ prologue compliance | ▲ melhorado | ▲ melhorado |

### 7.2 `guardrails_block.yaml` — cenários de escalação

Sete cenários mandatórios de escalação para humano:

1. Discriminação detectada
2. Data subject request (LGPD)
3. Padrão de rejeições potencialmente discriminatório
4. Risk score > 0.8
5. Tentativa de manipulação/jailbreak
6. Conflito entre instrução do recrutador e regra de fairness
7. Pedido do candidato para contestar decisão (Art. 86)

### 7.3 Direito de contestação (EU AI Act Art. 86)

Implementado em 2026-04-23:
- **Endpoint:** `GET /api/v1/candidate/decisions/explain`
- **Agente:** `CandidateSelfServiceAgent` com tool `explain_candidate_decision`
- **Política:** `compliance_block.yaml` seção `right_to_contest` (variantes `decision` e `communication`)
- **Prazo recomendado:** 30 dias para contestação

---

## 8. Accuracy, Robustez, Cibersegurança (Art. 15)

### 8.1 Modelos ancorados

Versões anchorage explícita para reprodutibilidade:
- `claude-sonnet-4-5` (stable release)
- `claude-haiku-4-5-20251001` (version-pinned para FairnessGuard L3)
- `claude-opus-4-7` (1M context, uso consultivo)

### 8.2 Rate limits

- `POST /api/v1/candidate/chat`: 10/hora, 30/dia por `candidate_id` (Redis)
- `GET /api/v1/candidate/decisions/explain`: mesmo rate limit
- APIs internas: rate limit por API key (documentado em `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`)

### 8.3 JWT token scoping (anti-IDOR)

- `candidate_token`: contém `candidate_id`, `vacancy_id`, `company_id` — **sempre derivados do token**, nunca aceitos do input
- `recruiter_token`: contém `user_id`, `company_id`, `permissions` — validado pelo `TenantGuard`

### 8.4 Circuit breakers e fallbacks

Documentado em `RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md`:
- `CircuitBreaker` em 20 circuitos críticos (LLM providers, ATS integrations, Redis)
- 3 estados: Closed → Open → Half-Open
- Fallback lenient para FairnessGuard L3 (`is_blocked=False, confidence=0.5`) quando API do provider falha, com `soft_warnings` para audit

---

## 9. Direitos do Titular (LGPD + EU AI Act Art. 86)

### 9.1 Explicabilidade

- **Ao operador (recrutador):** `decision_explanation.py` — retorna `reasoning`, `factors`, `confidence`, `fairness_check`, `calibration_weights_used`
- **Ao candidato:** `candidate_portal_explanation.py` — retorna **apenas** `criteria_evaluated`, `criteria_ignored`, `fairness_check` agregado, `transparency_note`, `art_86_notice`; **nunca** scoring bruto

### 9.2 Revisão humana

Qualquer decisão pode ser escalada para revisão humana via:
- Canal formal de compliance do deployer (configurável por `company_id`)
- Solicitação do candidato via portal (`/api/v1/candidate/chat`)
- Escalação automática quando `risk_score > 0.8` (`hiring_policy.yaml`)

### 9.3 Contestação (prazo 30 dias)

Direito documentado em `compliance_block.yaml` seção `right_to_contest` e exposto ao candidato via `art_86_notice` em toda resposta de explicação.

### 9.4 Acesso e exclusão (data_subject_request)

Endpoint herdado para LGPD Arts. 18 e 15 — acesso e exclusão de dados. Fluxo: candidato solicita → compliance do deployer valida → sistema exclui com tombstone auditável.

---

## 10. Benchmark de Mercado e Comparação com Concorrentes

Esta seção consolida o benchmark realizado em 2026-04-23 contra os 4 principais players e 5 frameworks regulatórios, originalmente documentado em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.7.

### 10.1 Requisitos regulatórios — status cruzado

| Requisito | Base legal | O que exige | Status WeDOTalent | Gap |
|-----------|-----------|-------------|-------------------|-----|
| Classificação como IA de alto risco | EU AI Act Anexo III cat. 4 | Registro obrigatório após 02/08/2026 | Enquadramento inevitável | Formalizar registro quando database ativo |
| Governança de dados de treinamento | EU AI Act Art. 10 | Documentar proveniência de dados | 100% prompt-based; sem fine-tuning | Documentar (este doc §3) |
| Transparência ao operador (AI Fact Sheet) | EU AI Act Art. 13 | Formato exigido | 5 Fact Sheets publicadas 2026-04-23 (§11) | — |
| Supervisão humana (design) | EU AI Act Art. 14 | Override acionável na UI | `guardrails_block.yaml` + HITL por domínio | Validar acionabilidade na UI |
| Acurácia, robustez, segurança | EU AI Act Art. 15 | Métricas por grupo demográfico | Infraestrutura (`fairness_audit_log`); DI ratios pendentes | Bias audit Q3/2026 |
| Direito à explicação ao candidato | EU AI Act Art. 86 | Endpoint direto-ao-candidato | **Implementado 2026-04-23** (`/api/v1/candidate/decisions/explain`) | — |
| Direito de revisão automatizada | LGPD Art. 20 | Canal de revisão | Implementado via portal + email compliance | — |
| Identificação e mitigação de viés | NIST AI RMF MEASURE 2.11 | Testes documentados | FairnessGuard L1+L2+L3 | Bias audit independente (P1.2) |
| Escalação de incidentes | NIST AI RMF MANAGE 4.1 | SLA formal | `guardrails_block.yaml` + 7 cenários | Formalizar SLA (P2) |
| Sistema de gestão de IA | ISO/IEC 42001:2023 | AIMS certificado | — | Certificação 2027 |
| Disparate impact testing | NYC Local Law 144 | DI ratio ≥ 0.80 por grupo | Em coleta | Auditoria Q3/2026 |

### 10.2 Benchmark competitivo — 9 dimensões × 5 players

Fontes verificadas em §10.5.

| Dimensão | WeDOTalent (LIA) | Workday / HiredScore | HiPeople | Eightfold AI | LinkedIn |
|----------|------------------|---------------------|----------|--------------|----------|
| **Atributos protegidos declarados** | **14** | 4+ (publicados parcialmente) | 4+ (proxies) | 4+ (+ interseções) | 4+ |
| **Lista pública de atributos** | Pós §11 (em curso) | Parcial via ML Fact Sheets | Parcial | Sim (bias audit anual) | Sim (LiFT open-source) |
| **Explicabilidade ao candidato** | ✅ **desde 2026-04-23** (endpoint novo) | Apenas ao deployer | Apenas ao recrutador | Sim (via portal) | Declarado (sem mecanismo público) |
| **HITL no design** | ✅ 3 níveis `autonomy` | ✅ "human review of any outputs" | ✅ Recrutador como ponto final | ✅ Candidate masking + humano | ✅ Revisão humana |
| **Direito de contestação direto** | ✅ **implementado 2026-04-23** | Não encontrado publicamente | Não encontrado publicamente | Não encontrado publicamente | Não encontrado publicamente |
| **Audit trail** | ✅ Alembic 015 + fairness_audit_log | ✅ ML Fact Sheets + ISO 42001 | ✅ Warden AI dashboard público | ✅ Bias audit anual + ISO 42001 | LiFT open-source |
| **Testes de fairness documentados** | ✅ L1+L2+L3 interno; audit externo Q3/2026 | ✅ Coalfire (NIST) + Schellman (ISO) | ✅ NYC LL144 | ✅ BABL AI anual (menor ratio 0.880) | LinkedIn Fairness Toolkit |
| **Certificações externas** | — (roadmap 2027) | ISO 42001 + NIST AI RMF | NYC LL144; EU AI Act em andamento | ISO 42001 + NYC LL144 | — (open-source como transparência) |
| **Score consolidado /10** | **7/10** ↑ | **8/10** | **7/10** | **9/10** | **7/10** |

> **Nota:** o score do WeDOTalent subiu de 6/10 (snapshot 2026-04-22, pré-implementações) para 7/10 após os fixes aplicados em 2026-04-23 (endpoint Art. 86, Fact Sheets, FairnessGuard L3 ativado).

### 10.3 Diferenciais reais do WeDOTalent

1. **FairnessGuard em 3 camadas (L1+L2+L3):** arquitetura única — regex determinístico + categorização por tipo + LLM semântico. Mais sofisticado do que o bloqueio binário de proxies adotado por HiPeople e LinkedIn, e cobre viés sutil que escapa do vocabulário fixo.

2. **14 atributos protegidos explícitos:** número superior ao declarado publicamente pelos 4 concorrentes analisados. Publicação oficial da lista planejada para Q2/2026 como parte deste documento.

3. **Contra-argumentação ativa em `hiring_policy.yaml`:** LIA não apenas bloqueia critérios proibidos — contra-argumenta educativamente citando Lei 9.029/95. **Nenhum concorrente descreve mecanismo equivalente publicamente.**

4. **FairnessGuard end-to-end:** cobertura em CV screening, WSI evaluation e pipeline transitions — não apenas na triagem inicial de currículos.

5. **4 variantes contextuais de compliance_block:** granularidade `decision` / `communication` / `operational` / `defensive` — não evidenciada publicamente pelos concorrentes.

6. **Right to contest direto ao candidato:** implementado em 2026-04-23 via endpoint JWT-token, antes que obrigação regulatória (02/08/2026) entre em vigor. Nenhum dos 4 concorrentes publica mecanismo equivalente.

### 10.4 Gaps vs. mercado

- **Bias audit independente publicado anualmente:** Eightfold é referência (BABL AI, menor ratio 0.880). Roadmap WeDOTalent: Q3/2026 (§11.2).
- **Certificação ISO/IEC 42001:2023:** Workday e Eightfold têm. Roadmap WeDOTalent: 2027 (§11.3).
- **AI Fact Sheets formato padronizado:** Workday estabelece benchmark. Fact Sheets WeDOTalent publicadas 2026-04-23 (§11.2.a).

### 10.5 Fontes primárias (15 URLs verificáveis)

- EU AI Act Anexo III: https://artificialintelligenceact.eu/annex/3/
- EU AI Act Art. 13/14/15: https://artificialintelligenceact.eu/section/3-2/
- EU AI Act Art. 86: https://artificialintelligenceact.eu/article/86/
- NIST AI RMF 1.0: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- LGPD Art. 20: https://lgpd-brasil.info/capitulo_03/artigo_20
- Eightfold Responsible AI: https://eightfold.ai/responsible-ai/
- Eightfold Bias Audit 2026 (PDF): https://eightfold.ai/wp-content/uploads/eightfold-summary-of-bias-audit-results.pdf
- Workday Responsible AI Practices: https://www.workday.com/en-us/artificial-intelligence/responsible-ai-practices.html
- Workday Independent Verifications: https://blog.workday.com/en-us/workday-secures-dual-independent-verifications-of-its-approach-to-responsible-ai.html
- HiPeople AI Resume Screening: https://www.hipeople.io/blog/introducing-hipeople-ai-resume-screening-automate-inbound-chaos-once-and-forever
- HiPeople Warden AI Dashboard: https://trust.warden-ai.com/hipeople/ai-application-screening
- LinkedIn Responsible AI Principles: https://www.linkedin.com/blog/member/trust-and-safety/responsible-ai-principles
- LinkedIn LiFT Toolkit (GitHub): https://github.com/linkedin/LiFT
- NYC Local Law 144 Guide: https://www.warden-ai.com/resources/hr-tech-compliance-nyc-local-law-144

---

## 11. Roadmap Público de Publicações e Implementações

### 11.1 O que já foi feito (2026-04-23)

| ID | Entrega | Artefato canônico |
|----|---------|-------------------|
| Fix P0 | Regras de fairness + HITL no agente autônomo | `app/prompts/domains/autonomous.yaml` |
| Fix P0 | Direito de contestação Art. 86 declarativo | `app/prompts/shared/compliance_block.yaml` (`right_to_contest`) |
| Fix P1 | Compliance block em culture_analysis | `app/prompts/domains/culture_analysis.yaml` (bloco `<compliance_hr>`) |
| Fix P1 | Prologue de compliance no roteador | `app/prompts/domains/orchestrator.yaml` |
| Ativação P1 | FairnessGuard Layer 3 em produção | `.env` + `FAIRNESS_LAYER3_RUNBOOK.md` |
| Novo P0 | Endpoint Art. 86 direto-ao-candidato | `/api/v1/candidate/decisions/explain` |
| Novo P0 | Tool `explain_candidate_decision` | `app/domains/candidate_self_service/tools/explain_candidate_decision.py` |
| Publicação P1 | 5 AI Fact Sheets PT + EN | `docs/responsible-ai/fact-sheets/*.md` |
| Publicação P2.1 | Este documento (Art. 11 Tech Doc) | `docs/responsible-ai/eu-ai-act-technical-documentation-pt.md` + `-en.md` |

### 11.2 O que ainda precisa ser feito

#### a) Publicação de informações sobre features
Fact Sheets criadas — próximo passo é **publicação no site wedotalent.cc**. Requer:
- Decisão de rota final (`wedotalent.cc/responsible-ai/fact-sheets/...`)
- Design do template HTML para renderização pública
- Link no menu/footer do produto
- Revisão jurídica final das versões PT + EN

**Responsável:** equipe de Marketing + Legal + DPO
**Prazo sugerido:** Q2/2026

#### b) Bias audit independente com publicação
Plano completo em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.3 — 3 sprints (9 semanas):
- Sprint A (4 semanas): construir `bias_audit_service.py` interno que calcula DI ratio por grupo
- Sprint B (3 semanas): contratar auditor externo (opções: BABL AI, Warden AI, Coalfire)
- Sprint C (2 semanas): publicar resultados em `wedotalent.cc/responsible-ai/bias-audit-2026`

**Responsável:** Compliance team + Eng (Sprint A) + DPO (contratação)
**Prazo sugerido:** Q3/2026

#### c) Endpoint Art. 86 ✅ **FEITO em 2026-04-23**
Ver §11.1. Próximos passos de operacionalização:
- Frontend do candidate portal que chama o endpoint e renderiza resposta
- Template de email com link JWT para o candidato acessar
- Configurar canal formal de contestação por `company_id` (`CompanyComplianceSettings`)

**Responsável:** FE team + Product
**Prazo sugerido:** Q2/2026

#### d) Certificação ISO/IEC 42001:2023
- Estruturar AIMS (AI Management System) formal
- Conduzir AI Impact Assessment (AIIA)
- Passar por auditoria de certificação

**Responsável:** DPO + executivos
**Prazo sugerido:** 2027

#### e) Registro no EU AI Act database
Obrigatório após 02/08/2026 para providers de sistemas de alto risco. Este documento (após revisão jurídica) será a base para o registro.

**Responsável:** Legal + DPO
**Prazo:** pós 02/08/2026 (quando database estiver ativo)

#### f) Página pública `wedotalent.cc/responsible-ai`
Página-hub que linka: Fact Sheets, este Technical Documentation, Bias Audit (quando publicado), princípios de IA responsável, canal de contato.

**Responsável:** Marketing + Legal
**Prazo sugerido:** Q3/2026 (depois de bias audit Q3)

#### g) SLA formal de incidentes de fairness
Documentar tempos de resposta e procedimentos de remediação para incidentes detectados por `fairness_audit_log` ou escalações via `guardrails_block.yaml`.

**Responsável:** Compliance team + DPO
**Prazo sugerido:** Q4/2026

#### h) Revisão jurídica externa deste documento
Antes de publicação pública e antes do registro no EU AI Act database, revisão por escritório jurídico especializado em AI/LGPD/EU AI Act.

**Responsável:** Legal (aprovação do fornecedor pelos executivos)
**Prazo sugerido:** Q2/2026

### 11.3 Timeline consolidada

| Trimestre | Entregas |
|-----------|----------|
| **Q2/2026** (em curso) | Fact Sheets publicadas no site; frontend Art. 86 endpoint; revisão jurídica deste doc |
| **Q3/2026** | Bias audit independente completo; publicação em página pública |
| **Q4/2026** | SLA formal; consolidação da página `wedotalent.cc/responsible-ai` |
| **Pós 02/08/2026** | Registro no EU AI Act database |
| **2027** | Preparação para ISO 42001 + auditoria de certificação |

### 11.4 Responsabilidades

| Papel | Responsabilidades |
|-------|-------------------|
| **Compliance team** | Conteúdo e atualização das Fact Sheets + este documento + monitoramento de métricas |
| **Engenharia** | Endpoints, flags de feature, testes de regressão, atualização de YAMLs |
| **DPO** | Revisão legal, declaração de conformidade, contratação de auditor externo, registro no database EU |
| **Marketing** | Página pública responsible-ai, comunicação de atualizações, design de Fact Sheets |
| **Executivos (Paulo)** | Aprovação de auditor externo, orçamento para ISO 42001, decisões de publicação |

---

## 12. Governança e Responsabilidades

### 12.1 Data Protection Officer (DPO)

- **Contato:** compliance@wedotalent.cc (canal a configurar em produção)
- **Atribuições:** revisão legal, aprovação de políticas, interface com autoridades (ANPD no Brasil, DPAs na UE)

### 12.2 Equipe de compliance

- Monitoramento semanal de `fairness_audit_log`
- Revisão mensal de custos e latência do FairnessGuard L3
- Revisão trimestral de políticas e fact sheets
- Escalação de incidentes de fairness para o DPO

### 12.3 Cadência de revisão deste documento

- **Anual** por padrão
- **Triggered** quando houver:
  - Mudança arquitetural significativa (novo agente, novo modelo LLM, nova camada de defesa)
  - Atualização regulatória relevante (EU AI Act, LGPD, NIST, ISO)
  - Resultados de bias audit que alterem §6.3
  - Incidente crítico de fairness ou segurança

---

## 13. Declaração de Conformidade

> Este documento consolida a documentação técnica exigida pelo EU AI Act Art. 11 (Annex IV) para sistemas de IA de alto risco classificados no Anexo III, categoria 4.
>
> A WeDOTalent declara que a plataforma LIA:
> - Opera com supervisão humana em todas as decisões de alto impacto (Art. 14)
> - Possui mecanismos documentados de transparência ao operador e ao candidato (Arts. 13 e 86)
> - Implementa testes de fairness em três camadas (L1+L2+L3) de defesa
> - Mantém audit trail rastreável de todas as decisões automatizadas
> - Garante direito de revisão humana e contestação conforme EU AI Act Art. 86 e LGPD Art. 20
>
> Este documento está **pronto para revisão jurídica externa** antes de publicação pública e registro no EU AI Act database (quando ativo).

Assinaturas (pendentes):
- [ ] Data Protection Officer
- [ ] Diretor de Engenharia
- [ ] CEO/Fundador

---

## Apêndice A — Referências cruzadas aos guias existentes

- `docs/reconstruction-guides/COMPLIANCE_RECONSTRUCTION_GUIDE.md` — arquitetura de defesa em 8 camadas, auditoria completa, benchmark detalhado (§10), plano de ação P0/P1 (§11)
- `docs/reconstruction-guides/LIA_PERSONA_RECONSTRUCTION_GUIDE.md` — camada de prompts, SystemPromptBuilder, 24 domain YAMLs
- `docs/reconstruction-guides/INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` — agentes, tools, orquestração
- `docs/reconstruction-guides/RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` — circuit breakers, learning loop
- `docs/reconstruction-guides/CANONICAL_FILES_BY_THEME.md` — índice master
- `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md` — operação da camada L3
- `docs/responsible-ai/fact-sheets/` — 5 fact sheets PT + EN

## Apêndice B — Changelog de compliance (2026-04-14 a 2026-04-23)

| Data | Alteração | Arquivo |
|------|-----------|---------|
| 2026-04-14 | Versão inicial `autonomous.yaml` sem compliance declarativo | `autonomous.yaml` |
| 2026-04-22 | Auditoria exaustiva vs. frameworks regulatórios | `COMPLIANCE §10` |
| 2026-04-23 | Fix P0 `autonomous.yaml` (behavioral_rules + HITL + compliance) | `autonomous.yaml` |
| 2026-04-23 | Fix P0 `compliance_block.yaml` (`right_to_contest` Art. 86) | `compliance_block.yaml` |
| 2026-04-23 | Fix P1 `culture_analysis.yaml` (`<compliance_hr>`) | `culture_analysis.yaml` |
| 2026-04-23 | Fix P1 `orchestrator.yaml` (compliance prologue) | `orchestrator.yaml` |
| 2026-04-23 | Ativação `FAIRNESS_LAYER3_ENABLED=true` em produção | `.env` |
| 2026-04-23 | Endpoint `/api/v1/candidate/decisions/explain` | `candidate_portal_explanation.py` |
| 2026-04-23 | Tool `explain_candidate_decision` | `explain_candidate_decision.py` |
| 2026-04-23 | 5 AI Fact Sheets publicadas (PT + EN) | `fact-sheets/*.md` |
| 2026-04-23 | Este documento publicado (v1.0) | `eu-ai-act-technical-documentation-pt.md` + `-en.md` |

## Apêndice C — Contatos e canais

- **Compliance:** compliance@wedotalent.cc
- **Suporte operacional:** support@wedotalent.cc
- **Privacidade (LGPD):** dpo@wedotalent.cc
- **Canal formal de contestação (EU AI Act Art. 86):** configurável por `company_id` — deployer define seu próprio canal em `CompanyComplianceSettings.contato_revisao`

## Apêndice D — Glossário bilíngue PT-EN (termos regulatórios)

| PT-BR | EN | Origem |
|-------|-----|--------|
| Sistema de IA de Alto Risco | High-Risk AI System | EU AI Act Art. 6 + Anexo III |
| Atributos protegidos | Protected attributes | Lei 9.029/95 + CLT Art. 373-A |
| Supervisão humana | Human oversight / Human-in-the-Loop (HITL) | EU AI Act Art. 14 |
| Direito à explicação | Right to explanation | EU AI Act Art. 86 |
| Direito de revisão | Right to review | LGPD Art. 20 |
| Decisão automatizada | Automated decision-making | LGPD Art. 20 + EU AI Act Art. 22 (GDPR linked) |
| Disparate impact ratio | Disparate impact ratio | NYC LL144 + EEOC four-fifths rule |
| Audit trail | Audit trail | EU AI Act Art. 12 |
| Provider (de sistema IA) | Provider | EU AI Act Art. 3 |
| Deployer (usuário do sistema) | Deployer | EU AI Act Art. 3 |
| Sujeito da decisão | Decision subject | GDPR + LGPD |
| Ação afirmativa (permitida) | Affirmative action (permitted) | Lei 8.213/91 + Lei 12.990/2014 |
| Sistema de gestão de IA | AI Management System (AIMS) | ISO/IEC 42001:2023 |

---

*Documento produzido em 2026-04-23 | Versão 1.0 | Todas as afirmações são embasadas em leitura direta de arquivos canônicos em `lia-agent-system/` ou em URL regulatória verificável (§10.5). Zero invenção.*
