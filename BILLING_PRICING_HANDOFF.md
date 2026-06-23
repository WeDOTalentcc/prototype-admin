# WeDOTalent — Billing, Pricing & Plans: Complete Handoff

> **Status:** documento canônico de referência para desenvolvimento de billing/pricing.
> **Data:** 2026-06-23 | **Mantenedor:** Paulo (produto) | **Destino:** devs + Claude Code
>
> Este documento é autocontido. Um dev pode ler este arquivo e entender completamente
> o que existe, o que está pendente e quais são as decisões de produto tomadas — sem
> precisar de contexto adicional.

---

## 1. VISÃO GERAL DO MODELO COMERCIAL

### 1.1 Filosofia de pricing

WeDOTalent cobra em **3 camadas independentes**:

```
CAMADA 1 — Assinatura fixa
  Recorrente mensal. Cobre seats (licenças de usuário), acesso
  à plataforma e quota de consumo incluída no plano.

CAMADA 2 — Consumo variável (pass-through ou markup)
  LLM tokens (Anthropic/BYOK), créditos Pearch, créditos Apify,
  execuções de agentes. Cobrados por uso real, separado do plano base.

CAMADA 3 — Excedente (overage)
  Quando consumo mensal ultrapassa os caps do plano. Arquitetura
  implementada; preços de overage pendentes de definição.
```

### 1.2 Programa ALFA (parceiros estratégicos)

Clientes ALFA são empresas âncora que entram antes do go-to-market amplo.
Condições especiais negociadas individualmente via admin WeDOTalent.

| | Fase 1 | Fase 2 |
|---|---|---|
| **Duração** | Meses 1-3 | Mês 4 em diante |
| **Receita** | Gratuito (validação) | Comercial com desconto |
| **Desconto típico** | N/A | 50% sobre assinatura regular |
| **Custo variável** | Pass-through a custo (sem markup) | Pass-through a custo (sem markup) |
| **Vigência** | Contrato de 12 meses | Renovação automática |

**Caso Sodexo (referência):**
- Fase 2 = R$2.500/mês (50% sobre R$5.000 regular)
- LLM: pass-through a custo sem markup (vs. markup 3x para clientes regulares)
- Créditos Pool: $0,36/candidato sourced (Pearch $0,24 + Apify $0,12)

---

## 2. PLANOS E TIERS

### 2.1 Tabela canônica de planos

Fonte de verdade: `lia-agent-system/libs/models/lia_models/plan_config.py`
Seed: `lia-agent-system/alembic/versions/292_add_company_plan_configs.py`
Atualização de seats: `lia-agent-system/alembic/versions/293_update_plan_seats.py`

| Dimensão | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|
| **max_seats** | 2 | 5 | 10 | 15 |
| **llm_monthly_cap** (tokens) | 500K | 2M | 10M | 40M |
| **llm_request_ceiling** (tokens/req) | 2K | 2K | 10K | 50K |
| **embedding_monthly_cap** | 10M | 50M | 200M | 500M |
| **pearch_credits_monthly** | 200 | 500 | 1.500 | 4.000 |
| **pearch_credits_rollover** | N | N | N | S |
| **apify_credits_monthly** | 200 | 500 | 1.500 | 4.000 |
| **apify_credits_rollover** | N | N | N | S |
| **max_custom_agents** | 1 | 2 | 10 | 50 |
| **max_sourcing_agents** | 1 | 1 | 5 | 20 |
| **max_digital_twins** | 0 | 0 | 0 | 10 |
| **max_campaigns** | 0 | 0 | 5 | 20 |
| **agent_executions_monthly** | 50 | 200 | 1.000 | 5.000 |
| **agent_execution_price_cents** (excedente) | 0 | 40c | 30c | 20c |
| **byok_enabled** | S | S | S | S |
| **is_trial** | S | N | N | N |
| **trial_days** | 30 | — | — | — |

### 2.2 Visibilidade operacional estimada (para o cliente)

Tradução dos caps técnicos em operações concretas que o cliente consegue entender.
Três blocos: Sourcing, Inteligência IA e Automação & Capacidade.

#### Bloco A — Sourcing (Pearch + Apify)

Pearch e Apify são **dois pools independentes** consumidos em momentos diferentes:

- **Pearch (busca):** 2 créditos/busca → retorna até 20 candidatos com flag "tem email disponível"
  mas sem revelar o contato. Créditos debitados do cap `pearch_credits_monthly`.

- **Apify (reveal):** 1 crédito/candidato → revela email real sob demanda.
  Dispara quando o recrutador adiciona o candidato à vaga ou clica "Revelar".
  Créditos debitados do cap `apify_credits_monthly` (pool separado do Pearch).
  Por padrão NÃO enriquece automaticamente durante a busca
  (`SEARCH_EAGER_CONTACT_ENRICHMENT=False` no código — `_shared.py:670`).

O recrutador pode fazer 100 buscas (usando 200 créditos Pearch), visualizar 2.000 candidatos,
e revelar emails apenas dos candidatos selecionados para trabalhar — economizando créditos Apify.

| Dimensão | Base | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|---|
| **Créditos Pearch/mês** (pool busca) | DB | 200 | 500 | 1.500 | 4.000 |
| **Buscas no pool global/mês** (÷ 2 créditos/busca) | Est. | ~100 | ~250 | ~750 | ~2.000 |
| **Candidatos encontrados/mês** (× 20/busca, média) | Est. | ~2.000 | ~5.000 | ~15.000 | ~40.000 |
| **Créditos Apify/mês** (pool reveal) | DB | 200 | 500 | 1.500 | 4.000 |
| **Candidatos com email revelado/mês** (1 crédito/cand.) | Est. | até 200 | até 500 | até 1.500 | até 4.000 |
| **Rollover Pearch** | DB | N | N | N | S |
| **Rollover Apify** | DB | N | N | N | S |

> "Email revelado" = recrutador adicionou candidato à vaga ou clicou "Revelar".
> Pearch (busca) e Apify (reveal) têm caps separados — o recrutador pode buscar mais
> e revelar seletivamente. Enterprise: créditos não usados acumulam para o mês seguinte.

#### Bloco B — Inteligência IA (LLM)

Todas as operações de IA competem pelo mesmo pool de tokens LLM. Estimativas baseadas
nos tokens médios por operação (fonte: `token_budget_service.py` AGENT_TYPE_REQUEST_OVERRIDES
— ScreeningAgent=1.5x, DeepAnalysisAgent=2x, CVParserAgent=1.25x).

**Tokens médios por operação:**

| Operação | Tokens médios | Base de cálculo |
|---|---|---|
| Triagem de candidato | ~4.000 tokens | req_ceiling × ScreeningAgent (1.5x) |
| Consulta no chat LIA | ~1.000 tokens | req_ceiling × 0.5 (resposta curta) |
| Geração de JD | ~8.000 tokens | req_ceiling × DeepAnalysisAgent (2x) |
| Parsing de CV | ~2.500 tokens | req_ceiling × CVParserAgent (1.25x) |

**Operações estimadas por plano:**

| Dimensão | Trial (500K) | Starter (2M) | Pro (10M) | Enterprise (40M) |
|---|---|---|---|---|
| **Triagens de candidatos/mês** | ~125 | ~500 | ~2.500 | ~10.000 |
| **Consultas no chat LIA/mês** | ~500 | ~2.000 | ~10.000 | ~40.000 |
| **Geração de JDs/mês** | ~62 | ~250 | ~1.250 | ~5.000 |
| **Parsings de CV/mês** | ~200 | ~800 | ~4.000 | ~16.000 |

> Pool compartilhado: triagens, chat, JDs e parsings consomem do mesmo cap de LLM.
> Um cliente que usa mais chat terá menos triagens disponíveis. Exibir na sub-tab
> Consumo como barra única de "IA utilizada" com breakdown por tipo de operação.

#### Bloco C — Automação & Capacidade

Limites operacionais fixos por plano — não dependem de consumo variável.

| Dimensão | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|
| **Execuções de agentes autônomos/mês** | 50 | 200 | 1.000 | 5.000 |
| **Usuários (seats)** | 2 | 5 | 10 | 15 |
| **Vagas/campanhas ativas simultâneas** | 0 | 0 | 5 | 20 |
| **Agentes customizados** | 1 | 2 | 10 | 50 |
| **Agentes de sourcing** | 1 | 1 | 5 | 20 |
| **Digital twins** | 0 | 0 | 0 | 10 |

> Execuções de agentes = chamadas de agentes autônomos completas (ex: agente de sourcing
> rodando pipeline end-to-end, agente de triagem em lote). Custo de excedente:
> Starter=R$0,40/exec | Pro=R$0,30/exec | Enterprise=R$0,20/exec.

