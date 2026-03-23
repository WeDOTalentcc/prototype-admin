---
name: wedo-governance
description: "Governança da plataforma WeDO Talent conforme Guia v3.3. Use ao criar features, agentes, prompts, integrações ou quando precisar verificar compliance com as 13 Crenças, Inegociáveis, Production Readiness (18 critérios) ou governança de agentes IA. Referência canônica: attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md"
---

# WeDO Governance — Governança da Plataforma WeDO Talent (Guia v3.3)

Esta skill codifica as regras de governança do WeDO Talent derivadas do Guia Completo v3.3 (Parte I — Manifesto e Parte VII — Roadmap). Use-a como referência rápida e checklist de compliance ao implementar qualquer feature, agente ou integração.

> **Referência canônica completa:** `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md`
> **Auditoria obrigatória:** Use `feature-audit` (`.agents/skills/feature-audit/`) como gate principal de auditoria antes de concluir qualquer tarefa.
> **Skills relacionadas:** `screening-compliance`, `dei-fairness`, `lgpd-data-protection`

---

## 1. Quando Usar

Carregue esta skill quando:

- Criar ou modificar **agentes IA**, prompts, intents ou domínios
- Implementar **features que afetam candidatos** (screening, ranking, rejeição, comunicação)
- Configurar **integrações externas** (LLM providers, WhatsApp, ATS, email)
- Precisar verificar **compliance** com as 13 Crenças ou Inegociáveis
- Preparar um **deploy para produção** (Production Readiness Gate)
- Implementar ou auditar **FairnessGuard, PII Masking, Consent Management**
- Criar **interfaces de usuário** (verificar WCAG 2.1 AA)
- Revisar **custos de IA** (token budgets, fallback chains)
- Receber pedido de **auditoria de governança** ou compliance
- Criar **policies, automações ou workflows** que tomam decisões sobre pessoas
- Verificar **aprendizado contínuo** (LongTermMemory, FeedbackLearning, preferências por recrutador)

---

## 2. As 13 Crenças (Resumo Executivo)

| # | Nome | Princípio-chave | Verificação rápida |
|---|------|----------------|-------------------|
| 01 | Humano em Primeiro Lugar | IA recomenda, humanos decidem. Decisões de alto impacto nunca automatizadas. | Existe caminho de escalação humana? Recrutador aprova antes de ação irreversível? |
| 02 | Justa e Não-Discriminatória | Teste de viés obrigatório. Atributos protegidos mascarados antes do LLM. | FairnessGuard ativo? Atributos protegidos (nome, gênero, idade, etnia, foto) removidos do input do LLM? |
| 03 | Transparente e Explicável | Candidato sabe que é avaliado por IA. Opt-out disponível. | "Por que fui rejeitado?" é respondível? System prompts versionados? |
| 04 | Segura e Respeitosa com Privacidade | Dados do candidato são confiança sagrada. Coleta mínima. LGPD inegociável. | PII masking ativo? Secrets fora do código? TLS 1.3+? |
| 05 | Construída por Humanos, Para Humanos | Todo engenheiro entende o impacto. Auditorias trimestrais. Red teaming contínuo. | Feedback loop do cliente → produto existe? |
| 06 | Em Melhoria Contínua | Métricas visíveis. Post-mortems em todo incidente. Iterar rápido, medir com cuidado. | Nenhuma dívida técnica que comprometa fairness/segurança? |
| 07 | Resiliente por Design | Nenhum ponto único de falha. Multi-provider LLM. Circuit breakers obrigatórios. | Circuit Breaker configurado? LLM fallback chain testada? Rate limiting ativo? |
| 08 | Observável e Rastreável | Toda saída de agente logada em formato estruturado. Trilha de auditoria persistente. | Structured logging (sem print)? Monitoramento e alertas ativos? |
| 09 | Consciente de Custos | Budget de tokens por interação. Limites por tenant. Cascata de barato → caro. | TokenTrackingService ativo? Budget por empresa configurado? CascadedRouter usado? |
| 10 | Inteligência vs Determinismo | IA onde agrega inteligência, código determinístico onde precisa de garantia. | Decisão que rejeita candidato tem guarda determinística? ConfidencePolicyService aplicado? |
| 11 | Anti-Bajulação | IA nunca concorda silenciosamente com pedidos que comprometam qualidade. | Regras 145/147 no system prompt? Benchmarks setoriais referenciados? Registro formal de risco? |
| 12 | Autonomia Progressiva | Nível de automação configurável por empresa. Cresce com confiança demonstrada. | Empresa nova começa como assistente? Autonomia não é concedida por padrão? |
| 13 | Acessível e Inclusiva | WCAG 2.1 AA obrigatório. Acessibilidade é direito, não feature. | aria-labels em componentes interativos? sr-only? focus-visible? Contraste 4.5:1? |

