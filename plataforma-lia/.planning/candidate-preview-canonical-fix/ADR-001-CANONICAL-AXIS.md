# ADR-001 — 2 Surfaces, Mesmo Eixo de Dados, Building Blocks Compartilhados

**Status:** APROVADO  
**Data:** 2026-05-23  
**Confirmado por:** Paulo Moraes  
**Milestone:** Candidato 2 Surfaces (Drawer + Page dual-mode)

---

## Contexto

O milestone "Candidato 2 Surfaces" identificou que o sistema tinha 3 surfaces de visualização de candidato:
- Surface 1: `CandidatePreview` (drawer/modal, read-only)
- Surface 2: Página `/funil-de-talentos/candidato/[id]` (rota standalone)
- Surface 3 (implícita): componentes duplicados entre as duas anteriores

Paulo usa deep-link direto para candidatos a partir de notificações e bookmarks. A página standalone é rota essencial para esse fluxo.

## Decisão

**2 surfaces canônicas com o mesmo eixo de dados e building blocks compartilhados:**

1. **Surface 1 — Drawer read-only:** `<CandidatePreview>` em `src/components/candidate-preview/`  
   - Contexto: kanban, pipeline overview, busca
   - Modo: leitura + opinião + decisão de pipeline
   - Dados: via `useCandidatePreviewCore`

2. **Surface 2 — Page dual-mode:** `<CandidatePage>` em `src/components/candidate-page/`  
   - Contexto: deep-link standalone + modal futuro
   - Modo: `mode="page"` (com edição inline via EditableField) | `mode="modal"` (read-only, para contextos similares ao drawer)
   - Dados: via `use-candidate-for-page`

**Building blocks compartilhados** em `src/components/candidate-profile/`:
- `CandidateScoreBadge` — badge de score canonical (substitui /100 legado)
- `CandidateAvatar` — avatar com iniciais
- `CandidateContactActions` — botões de contato
- `CandidateSkillsList` — lista de skills
- `EditableField` — campo inline editável com LGPD policy
- `ProfileExperienceSection`, `ProfileEducationSection` — seções de perfil

**Eixo de dados:** hooks em `src/hooks/candidates/` servem ambas as surfaces.

## Consequências

- Surface 3 eliminada — código absorvido em `CandidatePage`
- Nenhuma lógica de negócio duplicada entre surfaces
- Building blocks testáveis independentemente das surfaces
- Adição de nova surface futura: importar building blocks de `candidate-profile/`

## Sensors

- `check_no_orphan_routes.mjs` — garante que imports da pasta de rota antiga não vazam
- `check_candidate_score_no_legacy.mjs` — garante que /100 legado não retorna

---

_Registered by execute-phase F6 — 2026-05-30_