### 2.3 Estimativa de custo WhatsApp para o cliente

**Decisão de produto:** WhatsApp é custo do CLIENTE (conta Meta do cliente).
WeDOTalent homologa o número do cliente — não paga WhatsApp Business API.
Os créditos Apify consumidos na plataforma geram conversas WhatsApp estimadas.

**Fórmula canônica:**
```
conversas_estimadas = apify_credits_consumidos * 2
custo_whatsapp_brl  = conversas_estimadas * 0.0588 * taxa_usd_brl
```
Referência: Meta cobra ~$0.0588 USD por conversa de 24h iniciada pela empresa (Brasil).
Taxa USD/BRL usada: R$5,20.

| Plano | Cap Apify/mês | Conversas est. | Custo WhatsApp cliente (R$) |
|---|---|---|---|
| Trial | 200 créditos | ~400 conv. | ~R$122/mês |
| Starter | 500 créditos | ~1.000 conv. | ~R$305/mês |
| Pro | 1.500 créditos | ~3.000 conv. | ~R$915/mês |
| Enterprise | 4.000 créditos | ~8.000 conv. | ~R$2.440/mês |

> Esta estimativa é orientativa — exibir na sub-tab Consumo com disclaimer:
> "Estimativa baseada no consumo de enriquecimento de perfis. Custo cobrado
> diretamente pela Meta na sua conta WhatsApp Business."

### 2.4 Feature flags por plano

```
trial:      { byok: True }
starter:    { bulk_actions, export_full, byok }
pro:        starter + { custom_persona, analytics_advanced, integrations_ats,
                        voice_screening, offer_concierge, projetos_essencial }
enterprise: pro + { projetos_advanced, digital_twins, api_access, white_label }
```

Fonte: campo `feature_flags` JSONB em `company_plan_configs`.
Leitura no frontend: hook `usePlan` em `plataforma-lia/src/hooks/billing/`.

### 2.5 Plano ALFA — PENDENTE de implementação

**Decisão de produto tomada (Paulo, 2026-06-17):**
O plano ALFA não é um tier fixo no catálogo — é um registro customizado no
`company_plan_configs` com `plan_code = "alfa_<client_slug>"` e valores
específicos por cliente, mais o campo `desconto_pct` no `Subscription`.

**O que ainda falta criar:**
- Seed do plano ALFA base (ex: `alfa_base`) em `company_plan_configs`
- Flag `is_alfa_partner` para acionar pass-through em vez de markup LLM
- Admin UI para criar plano customizado e associar a um tenant

---

## 3. SISTEMA DE CRÉDITOS (QUOTA)

### 3.1 Terminologia

| Termo | O que é |
|---|---|
| **Crédito WeDOTalent** | Unidade de consumo. 1 crédito = R$0,12 (definido na proposta comercial). Usado internamente para debitação de quota. |
| **Pearch credit** | Crédito usado para buscas via Pearch (sourcing passivo). |
| **Apify credit** | Crédito usado para enriquecimento de perfil via Apify (LinkedIn scraping). |
| **LLM token** | Unidade de consumo de modelo de linguagem (Anthropic/BYOK). NAO é crédito WeDO — é grandeza separada com cap próprio em tokens. |

### 3.2 Custo por ação (ACTION_CREDIT_COSTS)

Fonte canônica: `lia-agent-system/app/domains/credits/services/credit_service.py`

```python
ACTION_CREDIT_COSTS = {
    "search":             2,
    "analysis":           5,
    "screening":         10,
    "report":             8,
    "ai_chat":            1,
    "email_send":         1,
    "interview_schedule": 3,
    "cv_parsing":         3,
    "bulk_search":        5,
    "pearch_search":      2,   # busca Pearch = 2 creditos = R$0,24 = $0,12 USD
    "apify_enrichment":   1,   # enriquecimento LinkedIn = 1 credito = R$0,12 = $0,12 USD
}
```

**Mapeamento com proposta comercial (Anexo I):**

| Operação na proposta | Créditos proposta | Código | Créditos código | Status |
|---|---|---|---|---|
| Busca Padrão (Pool Global) | 3 créditos / $0,36 | `pearch_search` | 2 créditos | DIVERGE (-1 crédito) |
| Desbloqueio E-mail | 2 créditos / $0,24 | não mapeado | — | PENDENTE |
| Desbloqueio Telefone | 14 créditos / $1,68 | não mapeado | — | PENDENTE |
| Enriquecimento LinkedIn | 1 crédito / $0,12 | `apify_enrichment` | 1 crédito | OK |

**Ação necessária:** adicionar `"telefone_desbloqueio": 14` e `"email_desbloqueio": 2`
ao dicionário `ACTION_CREDIT_COSTS` e criar testes sentinel.

### 3.3 Rastreamento de consumo

Fonte: `lia-agent-system/app/domains/billing/services/consumption_tracking_service.py`

Três funções principais:
- `record_apify_call(...)` — registra 1 crédito por chamada Apify (corrigido de 0 para 1 em commit bfda6bf8f)
- `record_pearch_call(...)` — recebe `credits_consumed` como parâmetro do caller
- `record_llm_call(...)` — registra tokens; `credits_consumed=0` (LLM não debita créditos WeDO — tem cap próprio em tokens)

---

## 4. SISTEMA DE CAPS E ENFORCEMENT

### 4.1 Como o enforcement funciona

Há três sistemas paralelos de cap:

**Sistema A — Token Budget (Redis, por dia)**
Arquivo: `app/shared/observability/token_budget_service.py`
- Cap diário por plano: starter=10K, pro=100K, enterprise=-1 (ilimitado)
- Cap por request: starter=2K, pro=10K, enterprise=50K
- Multiplicadores por tipo de agente: ScreeningAgent=1.5x, ProfileAnalysisAgent=2.5x, DeepAnalysisAgent=2.0x
- Reinicia diariamente a meia-noite UTC
- Lança `RequestBudgetExceededError` quando atingido

**Sistema B — AiCreditsBalance (PostgreSQL, mensal)**
Arquivo: `app/models/ai_consumption.py` + `app/api/v1/ai_consumption.py`
- Cap mensal em tokens (`monthly_limit`, padrão 100.000)
- `overage_allowed` (bool, padrão False) — se False bloqueia; se True cobra excedente
- `overage_rate_cents` — preço por token extra (padrão 0, PENDENTE definição)
- Enforcement em `ai_consumption.py:538` (P1-W3-08)

**Sistema C — Seats (por request, sincrono)**
Arquivo: `app/api/v1/client_users.py:364-370`
- Ao adicionar usuário, conta users ativos do tenant vs. `client.user_limit`
- Retorna HTTP 402 se limite atingido
- `user_limit` vem de `ClientAccount.settings["user_limit"]` ou default 10

### 4.2 Tabela de enforcement por dimensão

| Dimensão | Onde é capado | Comportamento ao limite | Preço excedente |
|---|---|---|---|
| LLM tokens/dia | Redis (token_budget_service) | HTTP 429 / exception | N/A (cap absoluto) |
| LLM tokens/mês | AiCreditsBalance.monthly_limit | HTTP 402 se overage_allowed=False | overage_rate_cents (= 0 no seed) |
| Pearch credits | company_plan_configs.pearch_credits_monthly | SEM GATE (só metering) | pearch_credit_price_cents (= 0 no seed) |
| Apify credits | company_plan_configs.apify_credits_monthly | SEM GATE (só metering) | apify_credit_price_cents (= 0 no seed) |
| Seats (usuários) | ClientAccount.user_limit | HTTP 402 | N/A |
| Vagas ativas | plan_limits_service (DEPRECIADO) | HTTP 402 | N/A |
| Custom agents | quota_enforcement.py | HTTP 402 | N/A |

**GAP CRITICO:** Pearch e Apify têm metering (registram consumo) mas NAO têm
gate computacional — o sistema não bloqueia quando o cap mensal é atingido.
O Token Budget (LLM) tem gate implementado. ACAO: implementar gate Pearch/Apify.

### 4.3 Overage: colunas prontas, preços a definir

As colunas existem no schema mas estão zeradas no seed:

```
# company_plan_configs — todos os planos atualmente têm:
embedding_overage_price_cents = 0   # PENDENTE definição
llm_overage_price_cents       = 0   # PENDENTE definição
pearch_credit_price_cents     = 0   # PENDENTE definição
apify_credit_price_cents      = 0   # PENDENTE definição
```

Exceção — `agent_execution_price_cents` (overage de execuções de agentes) JÁ definido:
```
starter: 40 centavos/execução | pro: 30 centavos | enterprise: 20 centavos
```