---

## 3. Inegociáveis

Estes são pré-condições para entregar QUALQUER feature. Se qualquer um falha, a feature não sai.

| # | Inegociável | Como verificar |
|---|------------|---------------|
| 1 | Nenhum candidato rankeado sem WSI explicitável | Score WSI tem raciocínio rastreável de input a output |
| 2 | Nenhuma rejeição automática sem review gate | Toda rejeição passa por humano ou gate de revisão configurado |
| 3 | FairnessGuard ativo em 100% das decisões de screening/ranking | Guard intercepta todas as decisões com log de intervenções |
| 4 | PII masking em todos os logs (PIIMaskingFilter) | install_global_pii_masking() no root logger; CPF, email, telefone, nomes mascarados |
| 5 | Consent antes de qualquer processamento | Nenhum candidato entra no pipeline sem consentimento registrado |
| 6 | Dados deletados quando solicitado (SLA 15 dias) | DSR (Data Subject Request) funcional com fluxo de exclusão |
| 7 | Human override sempre disponível | Recrutador pode reverter/sobrescrever qualquer decisão da IA |
| 8 | WCAG 2.1 AA em todas as interfaces | Navegação por teclado, contraste 4.5:1, aria-labels, screen reader |

**Regra absoluta:** Sem exceções. Sem "consertamos depois". Sem aprovação manual para bypass.

---

## 4. Governança de Agentes IA

### 4.1 EnhancedAgentMixin

Todo agente deve herdar EnhancedAgentMixin que fornece:
- **Memory**: LongTermMemoryService — contexto persistido entre sessões
- **Learning**: FeedbackLearningService + OutcomeTracker — aprende com resultados
- **Autonomy**: AutonomyEngine — nível de autonomia configurável por empresa

### 4.2 ConfidencePolicyService

Quando a IA infere um valor, o sistema calcula confiança e determina ação:

| Ação | Confiança | Comportamento |
|------|-----------|---------------|
| APPLY_SILENT | >= 0.85 | Aplica automaticamente sem notificar |
| APPLY_NOTIFY | 0.70 - 0.84 | Aplica mas notifica o recrutador |
| ASK_USER | < 0.70 | Apresenta como sugestão, pede confirmação |
| ALERT_CONFLICT | N/A | Múltiplas fontes divergem, alerta conflito |

### 4.3 Circuit Breaker (3 Estados) — 7 Circuitos por Serviço

Estados: `CLOSED` (normal) → N falhas → `OPEN` (rejeitando) → recovery_timeout → `HALF_OPEN` (testando) → sucesso → `CLOSED` / falha → `OPEN`

**Tabela completa dos 7 circuitos (`app/shared/resilience/circuit_breaker.py`):**

| Circuito | failure_threshold | recovery_timeout | timeout req. | Fallback |
|---------|:-----------------:|:----------------:|:------------:|---------|
| `ANTHROPIC_CIRCUIT` | 5 | 30s | 60s | Gemini (primário) |
| `OPENAI_CIRCUIT` | 5 | 30s | 60s | Gemini (fallback secundário) |
| `GEMINI_CIRCUIT` | 5 | 30s | 60s | Claude (fallback) |
| `PEARCH_CIRCUIT` | 3 | 60s | 30s | Database local (candidate pool) |
| `WORKOS_CIRCUIT` | 5 | 30s | 15s | Cache de tokens + login legacy |
| `MERGE_CIRCUIT` | 5 | 45s | 30s | DLQ para sincronização posterior |
| `GOOGLE_CALENDAR_CIRCUIT` | 5 | 60s | 30s | Agendamento offline (persiste localmente) |

