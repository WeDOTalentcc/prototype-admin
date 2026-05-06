# ADR-031 v2 — Protected Attributes Loader Path + Compliance Observability

**Status**: Accepted (supersedes ADR-031 v1 — proposed P0 was wrong premise; actual P0 was loader path bug)
**Data**: 2026-05-06
**Sprint**: Q2 Canonical Refactor (Sprint 1 — partial fix landed in commit `ca6f004cf`)
**Substitui**: ADR-031 v1 (Proposed P0 LGPD)

---

## Contexto — correção factual da v1

ADR-031 v1 alegou: **"`app/shared/config/protected_attributes.yaml` NÃO EXISTE em produção"** baseando-se em log error capturado. Diagnóstico estava parcialmente certo (havia P0 LGPD real) mas premissa da causa era errada.

**Realidade verificada** (auditoria E 2026-05-06 + investigação adicional Sprint 1D):

1. ✅ YAML **EXISTE** em `app/config/protected_attributes.yaml` (157 linhas, version 6, 12 atributos LGPD)
2. ❌ **Loader busca path errado**: `app/shared/compliance/protected_attributes.py:24-30` tinha **DUAS atribuições** de `_CONFIG_PATH`. A segunda (linha 28-30) sobrescrevia a primeira:

```python
# Linha 24-26: PRIMEIRA (correta) — resolve para app/config/
_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "config", "protected_attributes.yaml"
)

# Linha 28-30: SEGUNDA (broken — sobrescreve!) — resolve para app/shared/config/
_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "protected_attributes.yaml")
)
```

3. **Resultado em produção**: loader caía em `FileNotFoundError`, capturado por `except Exception`, retornava `{}`. Constants downstream (`PROTECTED_ATTRIBUTE_IDS`, `PROTECTED_DB_FIELDS`, `BIAS_AUDIT_DIMENSIONS`, `LEARNING_PROTECTED_FIELDS`) ficavam **vazias** desde Mar 2026. FairnessGuard rodava fail-OPEN.

ADR-031 v1 propôs criar o YAML — desnecessário. v2 corrige a causa real (path resolver) + adiciona observability.

---

## Decisão (v2)

### 1. Path resolver canonical (LANDED commit `ca6f004cf`)

Substituído por uma única atribuição correta:

```python
# Single canonical _CONFIG_PATH — DO NOT add a second reassignment
# (the v1 bug 2026-05-06: app/shared/config/... was non-existent path,
# made FairnessGuard fail-OPEN since Mar 2026).
_CONFIG_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "protected_attributes.yaml"
    )
)
```

**Verificação**: 7/7 TDD tests em `tests/unit/compliance/test_protected_attributes_loader_path.py` (red→green).

### 2. Sentry breadcrumb (LANDED commit `ca6f004cf`)

Loader agora emite breadcrumb compliance em qualquer falha:

```python
def _emit_sentry_breadcrumb(category: str, msg: str) -> None:
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            category=f"compliance.protected_attributes.{category}",
            message=msg,
            level="error",
        )
    except Exception:
        pass
```

Categories: `yaml_not_found`, `yaml_parse_error`.

### 3. `is_registry_loaded()` helper (LANDED commit `ca6f004cf`)

Para callers que precisam fail-closed (FairnessGuard, startup sanity check):

```python
def is_registry_loaded() -> bool:
    """Returns True iff YAML loaded with at least one protected attribute."""
    cfg = _load_config()
    return bool(cfg) and bool(cfg.get("attributes"))
```

### 4. Gaps remanescentes (Sprint 4 — não-blockers, ~6h)

| Item | Severidade | Esforço |
|---|---|---|
| FairnessGuard chama `is_registry_loaded()` em init + fails fast | P1 | 1h |
| Celery beat semanal `bias_audit_snapshot` populating job | P2 | 2h |
| Test negative: simular YAML missing → assert FairnessGuard raises | P1 | 1h |
| Doc compliance observability em `docs/operations/lgpd-runbook.md` | P2 | 2h |

### 5. NÃO escopo desta ADR

ADR-031 v1 propunha "criar protected_attributes.yaml" — **REJEITADO**, YAML
já existe e é canonical. Schema/version atual (157 linhas, 12 atributos) é
suficiente. Mudanças no YAML continuam a precisar de ADR adicional
(governance gate da v1 mantida).

---

## Consequências

### Positivas (já entregues no commit `ca6f004cf`)
- ✅ FairnessGuard volta a funcionar com 12 atributos LGPD/EEOC
- ✅ Sentry breadcrumb visível em monitoring
- ✅ Helper `is_registry_loaded()` permite fail-closed downstream
- ✅ TDD test 7/7 previne regressão
- ✅ Comentário no código documentando o bug histórico

### Negativas
- ⚠️ Gaps Sprint 4 (Celery beat, fail-fast init, test negative) ainda pendentes
- ⚠️ Histórico — produção rodou fail-open desde Mar 2026 (incidente compliance documentado)

### Reversibilidade
Reversível trivialmente (volta para 2 assignments e quebra de novo). Mas
**NÃO REVERTER** — é compliance crítico LGPD.

---

## Métricas de sucesso

- ✅ 7/7 testes pass em `test_protected_attributes_loader_path.py`
- ✅ Startup logs zero "[ProtectedAttributes] Failed to load YAML"
- ✅ `python3 -c "from app.shared.compliance.protected_attributes import is_registry_loaded; assert is_registry_loaded()"` retorna True
- 📋 Pendente Sprint 4: Sentry breadcrumb confirmado em staging
- 📋 Pendente Sprint 4: bias_audit_snapshots populating weekly via Celery beat

---

## Referências

- Commit `ca6f004cf` (canonical fix)
- `app/shared/compliance/protected_attributes.py` (loader)
- `tests/unit/compliance/test_protected_attributes_loader_path.py` (TDD)
- `/tmp/AUDIT-E-LGPD-FAIRNESS.md` (auditoria que descobriu)
- LGPD Art. 5º + Art. 11 + Art. 20
- Lei 9.029/95 (anti-discriminação)
- ADR-031 v1 (superseded)
- ADR-006 (No PII in logs) — complementar