**Para completar o modelo de overage:**
1. Definir preços com Paulo, criar migration de update
2. Implementar gate computacional para Pearch e Apify
3. Setar `overage_allowed=True` nos planos que devem cobrar excedente

---

## 5. DESCONTO ALFA (B6 — IMPLEMENTADO)

### 5.1 O que foi implementado

Feature concluída em commit `59dbdcd0d`.

**Backend:**
- Coluna `desconto_pct NUMERIC(5,2)` na tabela `subscriptions` (migration 294)
- Coluna `desconto_validade TIMESTAMP` na tabela `subscriptions`
- Endpoint `PATCH /api/v1/admin-api/subscription/{company_id}/discount`
  - Auth: `INTERNAL_API_TOKEN` (Bearer, machine-to-machine)
  - Payload: `{ "desconto_pct": float [0-100], "desconto_validade": "ISO8601 | null" }`
  - `desconto_pct=0` remove o desconto
- GET `/api/v1/billing/my-plan-summary` expõe desconto quando ativo:
  ```json
  {
    "data": {
      "plan_name": "Starter",
      "desconto": {
        "pct": 50.0,
        "validade": "2026-12-31T23:59:59"
      }
    }
  }
  ```

**Regras de negócio:**
- Admin WeDOTalent aplica via painel interno (endpoint `/admin-api/`)
- Desconto so aparece no response se `desconto_pct > 0`
- Sem expiracao = desconto permanente ate novo PATCH
- Frontend deve exibir badge "Desconto ALFA X%" na sub-tab Plano

### 5.2 O que o desconto NAO faz ainda

`desconto_pct` é atualmente um campo informativo — é exibido na UI mas NAO há
lógica de billing que o aplique automaticamente à geração de faturas.

**Para completar:** implementar em `BillingService.calculate_invoice()`:
```python
if subscription.desconto_pct > 0:
    price = base_price * (1 - subscription.desconto_pct / 100)
```

---

## 6. ARQUITETURA DO CÓDIGO DE BILLING

### 6.1 Mapa de arquivos

```
lia-agent-system/
  libs/models/lia_models/
    billing.py                  -- Subscription model (com desconto_pct/validade)
    plan_config.py              -- CompanyPlanConfig model (caps + pricing)
    ai_consumption.py           -- AiConsumption + AiCreditsBalance models

  app/domains/billing/
    services/
      billing_service.py        -- BillingService principal
      consumption_tracking_service.py  -- record_apify_call, record_pearch_call, record_llm_call
      consumption_report_service.py    -- relatórios de consumo

  app/domains/credits/
    services/
      credit_service.py         -- ACTION_CREDIT_COSTS (fonte de verdade de custos)
      token_budget_service.py   -- cap diário Redis + observabilidade LLM

  app/services/
    quota_enforcement.py        -- gates de agentes/campaigns/digital_twins

  app/api/v1/
    billing.py                  -- endpoints cliente-facing (my-plan-summary, my-usage-summary)
    admin_plan_api.py           -- endpoints admin (subscription, usage, discount)
    ai_consumption.py           -- metering técnico tokens + overage enforcement

  alembic/versions/
    292_add_company_plan_configs.py  -- cria tabela + seed dos 4 planos
    293_update_plan_seats.py         -- atualiza max_seats: pro=10, enterprise=15
    294_add_desconto_alfa_*.py       -- adiciona desconto_pct/validade ao Subscription
```

### 6.2 Endpoints canônicos

**Endpoints cliente-facing (JWT obrigatório):**

| Método | Path | O que retorna |
|---|---|---|
| GET | `/api/v1/billing/my-plan-summary` | Plano atual, seats, caps, features, desconto ALFA |
| GET | `/api/v1/billing/my-usage-summary` | Consumo do período: tokens, créditos, execuções |
| GET | `/api/v1/billing/usage-history` | Histórico de consumo por período |
| GET | `/api/v1/billing/invoices` | Faturas |

**Endpoints admin (INTERNAL_API_TOKEN):**

| Método | Path | Função |
|---|---|---|
| GET | `/api/v1/admin-api/subscription/{cid}` | Plano + features + quotas do tenant |
| GET | `/api/v1/admin-api/usage/{cid}` | Consumo período atual |
| POST | `/api/v1/admin-api/usage/{cid}/record` | Registrar consumo externo |
| PUT | `/api/v1/admin-api/subscription/{cid}/plan` | Mudar plano |
| PATCH | `/api/v1/admin-api/subscription/{cid}/discount` | Aplicar/remover desconto ALFA |

Contratos documentados em: `lia-agent-system/docs/admin-integration-contract.md`

---

## 7. FRONTEND — PLANO E COBRANÇA

### 7.1 Estrutura implementada

Hub "Plano e Cobança" em `plataforma-lia/src/components/settings/`:

```
PlanoBillingHub (ex-ConsumoHub, renomeado commit 24d2d21cc)
  Sub-tab: Plano     -- plano atual, features, add-ons, badge de desconto ALFA
  Sub-tab: Consumo   -- graficos de uso IA + Pearch + Agentes + Apify
  Sub-tab: Faturas   -- historico + PDF + NF-e
  Sub-tab: Cobrança  -- dados fiscais + meio de pagamento
```

Sidebar renomeada de "Consumo" para "Plano e Cobrança" (commit 9205e5156).

### 7.2 Hooks e componentes relevantes

```
plataforma-lia/src/
  hooks/billing/
    usePlan.ts              -- lê my-plan-summary, expõe isEnterprise, feature flags
  components/settings/
    PlanoBillingHub.tsx     -- hub principal (4 sub-tabs)
    BillingTab.tsx          -- sub-tab Plano (badge desconto ALFA aqui)
    ConsumoTab.tsx          -- sub-tab Consumo (adicionar estimativa WhatsApp aqui)
```

### 7.3 Exibição do desconto ALFA

Quando `data.desconto.pct > 0` no response de `/my-plan-summary`, a sub-tab Plano
exibe badge: "Desconto ALFA: 50% OFF" (ou o valor real do pct).

Badge implementado (commit B6). PENDENTE: lógica de cálculo do preço efetivo —
exibe o pct mas não calcula `assinatura * (1 - pct/100)`.

---

## 8. DIAGNÓSTICO COMERCIAL — PROPOSTA SODEXO

> Esta seção documenta decisões e insights derivados da análise da proposta
> Proposta_Comercial&Parceria_WeDOTalent&Sodexo_20032026.pdf (28 páginas).
> Sessão de análise: 2026-06-23.

### 8.1 Estrutura da proposta

- Fase 1 (meses 1-3): validação gratuita. Sem faturamento, sem SLA formal.
- Fase 2 (mês 4+): comercial ALFA. R$2.500/mês fixo + variáveis.
- Vigência contratual: 12 meses com renovação automática (Cláusula 3.1/3.2).
- Ticket regular (não-ALFA): R$5.000/mês para o mesmo perfil de cliente.

### 8.2 Inconsistências críticas (BLOCKERS antes de assinar)

| # | Cláusula | Problema | Ação |
|---|---|---|---|
| IC-1 | Anexo I | Valores de assinatura como "0" — placeholder não preenchido | Preencher R$2.500 ALFA / R$5.000 regular |
| IC-2 | 4.10(b/c) | Desconto definido como "0%" no contrato vs "50%" na narrativa | Substituir "0%" por "50% (cinquenta por cento)" |
| IC-3 | 4.1 | Fase de Validação por "x meses" — prazo em aberto | Definir "3 (três) meses" |
| IC-4 | 6.2 | Multa por uso indevido definida como "R$ x" | Definir valor (sugestão: R$50.000) |

### 8.3 Análise de margem (caso Sodexo ALFA, ~300 candidatos/mês, 5 recrutadores)

```
RECEITA
  Assinatura ALFA ........................ R$ 2.500
  (LLM negociado como pass-through para tier ALFA)

CUSTO VARIAVEL (WeDOTalent paga)
  LLM Anthropic (estimado)
    30 contratados * R$3,02/candidato ....   R$  91
    270 recusados * R$1,18/candidato .....   R$ 319
    Subtotal LLM .........................   R$ 410
  Pool Global (Pearch + Apify)
    300 candidatos * $0,36 * R$5,20 .....   R$ 562
  Voice screening (5% das triagens, VoIP)
    ~15 sessões * R$0,34/sessão .........   R$   5
  TOTAL CUSTO VARIAVEL ................... R$ 977

INFRAESTRUTURA (estimativa mensal)
  PostgreSQL (shared tenant) .............   R$  80
  Redis ..................................   R$  30
  Compute uvicorn/Next.js ................   R$ 150
  Storage (CVs, docs) ....................   R$  25
  Monitoring/logs ........................   R$  45
  Email (Mailgun) ........................   R$  20
  Backup .................................   R$  30
  TOTAL INFRA ............................   R$ 380

MARGEM BRUTA ESTIMADA = R$2.500 - R$977 - R$380 = R$1.143 (46%)
```

