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

Pearch e Apify são sempre pareados: toda vez que um candidato é adicionado a uma vaga,
o Apify roda automaticamente para revelar o email. A métrica operacional relevante para
o cliente é uma só: **candidatos processados/mês** (= créditos Apify, o gargalo real).

Pearch são as buscas no pool global (2 créditos/busca, retorna até 20 candidatos por busca)
— são a vitrine. Apify é o desbloqueio de contato (1 crédito/candidato) — é o que habilita
o candidato a ser trabalhado. Os caps são iguais em todos os planos por design.

| Dimensão | Base de cálculo | Trial | Starter | Pro | Enterprise |
|---|---|---|---|---|---|
| **Candidatos processados/mês** | apify_credits_monthly (1 crédito/candidato) | **200** | **500** | **1.500** | **4.000** |
| **Buscas no pool global** | pearch_credits / 2 créditos/busca × 20 candidatos/busca | ~2.000 encontrados | ~5.000 encontrados | ~15.000 encontrados | ~40.000 encontrados |
| **Rollover de créditos não usados** | pearch/apify_credits_rollover | N | N | N | S |

> "Candidatos processados" = adicionados à vaga com email revelado. As buscas Pearch
> retornam uma vitrine muito maior, mas só viram candidatos reais quando o Apify roda.
> Rollover Enterprise: créditos não usados acumulam para o mês seguinte.

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
  TOTAL CUSTO VARIAVEL ................... R$ 972

INFRAESTRUTURA (estimativa mensal)
  PostgreSQL (shared tenant) .............   R$  80
  Redis ..................................   R$  30
  Compute uvicorn/Next.js ................   R$ 150
  Storage (CVs, docs) ....................   R$  25
  Monitoring/logs ........................   R$  45
  Email (Mailgun) ........................   R$  20
  Backup .................................   R$  30
  TOTAL INFRA ............................   R$ 380

MARGEM BRUTA ESTIMADA = R$2.500 - R$972 - R$380 = R$1.148 (46%)
```

Nota: WhatsApp fora do COGS — custo do cliente Sodexo, não da WeDOTalent.
BYOK ativo reduziria o custo LLM significativamente.

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

### 8.6 Benchmarks de mercado

| Produto | Ticket médio | Seats tier 2 | IA nativa |
|---|---|---|---|
| HireVue | $35K-$100K/ano | — | Avançada |
| Gupy | R$3K-R$15K/mês | 10 | Parcial |
| Fetcher.ai | $3K-$8K/mês | 10 | Sourcing |
| Lever | $30K-$80K/ano | 15 | Conversacional |
| **WeDOTalent regular** | **R$5K/mês** | **5** | **LLM nativo** |
| **WeDOTalent ALFA** | **R$2,5K/mês** | **5** | **LLM nativo** |
| Kenoby | R$1,5K-R$5K/mês | 10 | Basica |

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

*Documento gerado a partir do estado do código + análise da proposta Sodexo em 2026-06-23.*
*Seats atualizados via migration 293: pro=10, enterprise=15 (confirmado Paulo 2026-06-23).*
*Próxima revisão recomendada: quando preços de overage forem definidos ou plano ALFA for criado.*
