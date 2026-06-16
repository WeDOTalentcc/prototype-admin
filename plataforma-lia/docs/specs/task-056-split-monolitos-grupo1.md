# Task #56 — Split Monolitos Grupo 1

## Summary

Split 4 monolithic files into domain modules and orchestrator+hook patterns.

## Changes

### 1. `services/lia-api.ts` → `services/lia-api/` (11 modules)

Original: ~4800L monolithic class
Result: 2L barrel re-export

| Module | Lines | Domain |
|--------|-------|--------|
| `base.ts` | 25 | Auth headers, backend URL |
| `types.ts` | 1900 | All 151 interfaces/types |
| `candidates-api.ts` | 371 | Candidate CRUD, search, screening |
| `jobs-api.ts` | 631 | Job vacancy CRUD, publishing, metrics |
| `chat-api.ts` | 215 | Chat, conversations, orchestrator |
| `wsi-api.ts` | 250 | WSI screening, questions |
| `misc-api.ts` | 1006 | Pipeline, bulk, interviews, company |
| `autonomous-api.ts` | 123 | Autonomous agent operations |
| `voice-api.ts` | 185 | Voice/multimodal endpoints |
| `feedback-api.ts` | 102 | Feedback CRUD |
| `index.ts` | 34 | Barrel with liaApi object |

### 2. `job-kanban-page.tsx` (4940L → 1489L orchestrator)

Hook extracted: `job-kanban/hooks/useKanbanPageCore.ts` (2449L)
Pattern: Orchestrator destructures hook return, renders JSX only.

### 3. `candidates-page.tsx` (4811L → 1323L orchestrator)

Hook extracted: `candidates/hooks/useCandidatesPageCore.tsx` (3676L)
Pattern: Orchestrator destructures hook return, renders JSX with dynamic imports.

### 4. `jobs-page.tsx` (4667L → 1340L orchestrator)

Hook extracted: `jobs/hooks/useJobsPageCore.tsx` (3486L)
Pattern: Orchestrator destructures hook return, renders JSX with dynamic imports.

## Type Safety

- Zero `any` in all lia-api domain modules
- Zero `any` in all 3 orchestrator files
- Zero `any` in all 3 hook files
- All replaced with `Record<string, unknown>`, `string`, `unknown`, or proper types

## Backward Compatibility

- `lia-api.ts` barrel preserves identical export API
- All 65 importing files continue to work unchanged
- No changes to component props or public APIs

## Runtime Verification

- Dev server compiles and renders all pages correctly
- No module resolution errors
- No duplicate declaration errors