Nota: WhatsApp fora do COGS — custo do cliente Sodexo, não da WeDOTalent.
BYOK ativo reduziria o custo LLM significativamente.
Voice com Twilio PSTN (ligação telefônica): ~R$32-124/mês adicional.

### 8.4 Caps protegem margem LLM

O argumento "consumo pode explodir e destruir margem" é PARCIALMENTE INCORRETO:

- LLM tem cap mensal (llm_monthly_cap) + cap por request (llm_request_ceiling)
  → sistema BLOQUEIA (HTTP 402) quando atingido. Margem LLM protegida.
- Pearch e Apify têm caps no modelo mas SEM gate computacional
  → consumo pode ultrapassar quota sem bloqueio. RISCO REAL.
- WhatsApp: custo do cliente, fora do escopo de proteção de margem WeDOTalent.

### 8.5 Riscos jurídicos materiais

| Risco | Cláusula | Severidade | Ação recomendada |
|---|---|---|---|
| Vigência indefinida | 1 | P0 | Preencher prazo antes de assinar |
| Responsabilidade sem receita na Fase 1 | 7.2 | P1 | Excluir Fase 1 do regime de responsabilidade |
| Marco Legal da IA (PL não aprovado) | 10.19 | P1 | Substituir por cláusula de adaptação pós-aprovação |
| WhatsApp: sanção cai sobre Sodexo | 10 | P1 | Adicionar obrigação WeDO de validar templates |
| Não-concorrência assimétrica | 11 | P2 | Adicionar reciprocidade |
| Confidencialidade sem proibição de uso derivativo | 15 | P2 | Adicionar cláusula de não-uso derivativo 24 meses |

### 8.6 Benchmarks de mercado (atualizado 2026-06-23)

> Pesquisa expandida com 15+ concorrentes — ver seção 13.2 para tabela completa com fontes.

| Produto | Ticket médio | Seats | IA nativa | Fonte |
|---|---|---|---|---|
| Eightfold AI | R$4.4M+/ano (10K emp.) | PEPM | Enterprise AI | christianandtimbers.com |
| Phenom | R$520K+/ano (mín.) | PEPM | Enterprise AI | christianandtimbers.com |
| HireVue | R$182K-754K/ano | — | Avançada | hirevue.com |
| SeekOut | R$104K/ano (mediana Vendr) | 3+ | Sourcing AI | vendr.com |
| hireEZ | R$68K/ano (mediana Vendr) | 3+ | Sourcing AI | vendr.com |
| Greenhouse | R$64K/ano (mediana Vendr) | PEPM | ATS+Sourcing | vendr.com |
| Lever | R$64K/ano (mediana Vendr) | PEPM | Conversacional | vendr.com |
| Fetcher | R$57K/ano (mediana Vendr) | 1-3 | Sourcing AI | vendr.com |
| SmartRecruiters | R$78K+/ano | — | ATS+AI | selectsoftwarereviews.com |
| Gupy | R$3K-R$15K/mês | 10 | Parcial | — |
| Kenoby | R$1,5K-R$5K/mês | 10 | Basica | — |
| **WeDOTalent regular** | **R$5K/mês (R$60K/ano)** | **5** | **LLM nativo** | — |
| **WeDOTalent ALFA** | **R$2,5K/mês (R$30K/ano)** | **5** | **LLM nativo** | — |

---

## 9. GAPS E TRABALHO PENDENTE

### 9.1 Gaps de código priorizados

| Prioridade | Gap | Arquivo | Ação |
|---|---|---|---|
| P0 | Gate computacional para Pearch/Apify (sem bloqueio ao atingir cap) | `consumption_tracking_service.py` | Implementar gate similar ao token_budget_service |
| P0 | `telefone_desbloqueio: 14` ausente em ACTION_CREDIT_COSTS | `credit_service.py:25` | Adicionar entry + test sentinel |
| P1 | `email_desbloqueio: 2` ausente em ACTION_CREDIT_COSTS | `credit_service.py:25` | Adicionar entry + test sentinel |
| P1 | Preços de overage zerados no seed (llm, pearch, apify) | `292_add_company_plan_configs.py` | Definir preços com Paulo e criar migration de update |
| P1 | `is_alfa_partner` flag ausente (LLM markup vs pass-through) | `Subscription` model | Adicionar coluna booleana; BillingService lê flag |
| P1 | `desconto_pct` não é aplicado em logica de faturamento | `billing_service.py` | Implementar `base_price * (1 - pct/100)` |
| P1 | Plano `alfa_base` não existe em `company_plan_configs` | migration 292 ou nova | Adicionar com valores alinhados à proposta Sodexo |
| P1 | Divergência de 1 crédito em Busca Padrão (proposta=3, código=2) | `credit_service.py` | Alinhar com decisão de produto |
| P2 | Card estimador de custo WhatsApp na sub-tab Consumo | `plataforma-lia/ConsumoTab.tsx` | Formula: `apify_credits * 2 * $0.0588 * taxa` |
| P2 | UI não calcula preço efetivo com desconto | `BillingTab.tsx` | `preco_efetivo = assinatura * (1 - desconto_pct/100)` |

### 9.2 Decisões de produto pendentes

1. Preço de overage para LLM, Pearch e Apify (colunas prontas em `company_plan_configs`)
2. Alinhamento do mapeamento de créditos — Busca Padrão é 3 créditos (proposta) ou 2 créditos (código)?
3. Caps do plano ALFA Sodexo — quantos seats? qual llm_monthly_cap? qual apify_credits_monthly?
4. Pass-through LLM para ALFA — via `is_alfa_partner` flag ou via `llm_price_per_1k_tokens_brl = custo`?

---

## 10. REGRAS DE DESENVOLVIMENTO

### 10.1 Ao alterar pricing/caps

1. Sempre editar `company_plan_configs` via nova migration Alembic (nunca UPDATE manual em prod)
2. Após mudar `company_plan_configs`, invalidar cache: `invalidate_tenant_context_cache(company_id)`
3. Atualizar `ACTION_CREDIT_COSTS` em `credit_service.py` e criar/atualizar teste sentinel em `tests/contract/test_admin_plan_api.py`
4. Checar se o frontend `usePlan.ts` precisa ser atualizado para refletir novo feature flag

### 10.2 Ao adicionar nova dimensão de consumo

1. Adicionar coluna em `company_plan_configs` (cap mensal + preço overage)
2. Adicionar função `record_<nova_dimensao>_call` em `consumption_tracking_service.py`
3. Adicionar gate computacional em `ai_consumption.py` ou serviço dedicado
4. Expor via `GET /api/v1/billing/my-usage-summary` e `GET /api/v1/admin-api/usage/{cid}`

### 10.3 Multi-tenancy — regra absoluta

`company_id` NUNCA vem do payload. Sempre do JWT via `Depends(require_company_id)`.
Qualquer leitura/escrita de billing usa `company_id` como filtro obrigatório.
Ver: `CLAUDE.md` secao "REGRA 2 — company_id PROIBIDO no request payload".

### 10.4 Autenticação dos endpoints admin

Os endpoints `/admin-api/*` usam `INTERNAL_API_TOKEN` (Bearer header, env var).
NUNCA expor esses endpoints sem autenticação. São chamados pelo painel admin
WeDOTalent (admin2.wedotalent.cc), não pelo cliente final.

---

## 11. PLANILHA CONSOLIDADA — TODOS OS PLANOS

> Referência única para projeções e exportação para Excel.
> Valores confirmados no código (migrations 292+301) + estimativas operacionais calculadas.
> Coluna "Base" indica se o valor é fixo no DB ou estimado.