> Cada nova integração externa **deve** ter um circuito registrado em `ALL_CIRCUITS`. Verificar se `ENABLE_*` feature flag desativa o circuito corretamente quando integração está OFF.

### 4.4 LLM Fallback Chain

1. **Claude** (Anthropic) — provider primário
2. **Gemini** (Google) — primeiro fallback (ANTHROPIC_CIRCUIT OPEN)
3. **OpenAI** (GPT) — segundo fallback (GEMINI_CIRCUIT OPEN)
4. **Erro crítico** — todos os 3 falharam → log P0 + alerta engenharia + HTTP 503

### 4.5 Caching Semântico em 3 Camadas (`CacheManagerService`)

`app/shared/resilience/cache_manager_service.py`

| Camada | Tipo | Latência | TTLs |
|--------|------|----------|------|
| **Session** (`SessionCache`) | In-memory, hash O(1) | Sub-ms | 1h (sessão ativa) |
| **Redis** (`RedisCache`) | Distribuído, compartilhado | ~1ms | Varia por domínio |
| **PostgreSQL** (`PostgresCache`) | Persistente longo prazo | ~10ms | 7-30 dias |

**TTLs por tier (`CacheTTL`):**

| Tier | TTL | Uso |
|------|-----|-----|
| `SESSION` | 1h (3.600s) | Contexto de conversa ativa |
| `VOLATILE` | 1 dia (86.400s) | Dados que mudam frequentemente |
| `STANDARD` | 7 dias (604.800s) | Dados moderadamente estáveis |
| `STABLE` | 30 dias (2.592.000s) | Dados raramente alterados |

**TTLs por domínio (`DOMAIN_TTL_CONFIG`):**

| Domínio | TTL | Justificativa |
|---------|-----|---------------|
| `CANDIDATE_SEARCH` | 300s | Resultados mudam com novos candidatos |
| `WSI_SCORE` | 3.600s | Scores não mudam dentro de uma sessão |
| `SKILL_CATALOG` | 86.400s | Catálogo muda raramente |
| `LLM_RESPONSE` | 900s | Respostas para prompts idênticos |

### 4.6 Dead Letter Queue (DLQ)

Retry com backoff exponencial: `delay = 60s × (2 ^ retry_count)`

| Tentativa | Delay |
|-----------|-------|
| 1ª retry | 60s |
| 2ª retry | 120s |
| 3ª retry | 240s |
| > 3 tentativas | DLQ — `status="failed"` + `failed_at` timestamp + alerta ops |

`max_delay`: 3.600s (1h) — cap de segurança. Jitter ±10% para evitar thundering herd.

### 4.7 Multi-Channel Fallback (Comunicação com Candidato)

Fallback progressivo quando canal primário falha:

1. **WhatsApp** (Meta API / Twilio) — canal primário
2. **SMS** (Twilio) — quando WhatsApp indisponível
3. **Email** (SendGrid / Resend / Mailgun) — última linha
4. **DLQ** — registra e escala para humano se todos falharem

Conteúdo e compliance são idênticos em todos os canais.

### 4.8 Rate Limiting — 2 Níveis

**Nível 1 — Middleware HTTP** (`app/middleware/rate_limiter.py`):

| Limite | Valor | Escopo |
|--------|-------|--------|
| Por minuto/usuário | 600 req | HTTP requests |
| Por hora/usuário | 20.000 req | HTTP requests |
| Por minuto/empresa | 3.000 req | HTTP requests |
| Por hora/empresa | 60.000 req | HTTP requests |
| Penalty block | 60s | Ao exceder limite |

**Nível 2 — TokenTrackingService** (proteção de custo):

