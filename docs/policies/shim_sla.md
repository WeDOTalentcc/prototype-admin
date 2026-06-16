# Política — SLA de remoção para shims `RAILS-DEPRECATED`

**Versão:** 1.0
**Vigência:** desde 2026-04-17
**Owner:** Tech Lead Backend
**Referência:** AUDIT FINAL 2026-04 (item F10)

---

## 1. Contexto

Durante o handoff `lia-agent-system → ats-api-rails`, vários serviços de
`app/shared/services/*.py` e `app/shared/compliance/bias_audit_service.py` foram
marcados como `# RAILS-DEPRECATED` mas mantidos vivos como **shims** para
evitar breakage de callers internos enquanto o adapter `integrations_hub/rails_adapter`
não está totalmente coberto.

A ausência de SLA explícito permitia que esses shims envelhecessem indefinidamente.
Esta política define o ciclo de vida formal e o cabeçalho de marcação obrigatório.

---

## 2. Cabeçalho obrigatório

Todo shim recebe, no topo do módulo (antes dos imports), o bloco:

```python
# @deprecated since=YYYY-MM-DD
# @remove-after=YYYY-MM-DD            # 90 dias após `since` se 0 importadores
# @owner=<area>                       # ex.: backend-platform
# @replacement=<módulo/serviço de destino>
```

Esse bloco é validado pelo CI lint `scripts/check_shim_headers.py` (todo arquivo
contendo `RAILS-DEPRECATED:` deve conter `@deprecated since=`).

---

## 3. Regras de remoção

| Condição | Ação |
|----------|------|
| **0 importadores em produção há ≥ 90 dias** | shim é removido na próxima PR de housekeeping (responsabilidade do owner) |
| **≥ 1 importador em produção** | shim continua, mas owner deve abrir issue de migração para `integrations_hub/rails_adapter` |
| **Cabeçalho ausente** | CI lint falha — bloqueia merge |
| **`@remove-after` excedido com importadores ainda ativos** | shim escala para revisão de Tech Lead em sprint review |

---

## 4. Inventário canônico (2026-04-17)

Cabeçalho aplicado em **14 shims**:

| Arquivo | Replacement |
|---------|-------------|
| `app/shared/compliance/bias_audit_service.py` | `integrations_hub/rails_adapter::bias_audit` |
| `app/shared/services/early_warning_service.py` | `integrations_hub/rails_adapter::early_warning` |
| `app/shared/services/journey_intelligence_service.py` | `integrations_hub/rails_adapter::journey_intelligence` |
| `app/shared/services/pipeline_prediction_service.py` | `integrations_hub/rails_adapter::pipeline_prediction` |
| `app/shared/services/pipeline_velocity_service.py` | `integrations_hub/rails_adapter::pipeline_velocity` |
| `app/shared/services/recruiter_metrics_service.py` | `integrations_hub/rails_adapter::recruiter_metrics` |
| `app/shared/services/silver_medalist_service.py` | `integrations_hub/rails_adapter::silver_medalist` |
| `app/shared/services/affirmative_service.py` | `integrations_hub/rails_adapter::affirmative` |
| `app/shared/services/briefing_service.py` | `integrations_hub/rails_adapter::briefing` |
| `app/shared/services/plan_limits_service.py` | `integrations_hub/rails_adapter::plan_limits` |
| `app/shared/services/zero_touch_scheduling_service.py` | `integrations_hub/rails_adapter::zero_touch_scheduling` |
| `app/shared/services/analysis_service.py` | `integrations_hub/rails_adapter::analysis` |
| `app/shared/services/seed_service.py` | `integrations_hub/rails_adapter::seed` |
| `app/shared/services/explainability_service.py` | `integrations_hub/rails_adapter::explainability` |

Os 142 outros shims listados no diagnóstico original do plan referem-se a
re-exports puros (linha única `from app.x import y`) e estão fora deste SLA —
serão removidos em batch quando o `integrations_hub` cobrir 100% das chamadas.

---

## 5. Como adicionar/remover um shim

- **Adicionar:** copie o bloco de cabeçalho no topo do arquivo, ajuste `since`
  para a data atual e `remove-after` para `+90 dias`. Atualize a tabela acima.
- **Remover:** delete o arquivo, remova a linha da tabela e procure callers com
  `grep -rn "from app.shared.services.<nome> import" lia-agent-system/`.
