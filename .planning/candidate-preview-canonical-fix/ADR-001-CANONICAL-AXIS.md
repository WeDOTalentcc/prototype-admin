# ADR-001 — Canonical axis: 2 surfaces, shared data eixo

**Data:** 2026-05-23
**Status:** Approved (Paulo D14)
**Phase:** F3+F4

## Contexto

O domínio "candidato" tinha 3 surfaces ativas:
1. **Drawer lateral** (`<CandidatePreview>`) — modal sheet aberto do kanban
2. **Modal full-page** (`<CandidatePage>`) — overlay full-screen
3. **Rota standalone** (`/funil-de-talentos/candidato/[id]/`) — Next.js page

Surface 2 estava com mock pesado. Surface 3 tinha hook canonical wired mas tabs eram stubs `R-020 P0-B`. Surface 1 era canonical. As 3 consumiam endpoints divergentes do backend (`/data_files?reference_type=` vs `/candidates/[id]/files`, etc.)

## Decisão

**Manter 2 surfaces propositalmente distintas:**

| Surface | Propósito |
|---|---|
| **Drawer** (mode=modal default em `<CandidatePage>`) | Consulta rápida no kanban + decisão de pipeline (read-only) |
| **Page** (mode=page) | Vista detalhada + edição inline (D7) |

A rota `/funil-de-talentos/candidato/[id]` continua existindo, mas renderiza `<CandidatePage mode="page">` via `<CandidateRoutePage>` wrapper (que carrega candidato via SWR hook `useCandidateForPage`).

**Eixo de dados comum:**
- Hooks: `useCandidatePreviewCore` + `useCandidateFiles` + `useCandidateForPage`
- Building blocks atômicos em `src/components/candidate-profile/*` reusáveis
- Endpoints canonical confirmados em ADR-006 (separate)

## Alternativas rejeitadas

- **Unificar Drawer + Page num componente único** (Paulo desautorizou D15: "são propositalmente diferentes")
- **Deletar route standalone** (D17: Paulo acessa via URL/link)
- **Reescrever 3 tabs Surface 3 do zero** (B1) — Surface 1 já tem versão canonical, evita 150KB de reescrita

## Consequências

- ✅ Surface 1 (drawer) intocada — fix Files broken via F2 sem refactor
- ✅ Surface 2 absorve código limpo de Surface 3 → -150KB de mock
- ✅ Rota preservada — deep-link continua funcionando
- ⚠️ Layout drawer (480px) vs page (1200px+) gera some squeeze visual em mode=page (defer pra design polish)
- ⚠️ Surface 1 e Surface 2 herdam mesmo conjunto de building blocks — mudanças cross-surface (boy scout)

## Refs

- Commit F3+F4: `bbdcb1824`
- PLAN.md V3 seção 2 (Arquitetura alvo)
