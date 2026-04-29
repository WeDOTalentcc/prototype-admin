# GitHub Copilot / Claude Code — Index

Este arquivo é o índice dos **instruction files** do monorepo WeDO Talent. Cada arquivo em `.github/instructions/` tem um `applyTo:` glob no frontmatter — Copilot e Claude Code carregam automaticamente o(s) arquivo(s) cujo glob bate com o arquivo sendo editado.

Para contexto amplo do monorepo (arquitetura, comandos, integrações críticas), ver `CLAUDE.md` na raiz. Para Design System do frontend, ver `plataforma-lia/CLAUDE.md`.

## Backend Rails — `ats_api/`

| Editando… | Instruction file | Cobre |
|---|---|---|
| `app/controllers/**/*.rb` | `rails-controllers.instructions.md` | herança, `render_*`, Searchkick em index, soft delete, strong params |
| `app/models/**/*.rb` | `rails-models.instructions.md` | ordem de blocos, associations (`dependent`), enums, concerns, JSONB, scopes |
| `app/services/**/*.rb` | `rails-services.instructions.md` | padrão `initialize(kw:) + call`, LLM+`LlmUsage`, caching, erro estruturado |
| `app/serializer/**/*.rb` | `rails-serializers.instructions.md` | JSON:API serializer patterns |
| `app/sidekiq/**/*.rb` | `rails-sidekiq.instructions.md` | workers, retries, idempotência |
| `db/migrate/**/*.rb` | `rails-migrations.instructions.md` | padrões de migration, reversibilidade |
| integrações Searchkick | `rails-searchkick.instructions.md` | `search_data`, reindex async, index tenant-scoped |
| código multi-tenant | `rails-apartment.instructions.md` | `Apartment::Tenant.switch!`, `account_id` |
| `spec/**/*_spec.rb` | `rails-specs.instructions.md` | RSpec patterns, factory bot, request specs |

Padrões-chave: controllers skinny → services; JSON:API via `render_success`/`render_error`; `is_deleted` para soft-delete; enums como hash com int explícito.

## Frontend Next.js — `plataforma-lia/`

| Editando… | Instruction file | Cobre |
|---|---|---|
| qualquer `*.{ts,tsx}` sob `plataforma-lia/src/` | `frontend-overview.instructions.md` | stack, layout de pastas, imports, portabilidade Vue, segurança |
| `src/app/**/*.{ts,tsx}` | `next-app-router.instructions.md` | Server vs Client Components, layouts, metadata, `loading/error/not-found`, i18n, API routes |
| `src/components/**/*.tsx` | `react-components.instructions.md` | anatomia, props, CVA, composição, 3 estados (loading/error/empty), acessibilidade |
| `*.tsx` (estilo) | `styling-tailwind.instructions.md` | `cn()`, ordem de classes, tokens DS, dark mode, z-index, transitions |
| forms RHF | `forms-and-validation.instructions.md` | Zod schema-first, `zodResolver`, `applyServerErrors`, `Field` wrapper, ARIA |
| `src/{lib/api,hooks,services,app/api}/**` | `data-fetching.instructions.md` | `createProxyHandlers`, SWR keys, invalidação, `extractErrorMessage`, JSON:API |
| `src/stores/**/*.ts` | `state-management.instructions.md` | Zustand (`interface State + Actions`), `devtools`, `persist`, seletores, árvore de decisão |
| qualquer `*.{ts,tsx}` | `typescript-conventions.instructions.md` | `strict` novo código, `any` vs `unknown`, `interface` vs `type`, `z.infer`, narrowing |

Padrões-chave: Server Components por padrão; SWR (não TanStack Query); `fetch` via `/api/backend-proxy/*` (não axios); JWT em cookie httpOnly; Zustand para UI global, SWR para server state; `cn()` + tokens DS.

## Como usar

### Claude Code

Carrega automaticamente todos os arquivos de `.github/instructions/` cujo `applyTo:` bate com o arquivo aberto. Também lê `CLAUDE.md` global e `plataforma-lia/CLAUDE.md` (aninhado).

### GitHub Copilot (Chat + code completion)

Habilite o suporte a custom instructions (Copilot Chat → Settings → "Code generation instruction files"). Os arquivos com frontmatter `applyTo:` são aplicados por glob automaticamente.

### Cursor / outros

O mesmo conteúdo é compatível com `.cursor/rules/` — copie o arquivo relevante e ajuste a extensão (`.mdc`) se sua IDE exigir.

## Contribuindo com novas regras

1. Crie `.github/instructions/<escopo>.instructions.md` com frontmatter `applyTo:` correto.
2. Registre na tabela acima + aponte em `CLAUDE.md` (seção "Regras por tipo de arquivo").
3. Siga o tom dos arquivos existentes: denso, opinionado, ✅/❌, seção "Rules" ao final, ~300 linhas máx.
4. Não duplique regras que já existem em outro instruction file — **referencie**.

## Hierarquia de prioridade

```
1. Instruções explícitas do usuário no chat         ← maior prioridade
2. CLAUDE.md (raiz) + CLAUDE.md do subprojeto
3. .github/instructions/*.instructions.md           ← este índice
4. Default behavior do assistente
```

Se há conflito entre um instruction file e o `CLAUDE.md` do subprojeto, o **subprojeto vence** (é mais específico). Se há conflito entre o usuário e qualquer um dos dois, **usuário vence**.