| Limite | Valor | Escopo |
|--------|-------|--------|
| Por minuto/usuário | 60 chamadas LLM | Tokens |
| Por hora/usuário | 100.000 tokens | Tokens |
| Por dia/usuário | 500.000 tokens | Tokens |
| Por dia/empresa | 5.000.000 tokens | Tokens |
| Por mês/empresa | $500 | Custo |

Alertas: 80% do budget → alerta suave | 100% → bloqueio com mensagem clara.

### 4.9 TokenTrackingService e Budget

Cada chamada LLM registrada com: `user_id`, `company_id`, `agent_type`, `intent`, `input_tokens`, `output_tokens`, `model`, `latency_ms`.

`AiCreditsBalance`: wallet por empresa com `check_limits()` antes de cada chamada e `set_custom_limits()` por empresa.

### 4.10 Anti-Bajulação

A IA NUNCA concorda silenciosamente com pedidos que comprometam qualidade. 8 benchmarks setoriais referenciados (ABRH, GPTW, Gupy, Robert Half, LinkedIn, Glassdoor, IBGE, MTE). Regras 145 e 147 do system prompt. Divergências documentadas formalmente na trilha de auditoria.

### 4.11 CascadedRouter (Economia de Cascata)

Resolver intenções na camada mais barata possível: Memory cache (O(1)) > Fast router (regex/keyword) > LLM fallback. Mantém estatísticas em tempo real: `memory_hits`, `fast_hits`, `llm_hits`, `total`.

---

## 5. Framework de Aprendizado Contínuo (Seção 15 do Guia)

A LIA aprende com cada interação, correção e outcome. O aprendizado é estruturado em 4 camadas.

### 5.1 LongTermMemoryService — 4 Tipos de Memória

`app/shared/agents/long_term_memory.py` — persistida em `agent_long_term_memory` com isolamento por `company_id` e `domain`.

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `pattern` | Padrões recorrentes das interações | "Empresa X sempre contrata CLT, nunca PJ" |
| `preference` | Preferências do recrutador aprendidas | "Recrutador Y prefere listar 5 candidatos, não 10" |
| `learning` | Aprendizados de correções e feedbacks | "Faixa salarial Dev Sênior SP: R$18-22k, não R$15-18k" |
| `outcome` | Resultados de contratações para calibração | "Vagas Data Science Python+SQL preenchem em 35 dias" |

Upsert inteligente: memória existente atualiza o valor e recebe bônus de `+0.1` no `relevance_score` (cap: 1.0).

### 5.2 FeedbackLearningService — Aprendizado por Correção

`app/services/feedback_learning_service.py` — ciclo baseado em correções do recrutador no wizard de criação de vagas.

**Ciclo:** Execução → Sugestão LIA → Recrutador aceita/corrige/rejeita → `FeedbackLearningService` registra → `LearningExtractor` converte em formato DPO → Revisão de compliance → Memória persistida.

**Níveis de confiança** (baseados em tamanho de amostra):

| Nível | Amostras | Comportamento |
|-------|----------|---------------|
| `high` | ≥ 10 | Recomendações aplicadas com confiança |
| `medium` | 5-9 | Recomendações apresentadas como sugestão |
| `low` | 1-4 | Dados insuficientes para recomendação |
| `none` | 0 | Sem dados — não aplica |

**Análise de padrões de correção:** detecta vieses sistemáticos nas sugestões (ex: se recrutadores corrigem salários para cima em >10% dos casos, gera recomendação automática de ajuste).

### 5.3 OutcomeTracker — Métricas de Resultado

Rastreia outcomes de contratação via `record_outcome` / `get_success_patterns` para calibrar recomendações futuras:

- **TTF (Time to Fill):** dias da abertura ao fechamento da vaga
- **Funil:** `candidate_count_total` → `screened` → `interviewed` → `offered` (taxas de conversão por etapa)
- **Satisfação:** `satisfaction_score` (1-5) do hiring manager
- **Salário:** comparação entre faixa inicial e salário final efetivo
- **Skills efetivas:** quais skills dos contratados foram mais relevantes

Padrões analisados por role, seniority e período (default: 12 meses).