| Categoria | Dimensão | Base | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|---|---|
| **LIMITES TÉCNICOS** | Usuários (seats) | DB | 2 | 5 | 10 | 15 |
| | Cap LLM mensal (tokens) | DB | 500.000 | 2.000.000 | 10.000.000 | 40.000.000 |
| | Cap LLM por request (tokens) | DB | 2.000 | 2.000 | 10.000 | 50.000 |
| | Cap embedding mensal (tokens) | DB | 10.000.000 | 50.000.000 | 200.000.000 | 500.000.000 |
| | Créditos Pearch/mês | DB | 200 | 500 | 1.500 | 4.000 |
| | Rollover Pearch | DB | N | N | N | S |
| | Créditos Apify/mês | DB | 200 | 500 | 1.500 | 4.000 |
| | Rollover Apify | DB | N | N | N | S |
| | Execuções de agentes/mês | DB | 50 | 200 | 1.000 | 5.000 |
| | Agentes customizados | DB | 1 | 2 | 10 | 50 |
| | Agentes de sourcing | DB | 1 | 1 | 5 | 20 |
| | Vagas/campanhas ativas | DB | 0 | 0 | 5 | 20 |
| | Digital twins | DB | 0 | 0 | 0 | 10 |
| | BYOK habilitado | DB | S | S | S | S |
| | Trial (dias) | DB | 30 | — | — | — |
| **SOURCING ESTIMADO** | Créditos Pearch/mês (pool busca) | DB | 200 | 500 | 1.500 | 4.000 |
| (2 pools separados) | Buscas no pool global (÷ 2 créditos/busca) | Est. | ~100 | ~250 | ~750 | ~2.000 |
| | Candidatos encontrados/mês (× 20/busca) | Est. | ~2.000 | ~5.000 | ~15.000 | ~40.000 |
| | Créditos Apify/mês (pool reveal) | DB | 200 | 500 | 1.500 | 4.000 |
| | **Candidatos com email revelado/mês** (sob demanda) | Est. | **até 200** | **até 500** | **até 1.500** | **até 4.000** |
| **INTELIGÊNCIA IA ESTIMADA** | Triagens de candidatos/mês | Est. | ~125 | ~500 | ~2.500 | ~10.000 |
| | Consultas no chat LIA/mês | Est. | ~500 | ~2.000 | ~10.000 | ~40.000 |
| | Geração de JDs/mês | Est. | ~62 | ~250 | ~1.250 | ~5.000 |
| | Parsings de CV/mês | Est. | ~200 | ~800 | ~4.000 | ~16.000 |
| **WHATSAPP CLIENTE** | Conversas estimadas/mês | Est. | ~400 | ~1.000 | ~3.000 | ~8.000 |
| | Custo WhatsApp cliente (R$/mês) | Est. | ~R$122 | ~R$305 | ~R$915 | ~R$2.440 |
| **PREÇOS DE EXCEDENTE** | Excedente agentes (R$/execução) | DB | — | R$0,40 | R$0,30 | R$0,20 |
| | Excedente LLM (R$/1K tokens) | Pendente | — | — | — | — |
| | Excedente Pearch (R$/crédito) | Pendente | — | — | — | — |
| | Excedente Apify (R$/crédito) | Pendente | — | — | — | — |
| **REFERÊNCIA DE CUSTOS** | Custo LLM Anthropic (claude-3-sonnet input) | Ref. | $0,003/1K | $0,003/1K | $0,003/1K | $0,003/1K |
| | Custo LLM Anthropic (claude-3-sonnet output) | Ref. | $0,015/1K | $0,015/1K | $0,015/1K | $0,015/1K |
| | Custo Pearch (busca) | Ref. | $0,12 USD | $0,12 USD | $0,12 USD | $0,12 USD |
| | Custo Apify (enriquecimento) | Ref. | $0,01 USD | $0,01 USD | $0,01 USD | $0,01 USD |
| | Custo por candidato processado (Pearch+Apify) | Ref. | $0,34 USD | $0,34 USD | $0,34 USD | $0,34 USD |
| | Custo WhatsApp Meta por conversa | Ref. | $0,0588 USD | $0,0588 USD | $0,0588 USD | $0,0588 USD |
| **EMBEDDINGS** | Cap mensal (tokens) | DB | 10.000.000 | 50.000.000 | 200.000.000 | 500.000.000 |
| (Gemini text-embedding-004 | Embeddings geradas/mês (est.) | Est. | ~1.100 | ~4.250 | ~20.750 | ~82.000 |
| fallback: OpenAI | Tokens estimados/mês | Est. | ~1,6M | ~6,4M | ~31M | ~123M |
| text-embedding-3-small) | % do cap utilizado | Est. | ~16% | ~13% | ~16% | ~25% |
| | **Custo Gemini** (text-embedding-004) | Ref. | GRATUITO | GRATUITO | GRATUITO | GRATUITO |
| | Custo OpenAI fallback (text-emb-3-small) | Ref. | $0,02/M tok. | $0,02/M tok. | $0,02/M tok. | $0,02/M tok. |
| | **COGS embeddings/mês** | Est. | ~R$0 | ~R$0 | ~R$0 | ~R$13 |
| **TRIAGEM POR VOZ** | Disponível no plano | Policy | ✅ todos | ✅ todos | ✅ todos | ✅ todos |
| (WSI candidato — 2 pipelines) | Cap diário (policy.py `max_voice_screenings_per_day`) | Policy | 20/dia | 20/dia | 20/dia | 20/dia |
| | Cap mensal estimado (× 30 dias) | Est. | ~600 | ~600 | ~600 | ~600 |
| | Sessões estimadas/mês (5% das triagens) | Est. | ~6 | ~25 | ~125 | ~500 |
| | Duração típica/sessão | Ref. | ~15 min | ~15 min | ~15 min | ~15 min |
| | **Pipeline 1: Gemini Live Audio (VoIP browser)** | Ref. | — | — | — | — |
| | Custo Gemini 2.5 Flash/sessão (STT+LLM+TTS nativo) | Ref. | **~R$0,34** | **~R$0,34** | **~R$0,34** | **~R$0,34** |
| | **Pipeline 2: Twilio PSTN (ligação telefônica)** | Ref. | — | — | — | — |
| | Twilio ($0,05-0,10/min × 15 min) | Ref. | R$3,90-7,80 | R$3,90-7,80 | R$3,90-7,80 | R$3,90-7,80 |
| | Gemini STT + LLM + OpenAI TTS | Ref. | ~R$0,47 | ~R$0,47 | ~R$0,47 | ~R$0,47 |
| | Custo total Twilio pipeline/sessão | Ref. | **~R$2,13-8,27** | **~R$2,13-8,27** | **~R$2,13-8,27** | **~R$2,13-8,27** |
| | **COGS triagem voz/mês (Gemini Live VoIP)** | Est. | **~R$2** | **~R$9** | **~R$43** | **~R$170** |
| | COGS triagem voz/mês (Twilio PSTN, rate negociado) | Est. | ~R$13 | ~R$53 | ~R$266 | ~R$1.065 |
| | COGS triagem voz/mês (Twilio PSTN, rate padrão) | Est. | ~R$50 | ~R$207 | ~R$1.034 | ~R$4.135 |
| **AGENT STUDIO VOICE** | Feature incluída no plano | DB | ❌ | ❌ | ✅ | ✅ |
| (agentes customizados | Gate: `voice_screening_v2_enabled` per-tenant | Code | — | — | WeDOTalent ativa | WeDOTalent ativa |
| com canal de voz) | Custo: mesmo modelo Gemini Live (VoIP) ou Twilio (PSTN) | Ref. | — | — | R$0,34-8,27/sessão | R$0,34-8,27/sessão |
| **CUSTOS VARIÁVEIS** | Custo LLM/triagem candidato contratado (~6K tokens) | Est. | R$3,02 | R$3,02 | R$3,02 | R$3,02 |
| (WeDOTalent paga) | Custo LLM/triagem candidato recusado (~2.4K tokens) | Est. | R$1,18 | R$1,18 | R$1,18 | R$1,18 |
| | Custo Pearch/busca | Ref. | R$0,62 | R$0,62 | R$0,62 | R$0,62 |
| | Custo Apify/candidato processado | Ref. | R$0,05 | R$0,05 | R$0,05 | R$0,05 |
| | COGS/candidato processado (Pearch amortizado + Apify, sem triagem LLM) | Est. | ~R$0,08 | ~R$0,08 | ~R$0,08 | ~R$0,08 |
| **INFRAESTRUTURA EST.** | PostgreSQL (RDS t3.medium) | Est. | ~R$80 | ~R$80 | ~R$80 | ~R$80 |
| (por tenant/mês, | Redis ElastiCache (t3.micro) | Est. | ~R$30 | ~R$30 | ~R$30 | ~R$30 |
| não varia por plano) | Compute EC2/ECS (FastAPI + workers) | Est. | ~R$150 | ~R$150 | ~R$150 | ~R$150 |
| | Storage S3 (CVs, JDs, logs) | Est. | ~R$25 | ~R$25 | ~R$25 | ~R$25 |
| | Monitoring + Observability | Est. | ~R$45 | ~R$45 | ~R$45 | ~R$45 |
| | Email transacional (SES/SendGrid) | Est. | ~R$20 | ~R$20 | ~R$20 | ~R$20 |
| | Backup e transferência de dados | Est. | ~R$30 | ~R$30 | ~R$30 | ~R$30 |
| | **TOTAL infra/tenant/mês** | Est. | **~R$380** | **~R$380** | **~R$380** | **~R$380** |
| **MODELO DE MARGEM** | Receita mensal (Sodexo ALFA Fase 2) | Ref. | R$2.500 | — | — | — |
| (caso Sodexo ALFA, | COGS LLM triagens (~750 triagens × R$1,30 médio) | Est. | ~R$975 | — | — | — |
| ~300 cand/mês, 5 seats) | COGS Pearch + Apify (~300 candidatos processados) | Est. | ~R$53 | — | — | — |
| | COGS total | Est. | ~R$1.028 | — | — | — |
| | Infraestrutura/tenant | Est. | ~R$380 | — | — | — |
| | Margem bruta (sem infra) | Est. | R$1.472 (59%) | — | — | — |
| | **Margem líquida (com infra)** | Est. | **R$1.092 (44%)** | — | — | — |

