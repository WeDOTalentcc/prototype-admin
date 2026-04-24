# FairnessGuard Layer 3 — Runbook Operacional

> **Status:** Ativado em produção em **2026-04-23**
> **Flag:** `FAIRNESS_LAYER3_ENABLED=true` em `lia-agent-system/.env`
> **Referência:** `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.2

---

## 1. O que muda quando a flag está `true`

### Antes (flag = `false`)
- FairnessGuard aplicava apenas:
  - **L1:** regex determinístico (19 categorias, 13 PT + 6 EN)
  - **L2:** dicionário de viés implícito (43 termos PT + EN)
- Proxies sutis que não batem regex nem termo literal (ex: `"prefiro alguém do bairro X"` como proxy para classe/raça) **passavam sem alerta**.

### Depois (flag = `true`)
- FairnessGuard aplica adicionalmente:
  - **L3:** classificação semântica via `claude-haiku-4-5-20251001`
- L3 **só é acionada para `HIGH_IMPACT_ACTIONS`** (rejeição, shortlist, wsi_score) — não para todas as chamadas
- Resultado de L3 é **cacheado no Redis por 1 hora** (chave derivada do texto + contexto)
- Se L3 falhar por exceção (API down, timeout), retorna `is_blocked=False, confidence=0.5` com `soft_warnings` — fallback lenient (L1+L2 continuam válidos)

### Escopo real da ativação
- `app/shared/compliance/fairness_guard.py` linhas 911-970 — código canônico
- Trigger interno: função `check_with_layer3()` chamada por `check()` quando action ∈ `HIGH_IMPACT_ACTIONS`
- Texto > 200 chars e Layers 1+2 tenham passado (`is_blocked=False` no L1+L2) — condição dos testes `test_sprint2_fairness_agent.py`

---

## 2. Métricas a monitorar por 7 dias

| Métrica | Alvo | Como medir | Ação se fora do alvo |
|---------|------|------------|----------------------|
| Custos Anthropic (claude-haiku-4-5) | < USD 5/dia | Dashboard billing Anthropic | Se > USD 10/dia: investigar cache miss rate, considerar aumentar TTL Redis |
| Cache hit rate Redis | > 60% | `redis-cli --stat` + contadores de `fairness_layer3:*` | Se < 40%: revisar chave de cache (collision?) ou aumentar TTL |
| Latência P95 `POST /api/v1/chat` em agentes de decisão | < 800 ms | APM / dashboard observability | Se > 1200 ms: considerar L3 só em ações assíncronas |
| Novos `soft_warnings` em `fairness_audit_log` | Não deve ter pico abrupto | `SELECT COUNT(*) FROM fairness_audit_log WHERE created_at > '2026-04-23' AND soft_warnings IS NOT NULL` | Se + 500%: revisar false positives do L3 |
| Erros de L3 (exceções capturadas) | < 1% | log `[FairnessGuard] Layer 3 skipped: ...` | Se > 5%: indica problema de conectividade Anthropic |

---

## 3. Rollback

Se qualquer métrica do §2 estourar consistentemente por 48h:

```bash
# SSH no Replit
ssh replit-wedo
# Editar .env
sed -i 's/^FAIRNESS_LAYER3_ENABLED=true$/FAIRNESS_LAYER3_ENABLED=false/' /home/runner/workspace/lia-agent-system/.env
grep FAIRNESS_LAYER3_ENABLED /home/runner/workspace/lia-agent-system/.env
# Deve retornar: FAIRNESS_LAYER3_ENABLED=false
```

Efeito imediato: próximas chamadas ao FairnessGuard usam apenas L1+L2 (comportamento anterior). Nenhum deploy necessário — o arquivo é lido runtime via `getattr(_settings, "FAIRNESS_LAYER3_ENABLED", False)`.

---

## 4. Testes automatizados

Os testes em `tests/test_sprint2_fairness_agent.py` cobrem ambos os estados:

```bash
# No Replit
cd /home/runner/workspace/lia-agent-system
python3 -m pytest tests/test_sprint2_fairness_agent.py -x
```

Cenários cobertos:
- `FAIRNESS_LAYER3_ENABLED=1` → `check_semantic()` é chamada
- `FAIRNESS_LAYER3_ENABLED` não definido → `check_semantic()` NÃO é chamada

---

## 5. Por que ativar em produção (trade-off documentado)

Baseado em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.2:

| Dimensão | L3 OFF (antes) | L3 ON (agora) |
|----------|----------------|---------------|
| Custo | USD 0 extra | ~USD 0.0001 por check (claude-haiku-4-5) |
| Latência | ~50 ms (regex + dict lookup) | +200-500 ms primeiro check, ~50 ms após cache |
| Escopo | Todas as checks | Só `HIGH_IMPACT_ACTIONS` |
| Cobertura de viés | L1 regex + L2 43 termos | + semântico — pega proxies sutis que L2 não detecta |
| Risco de falso-negativo | Maior | Menor |

Recomendação do `.env.production.example` (template oficial): `FAIRNESS_LAYER3_ENABLED=true  # [RECOMMENDED] in production`.

---

## 6. Responsáveis

- **Compliance/fairness:** revisar `soft_warnings` semanal + revisar custos mensal
- **Engenharia:** monitorar latência P95 + taxa de erro L3
- **DPO:** se `soft_warnings` indicarem padrão sistêmico de viés, escalação via `guardrails_block.yaml` seção `escalation`

---

*Runbook criado em 2026-04-23 | Próxima revisão: 2026-04-30 (7 dias após ativação)*