### 5.4 Recruiter Preferences Learning — Personalização Individual

A LIA aprende preferências de cada recrutador individualmente e as aplica automaticamente:

- Formato de apresentação preferido (resumo curto vs. análise detalhada)
- Quantidade de candidatos por shortlist
- Campos priorizados na comparação
- Tom de comunicação preferido para mensagens a candidatos
- Horários e frequência de notificações

Armazenadas como tipo `preference` no `LongTermMemoryService`, **isoladas por recrutador e empresa**. Aplicadas via `ConfidencePolicyService` com `APPLY_SILENT` quando confiança na preferência é alta (≥ 0.85). A fonte `recruiter_history` tem confiança base 0.80 no `ConfidencePolicyService`.

### 5.5 CompanySkill Promotion Dinâmica — Aprendizado Colaborativo

Quando múltiplos recrutadores da mesma empresa adicionam uma skill que não existe no catálogo padrão:

1. Skill registrada como `learning` na memória de longo prazo
2. Após threshold de ocorrências → promovida ao catálogo da empresa
3. Passa a ser sugerida automaticamente para vagas similares da mesma empresa

### 5.6 LearningExtractor — 3 Categorias

Após cada loop ReAct (via `EnhancedAgentMixin._post_loop_learning`), aprendizados são extraídos automaticamente em 3 categorias:

| Categoria | O que extrai |
|-----------|-------------|
| `patterns` | Padrões comportamentais detectados nas interações |
| `preferences` | Preferências explícitas ou implícitas do recrutador |
| `outcomes` | Resultados que calibram recomendações futuras |

DPO export disponível via `TrainingDataService` (endpoint JSONL) para uso futuro em fine-tuning.

---

## 6. Production Readiness Gate (18 Critérios)

Todo deploy para produção deve passar 18/18. Sem exceções.

| # | Critério | Categoria |
|---|----------|-----------|
| 1 | Circuit Breaker configurado em todos os serviços externos | Resiliência |
| 2 | LLM fallback chain testada end-to-end | Resiliência |
| 3 | PII Masking ativo em todos os logs | Segurança |
| 4 | Rate Limiting configurado por tenant | Segurança |
| 5 | Dead Letter Queue ativa para mensagens falhadas | Resiliência |
| 6 | Token budget configurado por company | Custos |
| 7 | Consent management ativo para novos candidatos | Compliance |
| 8 | FairnessGuard ativo em todas as interações | Fairness |
| 9 | Bias audit baseline estabelecido | Fairness |
| 10 | Health check endpoint respondendo | Operações |
| 11 | Error alerting configurado (P0/P1) | Operações |
| 12 | Backup de dados verificado | Operações |
| 13 | Rollback procedure documentado | Operações |
| 14 | Load test executado (P95 < 5s) | Performance |
| 15 | Security scan limpo (0 critical/high) | Segurança |
| 16 | LGPD compliance checklist aprovado | Compliance |
| 17 | WCAG 2.1 AA compliance verificado | Acessibilidade |
| 18 | PII Masking global ativo em todos os loggers | Segurança |

---

## 7. Referência Rápida de Decisão

Antes de implementar qualquer feature, responda estas 5 perguntas:

1. **É justo?** — Testamos para viés? Discrimina mesmo inadvertidamente?
2. **É necessário?** — Genuinamente melhora fairness, segurança ou experiência?
3. **É transparente?** — Conseguimos explicar para candidatos e reguladores?
4. **Conseguimos medir?** — Temos métricas? Detectamos regressões?
5. **É resiliente?** — O que acontece quando uma dependência falha?

**Se todas = SIM: Construa. Se qualquer = NÃO: Reconsidere ou redesenhe.**

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/wedo-governance` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/wedo-governance.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/wedo-governance/SKILL.md` |

**Quando ativar:**
- Antes de criar qualquer feature nova (5 Perguntas)
- Ao preparar deploy (Production Readiness Gate — 18 critérios)
- Ao criar agentes IA, prompts ou integrações externas
- Ao verificar compliance com as 13 Crenças e 8 Inegociáveis