> **⚠️ Gaps de pricing identificados (resolver antes de assinar contratos ALFA):**
> - **P1a** `pearch_search = 2 créditos` no código vs. proposta = 3 → diferença de R$0,31/busca.
>   Arquivo: `lia-agent-system/app/shared/billing/credit_service.py` → dict `ACTION_CREDIT_COSTS`
> - **P1b** `email_desbloqueio` ausente em `ACTION_CREDIT_COSTS` → cobrança de desbloqueio de email não contabilizada
> - **P1c** `telefone_desbloqueio` ausente em `ACTION_CREDIT_COSTS` → idem para telefone
> - **P2** Flag `is_alfa_partner` inexistente → clientes ALFA recebem markup 3x no LLM em vez de pass-through.
>   Arquivo: `billing.py` → precisa de `if subscription.is_alfa_partner: aplicar_custo_sem_markup()`
> - **P3** Linguagem da proposta usa "por candidato" vs. sistema cobra "por token" — alinhar linguagem antes de assinar contrato
> - **P4** Infraestrutura (~R$380/tenant/mês) não estava incluída na proposta Sodexo → margem real 44%, não 59%
> - **P5** ~~CRÍTICO~~ **RECLASSIFICADO → P2** após investigação de custo real (2026-06-23). Triagem por voz WSI é disponível para TODOS os planos via `policy.py`. Custos reais: **Gemini Live (VoIP browser) = R$0,34/sessão** | **Twilio PSTN = R$2,13-8,27/sessão**. COGS mensal aceitável (ver seção 11 corrigida). A estimativa anterior de R$94/sessão usava preços de OpenAI Realtime API — o código real usa Gemini 2.5 Flash com TTS nativo (`gemini_live_audio_service.py`), 28× mais barato. Voice pode ser incluído nos planos com margem positiva. Oportunidade: cobrar R$5-10/sessão extra-plano com margem 40-93%. Cap continua em `policy.py` por setor (padrão 20/dia). Nota: `voice_screening` feature_flag em plan_configs é exclusivamente para **Agent Studio voice** (agentes customizados com canal de voz) — esse sim é Pro+ only.

> **Legenda base:** DB = valor fixo no banco (migration 292/301), confirmado por código.
> Est. = estimativa calculada a partir dos caps do DB. Pendente = decisão de produto pendente.
> Ref. = custo de fornecedor externo (não é receita WeDOTalent).
>
> **Fórmulas usadas nas estimativas:**
> - Buscas Pearch = pearch_credits / 2
> - Candidatos encontrados = buscas × 20 (default da API, máx 50)
> - Candidatos processados = apify_credits (1 crédito/candidato com email)
> - Triagens = llm_monthly_cap / 4.000 tokens
> - Chat queries = llm_monthly_cap / 1.000 tokens
> - JDs = llm_monthly_cap / 8.000 tokens
> - Parsings = llm_monthly_cap / 2.500 tokens
> - Conversas WhatsApp = apify_credits × 2
> - Custo WhatsApp = conversas × $0,0588 × R$5,20
> - Embeddings/mês = (triagens × 3) + (chat × 1) + (JDs × 2) + (sourcing × 1)  — média 1.500 tokens/embedding
> - Custo embedding Gemini text-embedding-004: GRATUITO (sem cobrança por token)
> - Custo embedding OpenAI fallback: $0,02/M tokens × tokens_estimados × R$5,20
> - Voice COGS Gemini Live (VoIP browser): sessões × $0,065/sessão × R$5,20 = ~R$0,34/sessão (fonte: `gemini_live_audio_service.py:18`)
> - Voice COGS Twilio PSTN: sessões × ($0,05-0,10/min × 15 min + $0,09 STT/LLM/TTS) × R$5,20 = R$2,13-8,27/sessão
> - Voice sessões estimadas: 5% das triagens do plano (estimativa conservadora de adoção)
> - Nota (2026-06-23): estimativa anterior usava OpenAI Realtime API (~$18/sessão = R$94). Código real usa Gemini 2.5 Flash com TTS nativo, 28× mais barato.
> - Custo LLM/triagem contratado: 6.000 tokens × (input $0,003 + output $0,015)/1K × R$5,20 = R$3,02
> - Custo LLM/triagem recusado: 2.400 tokens × mesma fórmula = R$1,18
> - COGS/candidato processado (sem triagem): R$0,62/20 cand. (Pearch amortizado) + R$0,05 Apify ≈ R$0,08
> - Infra por tenant: estimativa para tenant ativo com ~300 cand/mês (não varia por plano)

---

## 12. CAPACIDADE DE VAGAS POR PLANO

> Responde: **"Quantas vagas eu consigo conduzir por mês em cada plano?"**
>
> O cap determinante é o `llm_monthly_cap`. Cada vaga consome tokens em 4 operações:

| Operação | Tokens | Frequência |
|---|---|---|
| JD creation/enrichment | ~8.000 | 1× por vaga |
| WSI setup (geração de perguntas) | ~4.000 | 1× por vaga |
| Triagem por candidato (parse CV + score) | ~4.000 | N× por vaga |
| Chat recruiter sobre a vaga (est. 10 queries) | ~5.000 | 1× por vaga |
| **Total por vaga** | **17.000 + (N × 4.000)** | — |

### 12.1 Vagas conduzíveis por mês — por cenário de volume

| Cenário | Cand. triados/vaga | Tokens/vaga | Trial (500K) | Starter (2M) | Pro (10M) | Enterprise (40M) |
|---|---|---|---|---|---|---|
| Baixo volume (nicho, especializado) | 10 | ~57K | **~8 vagas** | **~35 vagas** | **~175 vagas** | **~700 vagas** |
| **Médio — padrão de mercado** | **20** | **~97K** | **~5 vagas** | **~20 vagas** | **~100 vagas** | **~412 vagas** |
| Alto volume (logística, varejo, ops) | 50 | ~217K | **~2 vagas** | **~9 vagas** | **~46 vagas** | **~184 vagas** |
| Muito alto volume (massa, 200 cand.) | 200 | ~817K | **~0,6 vagas** ⚠️ | **~2 vagas** | **~12 vagas** | **~49 vagas** |

> ⚠️ Trial com vaga de alto volume (50+ candidatos): 1-2 vagas esgotam o cap. Plano Trial é adequado apenas para testar o produto com vagas pequenas ou usar BYOK.

### 12.2 Constraint secundário — Apify (email reveal)

Se o recrutador revelar email de ~50% dos candidatos triados:

| Plano | Apify credits | Reveals (50% de N=20) | Vagas até esgotar Apify |
|---|---|---|---|
| Trial | 200 | 10/vaga | **~20 vagas** |
| Starter | 500 | 10/vaga | **~50 vagas** |
| Pro | 1.500 | 10/vaga | **~150 vagas** |
| Enterprise | 4.000 | 10/vaga | **~400 vagas** |

**Conclusão:** Apify só limita quando o recrutador revela email de MUITOS candidatos por vaga. No cenário médio (20 cand/vaga, 50% reveals), o LLM limita primeiro em Trial e Starter; no Pro, os dois convergem em ~100 vagas.

### 12.3 Tabela síntese — recomendação de plano por perfil de cliente

| Perfil do cliente | Vagas/mês típicas | Cand./vaga | Plano adequado | Bottleneck |
|---|---|---|---|---|
| Startup / MVP | 1–5 | 10–20 | Trial (teste) → Starter | LLM |
| PME crescimento | 5–20 | 15–30 | Starter | LLM |
| Empresa média | 20–100 | 20–50 | Pro | LLM |
| Enterprise / varejo | 50–200 | 50–200 | Enterprise | LLM + Apify |
| BPO / RPO (massa) | 200+ | 200+ | Enterprise + BYOK | BYOK obrigatório |

### 12.4 Impacto do BYOK na capacidade

Com BYOK ativo, o `llm_monthly_cap` do plano é substituído pelo limite da chave do cliente — na prática ilimitado para fins práticos. O sistema rastreia o consumo (LGPD/billing) mas não bloqueia.

