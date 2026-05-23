# ADR-003 — Candidate route absorption (Surface 3 → Surface 2)

**Data:** 2026-05-23
**Status:** Approved (Paulo D18)
**Phase:** F3+F4

## Contexto

Surface 3 (`/funil-de-talentos/candidato/[id]/`) tinha:
- ✅ Hook canonical (`useCandidatePageCore` da rota, 630 LOC, wired endpoints)
- ✅ ProfileTab implementado (565 LOC)
- ✅ CandidatoDetailClient layout (458 LOC)
- ❌ Tabs Activities/Files/Opinions = STUBS marcados `R-020 P0-B "em desenvolvimento"`

Paulo confirmou (D14, D17): "Surface 3 é legado e não deve permanecer, mas rota /candidato/[id] deve ser preservada (deep-link)."

Surface 1 (drawer) ja tem 3 tabs canonical wired (3 fontes Rails, WSI 0-10, multi-tenant).

## Decisão

**Caminho B (absorção):**

1. Deletar `funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` + `CandidateProfileTab.tsx` + `useCandidatePageCore.tsx` + 3 stubs `components/*Tab.tsx`
2. Deletar 5 Surface 2 mocks (`candidate-page/CandidatePage*Tab.tsx` + `useCandidatePageCore.tsx`)
3. Reescrever `candidate-page.tsx` wrapper em dual-mode (`mode: 'modal' | 'page'`) consumindo tabs canonical de Surface 1
4. Criar `<CandidateRoutePage>` que carrega candidato via SWR hook `useCandidateForPage` + delega para `<CandidatePage mode="page">`
5. Reescrever rota `page.tsx` para renderizar `<CandidateRoutePage>` dentro de `<ErrorBoundarySection>`

Total: 14 arquivos deletados, 2 novos, 2 modificados.

## Alternativas rejeitadas

- **B1 — Reescrever 3 tabs Surface 3 do zero** (~150KB de reescrita; Surface 1 já tem prontos)
- **B3 — Mock-by-mock fix in-place** (mantém débito visual; não consolida axis)
- **Deletar rota standalone** (D17: Paulo usa deep-link)
- **Unificar Drawer e Page** (D15: propositalmente diferentes)

## Consequências

- ✅ Surface 2 herda qualidade canonical de Surface 1
- ✅ Rota preservada com URL pública intacta
- ✅ -150KB de mock/stub
- ⚠️ Surface 2 ainda usa wrapper próprio (`candidate-page.tsx`) que importa de Surface 1 — mudanças em Surface 1 propagam automaticamente (good) mas requerem teste cross-surface
- ⚠️ Tabs canonical foram desenhados para drawer (480px); em page (1200px+) layout fica "cramped" no centro com max-w-7xl. Polish visual em fase futura

## Refs

- Commit F3+F4: `bbdcb1824`
- PLAN.md V3 seção F3
