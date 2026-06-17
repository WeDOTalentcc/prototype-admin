# `_wedo_internal/` — Componentes da área staff WeDOTalent (provisória)

**Status:** provisional. Migra para repo `wedotalent-admin` (admin2.wedotalent.cc) quando ele nascer.

## Disciplina canonical

1. **Apenas componentes movidos para a área staff** vivem aqui.
2. **Não importar para fora do route group `(staff)/`** — ESLint rule `no-restricted-imports` bloqueia (warn-only nesta PR; promover blocking quando todos os 8/9 components estiverem migrados).
3. Cada subdiretório espelha a estrutura de rota correspondente:
   - `fairness/` → `src/app/[locale]/(staff)/wedo-admin/fairness/`
   - `governanca/` → `src/app/[locale]/(staff)/wedo-admin/governanca/`
4. **Backend services NÃO mudam.** Os componentes aqui continuam chamando os mesmos proxy routes e endpoints FastAPI que tinham na localização original.

## Plan canonical

`/Users/paulomoraes/.claude/plans/jolly-roaming-moler.md` (seção "PLANO DE EXECUÇÃO")

## Audit base

`~/Documents/wedotalent_audit_2026-05-25/10_extraction_mapping.md`
