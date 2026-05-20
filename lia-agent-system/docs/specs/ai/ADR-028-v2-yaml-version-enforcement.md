# ADR-028-v2: YAML metadata.version Enforcement (T-05)

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-05)
**Suplementa:** ADR-028 (Single Source of Truth Prompts)
**Relaciona:** ADR-031-v3 (FairnessGuard cross-sector), T-13 (per-tenant YAML hot-reload)

## Contexto

ADR-028 canonical estabeleceu que prompts vivem em `app/prompts/` como YAML
versionados. Auditoria SSH 2026-05-20 (T-05 Fase A) revelou que **20 de 36 YAMLs
nao tinham `metadata.version` field** — apenas 16 cumpriam o canonical.

Plano V3 listou apenas 2 sites (compliance_block.yaml, orchestrator.yaml) —
mais uma subestimativa pelo plan meta-level.

## Problema

Sem `metadata.version`:
- Rollback granular impossivel (qual versao usar para revert?)
- Hot-reload futuro (T-13) inviavel (cache invalidation por version)
- Drift entre dev e producao sem audit trail
- Diff de PR fica ambiguo (mudou logica ou apenas formatacao?)

## Decisao

Todo YAML em `app/prompts/**/*.yaml` DEVE ter:

```yaml
metadata:
  version: "1.0"  # semver compatible
  added_by: "<contexto>"  # opcional mas recomendado
```

Tipos aceitos para version: `str`, `int`, `float` (semver string preferido).

## Aplicacao

T-05 aplicou metadata block em 20 YAMLs faltantes:

**Domains (12):** agent_calibration, analysis, candidate_self_service,
company_settings, culture_analysis, digital_twin, hiring_policy,
intent_classification, offer, orchestrator, pipeline_transition, talent_pool

**Experiments (2):** cascade_router_system_prompt, job_wizard_field_extraction

**Job creation gates (4):** gate_classifier, gate_competency, gate_review,
gate_wsi_questions

**Shared (2):** compliance_block, guardrails_block

Todos receberam `version: "1.0"` (baseline). Versions futuras incrementam
conforme SemVer:
- PATCH (1.0.1): typo, comment, formatting
- MINOR (1.1): novo campo opcional, novo few-shot example
- MAJOR (2.0): mudanca de behavior, breaking change downstream

## Sensor canonical BLOCKING

`scripts/check_yaml_metadata_version.py`:
- Parse YAML, valida `metadata.version` existe + tipo correto
- Exit 1 se violation, Exit 0 se OK
- Modo BLOCKING desde T-05 (sem warn-only intermediario — escopo zero
  apos fix, manter zero)

## Pre-commit + CI integration

Adicionar hook BLOCKING ao `.pre-commit-config.yaml`:

```yaml
- id: yaml-metadata-version
  name: "T-05 ADR-028-v2: YAML metadata.version enforcement"
  language: system
  entry: python3 scripts/check_yaml_metadata_version.py
  files: ^app/prompts/.*\.(yaml|yml)$
  pass_filenames: false
```

## Consequencias

**Positivas:**
- 100% YAMLs com version (36/36) — drift prevention canonical
- Hot-reload T-13 unlocked (version-based cache invalidation possivel)
- Rollback granular per YAML
- Diff de PR fica claro (mudou version = mudou comportamento)

**Negativas:**
- Pequena ceremony para criar YAML novo (adicionar metadata block)
- Mitigacao: template no `app/prompts/TEMPLATE.yaml` (opcional, T-15 followup)

## Verification

```bash
python scripts/check_yaml_metadata_version.py
# Esperado: "OK -- 36 YAMLs em app/prompts todos com metadata.version"
```

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-05 (este)** | 1 | 20 YAMLs migrated + sensor BLOCKING |
| T-13 | 7-9 | Per-tenant override + hot-reload (usa version field) |
| T-15 | 13 | check_canonical_domain_structure (valida YAML existe por domain) |

## Referencias

- ADR-028 Single Source of Truth Prompts (canonical original)
- PLANO_ACAO_REPLIT_V3 T-05
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md
- Sensor canonical: `scripts/check_yaml_metadata_version.py`