| Plano | Vagas/mês sem BYOK (médio) | Vagas/mês com BYOK |
|---|---|---|
| Trial | ~5 | Ilimitado (rastreado) |
| Starter | ~20 | Ilimitado (rastreado) |
| Pro | ~100 | Ilimitado (rastreado) |
| Enterprise | ~412 | Ilimitado (rastreado) |

> **Implicação comercial:** BYOK é o upsell natural para clientes que precisam de mais vagas. O valor do plano muda de "cap de tokens" para "suporte + SLA + features" quando BYOK está ativo.

---

## 13. DIAGNÓSTICO DE PRICING — CUSTOS × MERCADO × MARGENS

> **Data da análise:** 2026-06-23
> **Objetivo:** cruzar custos reais do código com preços de concorrentes para determinar
> o preço-alvo de cada plano, markups recomendados e modelo de pricing ideal.
> **Status:** diagnóstico apenas — nenhum preço foi alterado no código.

### 13.1 COGS por plano (cenário médio: 20 candidatos/vaga)

Custo real que a WeDOTalent paga para entregar o serviço a um tenant ativo.

| Componente | Trial (~5 vagas) | Starter (~20 vagas) | Pro (~100 vagas) | Enterprise (~400 vagas) |
|---|---|---|---|---|
| **LLM** (triagem + JD + chat) | R$133 | R$530 | R$2.650 | R$10.600 |
| **Pearch** (buscas, R$0,62/busca) | R$3 | R$12 | R$62 | R$248 |
| **Apify** (reveal 50% dos cand.) | R$3 | R$10 | R$50 | R$200 |
| **Voice** (Gemini Live, 5% triagens) | R$2 | R$9 | R$43 | R$170 |
| **Embeddings** (Gemini = grátis) | R$0 | R$0 | R$0 | R$0 |
| **Infra fixa** (Postgres+Redis+Compute+S3+etc.) | R$380 | R$380 | R$380 | R$380 |
| **COGS total** | **R$521** | **R$941** | **R$3.185** | **R$11.598** |
| COGS/seat | R$261 | R$188 | R$319 | R$116 |

> Fórmulas: LLM = vagas × (1,30 × cand/vaga + 1,12) tokens em R$. Pearch = vagas × R$0,62.
> Apify = vagas × 0,05 × cand × 50% reveal. Voice = 5% das triagens × R$0,34 (Gemini Live VoIP).
> Infra = R$380 fixo por tenant (não varia por plano).

### 13.2 Benchmark de concorrentes (conversão USD→BRL a R$5,20)

#### ATS + IA (plataformas comparáveis ao WeDOTalent)

| Concorrente | Modelo | Preço/seat/mês (R$) | ACV médio (R$) | Fonte |
|---|---|---|---|---|
| Manatal | Per-seat | R$78 | ~R$5K/ano | hiretruffle.com |
| Zoho Recruit | Per-seat | R$130-156 | ~R$9K/ano | selectsoftwarereviews.com |
| JazzHR | Flat | R$390/mês flat | ~R$5K/ano | selectsoftwarereviews.com |
| Lever | PEPM | R$36/employee | ~R$64K/ano (Vendr mediana) | pin.com, vendr.com |
| Greenhouse | Tiers | R$520/seat (mediana) | ~R$64K/ano (Vendr mediana) | pin.com, vendr.com |
| iCIMS | PEPM | R$31-47/employee | ~R$290K-3.3M/ano | christianandtimbers.com |
| SmartRecruiters | Flat tiers | R$6.500+/mês | ~R$78K+/ano | selectsoftwarereviews.com |

#### IA de sourcing puro (concorrentes parciais)

| Concorrente | Modelo | Preço/seat/mês (R$) | ACV médio (R$) | Fonte |
|---|---|---|---|---|
| hireEZ | Per-seat + créditos | R$878-1.300 | ~R$68K/ano (Vendr) | glozo.com, vendr.com |
| SeekOut | Per-seat + créditos | R$775 (Lite) | ~R$104K/ano (Vendr) | seekout.com, vendr.com |
| Fetcher | Per-seat + cand caps | R$775-3.375 | ~R$57K/ano (Vendr) | pin.com, vendr.com |
| Findem | Per-seat → per-hire | R$2.600 | ~R$31K/ano (est.) | herohunt.ai |
| Entelo/Rival | Per-seat | R$650-1.040 (est.) | ~R$62K/ano | findhrsoftware.com |

#### IA enterprise (faixa alta, referência de teto)

| Concorrente | Modelo | Preço | ACV típico (R$) | Fonte |
|---|---|---|---|---|
| Eightfold AI | PEPM | R$36-52/employee | R$4.4M+ (10K emp.) | christianandtimbers.com |
| Phenom | PEPM | R$36-68/employee | R$520K+/ano (mín.) | christianandtimbers.com |
| Paradox | Contrato enterprise | R$62K-2.6M/ano | Custom | paradox.ai (adquirida por Workday $1B) |
| HireVue | Contrato enterprise | R$182K-754K/ano | ~R$130/entrevista | hirevue.com |

#### Voice screening (pricing de referência)

| Concorrente | Preço/sessão (USD) | Preço/sessão (R$) | WeDOTalent custo real |
|---|---|---|---|
| PhoneScreen.AI | $4,00 | R$20,80 | **R$0,34 (VoIP)** |
| Rebecca AI | $4-8 | R$20,80-41,60 | **R$2,13-8,27 (PSTN)** |
| InterviewFlowAI | $0,99 | R$5,15 | — |
| HireVue | ~$25/entrevista | R$130 | — |

#### Modelo de AI credits (referência de mercado)

| Concorrente | Preço/crédito | O que 1 crédito faz | Fonte |
|---|---|---|---|
| Workable Agent | $0,69-0,90 | 1 candidato processado | workable.com |
| Intercom Fin AI | $0,99 | 1 conversa resolvida | intercom.com |
| Salesforce Agentforce | Custom | 1 ação completada | salesforce.com |
| Zendesk | $1,50-2,00 | 1 ticket resolvido | zendesk.com |

### 13.3 Preço recomendado por margem-alvo

Benchmark de margens brutas no mercado AI SaaS (fontes: ICONIQ, Bessemer, a16z):
- **SaaS tradicional:** 80-90% gross margin
- **AI SaaS 2024:** 41-50% gross margin (ICONIQ State of Cloud 2024)
- **AI SaaS 2025:** 45-52% gross margin (melhorando com otimização de inference)
- **AI SaaS 2026 target:** 55-65% gross margin (benchmark para escala)

| Margem-alvo | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|
| **50%** (piso aceitável) | R$0 | R$1.882 | R$6.370 | R$23.196 |
| **55%** (conservador) | R$0 | R$2.091 | R$7.078 | R$25.773 |
| **60%** (benchmark 2026) | R$0 | R$2.353 | R$7.963 | R$28.995 |
| **65%** (meta agressiva) | R$0 | R$2.689 | R$9.100 | R$33.137 |

**Preço por seat (margem 60%):**

| Plano | Preço total/mês | Preço/seat | USD equivalente | Referência de mercado |
|---|---|---|---|---|
| Trial | R$0 | — | — | Loss-leader (30 dias) |
| **Starter** | **R$2.353** | **R$471/seat** | ~$91/seat | ≈ Greenhouse mediana (R$520) |
| **Pro** | **R$7.963** | **R$796/seat** | ~$153/seat | Entre Greenhouse e hireEZ |
| **Enterprise** | **R$28.995** | **R$1.933/seat** | ~$372/seat | Abaixo de SeekOut/Findem |

### 13.4 Cenários de pricing comercial (arredondados)

| Cenário | Starter (5 seats) | Pro (10 seats) | Enterprise (15 seats) | Filosofia |
|---|---|---|---|---|
| **A — Conservador** | R$1.990/mês | R$6.990/mês | R$19.990/mês | Margem 53-58%, conquista market share |
| **B — Benchmark** | R$2.490/mês | R$8.990/mês | R$29.990/mês | Margem 62-66%, alinhado com mercado |
| **C — Premium** | R$2.990/mês | R$11.990/mês | R$39.990/mês | Margem 69-73%, posicionamento AI-first |

**Caso Sodexo ALFA (R$2.500/mês, 5 seats) = Cenário A com desconto ALFA:**
- Regular seria R$5.000 (cenário B) com 50% desconto ALFA
- Margem ALFA: 44% (aceitável para parceiro estratégico de validação)
- Margem regular (sem desconto): 72% (saudável)

### 13.5 Estratégia de markup recomendada

Para os campos `*_overage_price_cents` e `*_price_per_1k_tokens_brl` zerados no código:

