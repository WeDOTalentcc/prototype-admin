# ADR-003 — Surface 3 Absorvida em Surface 2 Dual-Mode

**Status:** IMPLEMENTADO  
**Data:** 2026-05-23  
**Milestone:** Candidato 2 Surfaces (Drawer + Page dual-mode) — F3

---

## Contexto

Antes do milestone, a rota `/funil-de-talentos/candidato/[id]` tinha sua propria
pasta `components/` com logica duplicada de `CandidatePreview`. Isso gerava:
- 2 implementacoes de listagem de atividades
- Mocks pesados inline (getDemoActivities, arrays de 12+ objetos JSX hardcoded)
- Div de 7 cards JSX estaticos sem dados reais

## Decisao

**Surface 3 eliminada. Rota absorvida em `CandidatePage mode="page"`.**

### O que foi eliminado

1. `src/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/components/` — pasta completa removida
2. `getDemoActivities()` — funcao geradora de mock activities (12 objetos hardcoded)
3. Array `aiPredictions` — 4 objetos fake de predicao AI
4. 7 cards JSX estaticos — substituidos por `CandidatePageSummary` + `CandidatePageHeader`
5. `src/data/demo-activities.ts` — arquivo de demo data sem consumers reais (orphaned em F3)

### O que foi preservado

- Rota `/funil-de-talentos/candidato/[id]` — mantida (Paulo usa deep-link)
- `CandidateRoutePage.tsx` — thin wrapper sobre `<CandidatePage>` (28 LOC)
- `page.tsx` — entrada da rota Next.js

### Arquitetura pos-F3

```
src/app/.../funil-de-talentos/candidato/[id]/
  page.tsx                 ← Next.js page entry
  CandidateRoutePage.tsx   ← wrapper: useParams + useCandidateForPage + <CandidatePage>

src/components/candidate-page/
  CandidatePageHeader.tsx  ← header com avatar, score badge, acoes
  CandidatePageSummary.tsx ← resumo de perfil (experiencia, educacao, skills)
  __tests__/               ← smoke tests

src/components/candidate-profile/
  [building blocks compartilhados]
```

## Consequencias

- Zero duplicacao de logica entre Surface 1 e Surface 2
- Dados reais via `use-candidate-for-page` (nenhum mock em producao)
- `demo-activities.ts` pode ser deletado sem impacto (nenhum import real)

## Estado de limpeza (F6)

- `src/data/demo-activities.ts` — deletado em F6 (zero imports reais)
- Sensor `check_no_hardcoded_candidate_mocks.mjs` — confirma baseline 0 de nomes fake
- Sensor `check_no_hardcoded_arrays.mjs` — confirma baseline 0 de arrays hardcoded

---

_Registered by execute-phase F6 — 2026-05-30_
