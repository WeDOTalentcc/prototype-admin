# ADR-030 — Dois sistemas de AI Credits

**Data:** 2026-05-24  
**Status:** Aceito  
**Contexto:** billing.py e ai_consumption.py usam o termo "ai_credits" causando confusão, mas servem propósitos distintos e intencionalmente separados.

## Decisão

Manter dois sistemas separados com nomenclatura e responsabilidade clara:

### Sistema 1: Créditos de Plano (plan credits) — `billing.py`

- **Unidade:** crédito de plano (abstrato, comprado pelo cliente em lote)
- **Tabelas:** `subscriptions`, `invoices`, `payment_methods` (billing domain)
- **Escopo:** billing, invoicing, plan limits, integração Iugu/Vindi
- **Para verificar limite de plano:** usar `billing.py` / `CreditService`

### Sistema 2: Tokens LLM (consumption tracking) — `ai_consumption.py`

- **Unidade:** token de LLM (concreto, granular por modelo e call)
- **Tabelas:** `ai_consumption`, `ai_credits_balance`
- **Escopo:** usage metering, rate limiting, overage enforcement
- **Para logar consumo de token:** usar `ai_consumption.py` / `record_consumption`

## Motivo para manter separados

Billing credits são adquiridos em lote e têm validade de plano — representam
o "envelope comercial" da relação com o cliente. Tokens LLM são granulares,
variam por modelo (GPT-4/Claude/Gemini) e por call — representam o consumo
técnico real. Sincronizar os dois criaria acoplamento desnecessário e acirraria
responsabilidades de domínio distintas (Finance/Billing vs AI/Infrastructure).

## Interface pública

| Necessidade | Use |
|-------------|-----|
| Verificar se cliente tem plano ativo | `billing.py` / `BillingRepository` |
| Verificar limite de tokens do plano | `get_plan_limit(plan_code)` em `token_budget_service.py` |
| Registrar consumo de LLM | `ai_consumption.py` / `/record` endpoint |
| Verificar saldo atual de tokens | `ai_consumption.py` / `/balance` endpoint |
| Emitir fatura | `billing.py` / invoicing endpoints |

## Ratchet anti-confusão

- `billing.py` documenta: `# SISTEMA: Créditos de Plano (plan credits) — ADR-030`
- `ai_consumption.py` documenta: `# SISTEMA: Tokens LLM (consumption tracking) — ADR-030`

## Consequências

- Nomes de variáveis/funções que hoje dizem `ai_credits` em billing devem ser
  prefixados `plan_credits_` quando forem criados novos (não renomear bulk —
  evitar breaking change). Backlog item.
- Renaming futuro de `AiCreditsBalance` → `TokenUsageBalance` reduz ambiguidade.
  Deferir até após migração frontend completa.