| Componente | Custo WeDO (raw) | Markup sugerido | Preço ao cliente | Justificativa |
|---|---|---|---|---|
| **LLM tokens** (overage) | ~R$0,05/1K tokens | **3×** | R$0,15/1K tokens | PostHog 1.2× (transparente), Intercom 10-50× (value). 3× é sustentável |
| **Pearch busca** (overage) | R$0,62/busca (2 créd.) | **2×** | R$1,24/busca | hireEZ cobra ~R$1,30/crédito implícito |
| **Apify reveal** (overage) | R$0,05/candidato | **3×** | R$0,15/candidato | Volume alto compensa margem |
| **Embedding** (overage) | R$0/1K tokens (Gemini) | **N/A** | N/A | Gemini text-embedding-004 = gratuito |
| **Agent execution** (já definido) | Variável | — | 40¢/30¢/20¢ por tier | Já no código |
| **Voice screening** (sessão extra) | R$0,34 (VoIP) / R$2,13-8,27 (PSTN) | **5-15×** | R$5-10/sessão | PhoneScreen.AI R$21, Rebecca AI R$21-42. WeDO pode ser o mais barato |

**Implementação no código:**
```python
# Valores sugeridos para migration de UPDATE em company_plan_configs:
llm_overage_price_cents     = 15   # R$0,15/1K tokens (3× markup)
pearch_credit_price_cents   = 62   # R$0,62/crédito (1× = pass-through; ajustar se quiser 2×)
apify_credit_price_cents    = 15   # R$0,15/crédito (3× markup)
embedding_overage_price_cents = 0  # manter zero (Gemini é gratuito)
```

### 13.6 Voice screening — economia corrigida (2026-06-23)

**Correção importante:** a estimativa anterior de R$94/sessão estava baseada em OpenAI
Realtime API ($0,06/min input + $0,24/min output = ~$18/sessão). O código real usa
**Gemini 2.5 Flash com TTS nativo** (`gemini_live_audio_service.py`), que é **28× mais barato**.

**Dois pipelines no código:**

```
Pipeline 1 — Gemini Live Audio (VoIP, browser do candidato)
  Browser mic → [PCM 16kHz] → WebSocket → Gemini Live → [audio] → Browser speaker
  Custo: ~$0,065/sessão = R$0,34
  Fonte: gemini_live_audio_service.py:18 (modelo: gemini-2.5-flash, voz: Aoede)

Pipeline 2 — Twilio + Gemini STT + OpenAI TTS (ligação telefônica PSTN)
  Twilio → [μ-law 8kHz] → mulaw_to_wav → Gemini Flash STT → LLM → OpenAI TTS → Twilio
  Custo: $0,41-1,59/sessão = R$2,13-8,27
  Fonte: voice_screening_orchestrator.py:2-29
  Componentes: Twilio $0,05-0,10/min × 15 min + Gemini STT $0,01 + LLM $0,05 + OpenAI TTS $0,03
```

**Impacto no modelo de negócios:**
- Voice NÃO é armadilha de margem — é barato o suficiente para incluir nos planos
- Incluir no Starter (100 sessões VoIP/mês) = ~R$34 de COGS adicional
- Concorrentes cobram R$5-42/sessão → WeDOTalent pode cobrar R$5-10/sessão extra com margem 40-93%
- BYOK deixa de ser obrigatório para viabilidade econômica de voice

**Caps de voice por setor** (fonte: `policy.py` — varia por setor do tenant, não por plano):

| Setor | max_voice_screenings_per_day | Mensal estimado |
|---|---|---|
| default | 20 | ~600 |
| tech | 100 | ~3.000 |
| varejo | 500 | ~15.000 |
| logística | 1.000 | ~30.000 |
| saúde | 50 | ~1.500 |
| educação | 80 | ~2.400 |
| agro | 2.000 | ~60.000 |

### 13.7 Modelo de pricing recomendado — híbrido (base + consumo)

**Dados de mercado sobre modelos de pricing (2026):**
- **92% das empresas AI SaaS** usam modelo híbrido com componente de consumo (Bessemer VP)
- **126% de crescimento YoY** em modelos baseados em créditos (PricingSaaS 500 Index)
- **37% das empresas SaaS** usam pricing híbrido (GrowthUnhinged, up de 25%)
- **29% mantêm per-seat puro** (ainda dominante entre empresas >$150M ARR)
- Gartner projeta **40% do spend SaaS enterprise** em modelos usage/outcome até 2030

**Estrutura recomendada para WeDOTalent:**

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 1 — Base mensal fixa (assinatura)                   │
│  Cobre: seats + caps generosos + features do tier           │
│  Pricing: R$1.990-39.990/mês dependendo do plano            │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 2 — AI credits para excedente                       │
│  Quando o tenant ultrapassa o cap do plano:                 │
│  - LLM excedente: R$0,15/1K tokens (3× markup)             │
│  - Pearch excedente: R$1,24/busca (2× markup)              │
│  - Apify excedente: R$0,15/reveal (3× markup)              │
│  - Agent execution excedente: 40¢/30¢/20¢ (já no código)   │
│  Comportamento: overage_allowed=True cobra; =False bloqueia │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 3 — Add-ons opcionais                               │
│  - Voice screening extra: R$5-10/sessão                     │
│  - Digital twins: Enterprise-only (incluído)                │
│  - White-label: Enterprise-only (incluído)                  │
│  - BYOK: disponível em todos os planos (sem custo WeDO)     │
└─────────────────────────────────────────────────────────────┘
```

**Vantagens deste modelo:**
1. **CFO-friendly**: base previsível + excedente transparente
2. **Land & expand**: cliente começa no Starter, consome mais, paga excedente antes de fazer upgrade
3. **Infraestrutura pronta**: `company_plan_configs` já tem campos `*_overage_price_cents` — só popular
4. **Competitivo**: Workable Agent cobra R$3,60-4,70/candidato; WeDO cobra R$0,15/candidato em overage

### 13.8 Tendências de mercado relevantes para decisão

| Tendência | Dado | Fonte | Implicação WeDOTalent |
|---|---|---|---|
| AI comprime margens SaaS | 80-90% → 50-60% | HireFraction, a16z | Meta de 60% é realista, não agressiva |
| Platforms AI custam 68% mais | +68% vs non-AI | Adeptiq 2026 | Justifica premium sobre Gupy/Kenoby |
| ROI de recruiting AI | $4-6 por $1 investido | Christian & Timbers | Argumento de vendas: payback em 60-90 dias |
| Renovação ATS sobe 7-40%/ano | iCIMS 30-40%, Greenhouse 8-15% | TreeGarden, Pin | Desconto ALFA tempo-limitado + renovação com aumento |
| Hidden costs = +247% sobre preço base | Média do mercado | Adeptiq 2026 | WeDOTalent pode diferenciar com transparência |
| 50% das empresas >$50M ARR | adicionarão AI credits em 2026 | GrowthUnhinged | AI credits é o padrão emergente |
| AI agent pricing vai SUBIR | Diferente de chatbots que deflacionam | Ibbaka 2026 | Não sub-precificar execuções de agentes |

### 13.9 Resumo executivo do diagnóstico

**Posicionamento atual:**
- WeDOTalent a R$500/seat (Sodexo ALFA) está entre Greenhouse (R$520) e Lever (R$416)
- Margem ALFA 44% está abaixo do piso AI SaaS (50%) mas aceitável para parceiro estratégico
- Preço regular (R$1.000/seat sem desconto) é competitivo com hireEZ/SeekOut

**3 decisões pendentes:**
1. **Popularizar preços de overage** — campos existem zerados no código. Sugestão: LLM 15¢/1K, Pearch 62¢/créd, Apify 15¢/créd
2. **Definir preço-lista por plano** — Starter R$1.990-2.490, Pro R$6.990-8.990, Enterprise R$19.990-29.990
3. **Voice screening pricing** — incluir no plano (COGS baixo) ou cobrar R$5-10/sessão extra

**O que mudou com este diagnóstico:**
- Voice screening reclassificado de P0 (armadilha) para P2 (oportunidade) — custo real 28× menor que estimado
- Modelo híbrido (base + créditos) validado pelo mercado — 92% das empresas AI SaaS usam
- Margem de 60% é atingível com Starter a R$2.353 e Pro a R$7.963

---

*Documento gerado a partir do estado do código + análise da proposta Sodexo em 2026-06-23.*
*Seats atualizados via migration 301: pro=10, enterprise=15 (confirmado Paulo 2026-06-23).*
*Seção 13 (diagnóstico de pricing) adicionada em 2026-06-23 — pesquisa de 15+ concorrentes.*
*Próxima revisão recomendada: quando preços de overage forem definidos ou plano ALFA for criado.*
