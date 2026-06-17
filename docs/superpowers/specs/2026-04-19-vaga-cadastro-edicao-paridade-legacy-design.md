# Spec — Cadastro e Edição de Vaga (paridade legacy)

> Status: draft · Autor: Claude · Data: 2026-04-19 · Escopo: `plataforma-lia` (Next.js 15) · Substitui comportamento do legado `ats_front` (Vue 3 + Nuxt 3)

## 1. Objetivo

Tornar o fluxo de **criação** e **edição** de vagas em `plataforma-lia` funcionalmente equivalente ao legado Nuxt (documento `MIGRATION_VAGAS_DETALHE.md`, §11), preservando o **layout React já aprovado** (`JobEditTab` + `ScreeningConfigContent`). Saída do spec: usuário consegue cadastrar uma vaga do zero, preencher os 7 steps com persistência real no backend Rails e publicar — **sem** voltar ao sistema legado para completar qualquer campo.

Fora do escopo: kanban/gestão de candidatos, aba Triagem (dashboard), aba Agentes. Esses virão nos próximos specs (mencionados em §11).

## 2. Decisões de produto tomadas no brainstorm

- **Layout não muda.** Seções já implementadas (`info-geral`, `pessoas`, `processo`, `remuneracao`, `configuracoes`, `descricao`, `perguntas`) continuam como estão. Gap é de **wiring de dados**, não de UI.
- **Paridade, não cópia fiel.** Onde o legado tem bug comportamental conhecido (ex.: F5 perde a aba, publicar sem validação), este spec corrige na migração.
- **Criação usa o mesmo componente da edição.** Um único `JobEditTab` com prop `isCreationMode` (já existe); rota `/jobs/new` renderiza em modo criação, primeira save cria a vaga e redireciona para `/jobs/:id?tab=edit`.
- **Autocompletes dinâmicos vêm do backend.** Status/prioridade/urgência/departamento/cidade/tipo-de-local/tipo-de-contrato/senioridade deixam de ser hardcoded e passam a puxar de `/v1/users/*`.
- **Remuneração/benefícios migram para o padrão polimórfico** (`remuneration_relationships` + `benefit_relationships` com `bulk_upsert`). O form atual de salário/bônus/benefícios como array de strings é substituído.
- **Skills/behavioral/languages/responsibilities ganham persistência real** via `*_relationships`. Sugestões LIA continuam disponíveis (já existe componente).
- **WSI generation é async.** Backend expõe `POST /users/jobs/:id/generate_wsi?mode=wsi_compact|wsi_compact_plus` e o frontend polla status (sem WebSocket neste spec — WebSocket fica para o spec do kanban).

## 3. Estado atual (referência de baseline)

| Seção | Layout | Persistência | Endpoints | Gap |
|---|---|---|---|---|
| Step 1 — General | ✅ `JobInfoGeralSection.tsx` | Parcial (PUT genérico) | 5 autocompletes hardcoded | **M** |
| Step 2 — People | ✅ inline em `JobEditTab.tsx:232-268` | ❌ plain text inputs | Falta `/users/search` | **P** |
| Step 3 — Selective Processes | ✅ `JobProcessSection.tsx` + handlers em `useJobEditTab.ts` | ❌ só em memória | Zero endpoints wired | **GG** |
| Step 4 — Remuneration | ✅ `JobRemuneracaoSection.tsx` | ❌ formato simplificado | Zero endpoints wired | **GG** |
| Step 5 — Screening configs | ✅ `SCMSectionConfiguracoes.tsx` | Parcial (via ScreeningConfigManager) | Canais voice/ligacao faltando, `is_screening_active` não persiste direto | **M** |
| Step 6 — Description | ✅ mix (info-geral + SCMSectionContent) | Parcial | Falta skill/behavioral/language relationships CRUD | **G** |
| Step 7 — Questions (WSI) | ✅ `SCMSectionPerguntasEdit.tsx` | ❌ endpoints unknown | Falta evaluations/questions CRUD + generate_wsi | **GG** |
| Rota `/jobs/new` | ❌ não existe | — | — | **G** |
| Publicação | ✅ botão em `JobEditTab.tsx:90-107` | ❌ callback genérico | Falta PUT com `{is_published, job_status_id: <Ativa>}` + fetch dinâmico de status | **M** |

Arquivos-chave: `plataforma-lia/src/components/jobs/JobEditTab.tsx`, `plataforma-lia/src/components/jobs/job-edit-tab/*`, `plataforma-lia/src/components/screening-config/*`, `plataforma-lia/src/hooks/jobs/*`, `plataforma-lia/src/services/lia-api/jobs-api.ts`.

## 4. Arquitetura

### 4.1 Camada de serviços (novo)

Centralizar chamadas ao Rails em módulos por recurso, consumidos via SWR pelos hooks. Todas passam pelo proxy Next (`/api/backend-proxy/...`) — cookie httpOnly guarda JWT, nunca vai ao browser.

```
src/services/jobs/
  ├── jobs.service.ts               ← POST/PUT /users/jobs, /users/jobs/:id
  ├── job-metadata.service.ts       ← job_statuses, priorities, urgency_levels, workplace_types,
  │                                    employment_types, seniorities, departments, cities
  ├── selective-processes.service.ts← CRUD + order
  ├── remunerations.service.ts      ← list tipos, bulk_upsert relationships
  ├── benefits.service.ts           ← idem
  ├── skills.service.ts             ← skills + relationships (proficiency, required)
  ├── behavioral-skills.service.ts  ← idem
  ├── languages.service.ts          ← idem
  ├── evaluations.service.ts        ← evaluations + questions + generate_wsi
  └── job-publishing.service.ts     ← publish flow
```

Cada service expõe funções tipadas (`getX`, `createX`, `updateX`, `deleteX`, `bulkUpsertX`). Não encapsula SWR — isso é responsabilidade dos hooks.

### 4.2 Camada de hooks

```
src/hooks/jobs/
  ├── use-job.ts                    ← SWR do GET /users/jobs/:id (existe, amplia tipagem)
  ├── use-job-metadata.ts           ← autocompletes com cache compartilhado (SWR + dedupe)
  ├── use-job-save-section.ts       ← orquestra save de uma seção (decide POST vs PUT)
  ├── use-selective-processes.ts    ← CRUD + reorder + optimistic updates
  ├── use-remuneration.ts           ← carrega tipos, edita relationships
  ├── use-benefits.ts               ← idem
  ├── use-skills.ts                 ← autocomplete + create-inline + relationship CRUD
  ├── use-behavioral-skills.ts
  ├── use-languages.ts
  ├── use-evaluations.ts            ← evaluations + questions
  ├── use-wsi-generation.ts         ← dispara generate_wsi + polling
  └── use-job-publish.ts            ← busca job_status "Ativa" + PUT publish + validações pré-publish
```

Cada hook retorna `{ data, isLoading, error, mutate, <actions> }`.

### 4.3 Proxy Next

Para cada endpoint novo, adicionar rota em `src/app/api/backend-proxy/` seguindo o padrão existente. Exemplo: `/api/backend-proxy/selective-processes/order/route.ts` → POST `/v1/users/selective_processes/order`.

Rotas a criar:
- `selective-processes/*`
- `selective-processes/order`
- `remunerations/*`
- `remuneration-relationships/bulk_upsert`
- `benefits/*`
- `benefit-relationships/bulk_upsert`
- `skills/*`
- `skill-relationships/*`
- `behavioral-skills/*`
- `behavioral-skill-relationships/*`
- `languages/*`
- `language-relationships/*`
- `evaluations/*`
- `questions/*`
- `jobs/[id]/generate-wsi`
- `jobs/[id]/suggest-responsibilities`
- `job-statuses/*`, `job-priorities/*`, `job-urgency-levels/*`, `job-workplace-types/*`, `job-employment-types/*`, `job-seniorities/*`
- `departments/*`, `cities/*`
- `users/search`

### 4.4 Componentes

Componentes atuais permanecem. Mudanças cirúrgicas:

- **`JobInfoGeralSection.tsx`**: trocar selects hardcoded por `<Autocomplete>` conectado ao `useJobMetadata`. Adicionar `city` (falta hoje). Manter visual.
- **`JobEditTab.tsx:232-268`** (pessoas): extrair para `JobPessoasSection.tsx` e conectar ao `/users/search`. Email fica read-only e auto-popula.
- **`JobProcessSection.tsx`**: conectar handlers em `useJobEditTab.ts` ao `useSelectiveProcesses`. Trocar chevrons por drag-drop com `@dnd-kit/sortable` (biblioteca já no projeto). Distinção `fixas`/`padrão`/`custom` respeitada (campos locked conforme `stage_type`).
- **`JobRemuneracaoSection.tsx`**: redesenhar internals. Lista dinâmica de outras remunerações (select do tipo + currency input do valor). Benefícios viram cards com os 5 campos (`type_description`, `value`, `is_per_day`, `days_of_month`, `details`). Save centralizado em "Salvar" da seção.
- **`ScreeningConfigContent` / `SCMSectionConfiguracoes.tsx`**: acrescentar canais `channel_ligacao` e `channel_voice` (toggle). Expor `is_screening_active` como switch persistido.
- **`SCMSectionContent.tsx`**: adicionar blocos de skills/behavioral/languages como **sub-formulários controlados**. Cada um tem autocomplete (com criação inline), lista vinculada e remoção. Render unificado via componente genérico `<RelationshipPicker>` parametrizado.
- **`SCMSectionPerguntasEdit.tsx`**: conectar ao `useEvaluations`. Dois botões no topo ("WSI Compacto" / "WSI Completo") disparam `useWsiGeneration`.

### 4.5 Rota de criação

`src/app/[locale]/jobs/new/page.tsx` (novo):
- `'use client'` no wrapper que reusa `JobDetailClient`.
- Modo criação: sem `id`, `job=null`, `isCreationMode=true`.
- Ao salvar `info-geral` pela primeira vez, `POST /users/jobs` com campos mínimos obrigatórios (title, department, city). Response traz `id`.
- `router.replace('/jobs/:id?tab=edit')` preservando `?tab`.
- Proteção: se usuário tentar sair com form dirty, `beforeunload` prompt (legado não faz — ganho).

### 4.6 Publicação

`use-job-publish.ts`:
1. Busca `job_status` "Ativa" (cache de sessão).
2. Valida pré-publish: título preenchido, departamento, cidade, ≥1 selective_process, ≥1 skill técnica. (Legado não valida — é ganho do spec.) Bloqueia publish com toast e foca na seção pendente.
3. `PUT /users/jobs/:id { is_published: true, job_status_id }`.
4. Revalida `useJob` via SWR `mutate`.
5. Toast de sucesso + redireciona para `/jobs/:id?tab=management`.

## 5. Data flow

```
Usuário edita input
     │
     ▼
onChange local (jobEditForm / estado de seção)  ─► UI responsiva
     │
     ▼ (user clica "Salvar" na seção)
hook da seção chama service.update(...)
     │
     ▼
proxy Next → Rails
     │
     ▼
hook faz SWR.mutate(key) → revalidate de useJob (se vaga) OU da coleção (relationships)
     │
     ▼
UI re-renderiza com dados frescos
```

Mutations sempre via hooks; componentes não chamam services direto.

## 6. Validação

- **Por campo**: Zod schema por seção, integrado com `react-hook-form` onde form já usa RHF; onde é state manual (caso atual), manter manual no MVP mas validar no submit via Zod `.parse()`.
- **Cross-section**: validação de publish (§4.6).
- **Erros de API**: padrão do projeto — toast com `error.response?.data?.errors?.[0]` ou fallback genérico em pt-BR.
- **Save explícito, sem auto-save.** Cada seção tem botão "Salvar" que dispara mutation. O legado tem auto-save no Description — nesta migração descartamos para evitar salvar estado inválido; usuário precisa clicar em salvar.

## 7. Testes

Testes mínimos (vitest):
- **Services**: mock axios, teste shape de body para cada endpoint novo.
- **Hooks**: `use-selective-processes` (optimistic update + rollback), `use-job-publish` (validações), `use-wsi-generation` (polling loop).
- **Componentes**: render de `JobRemuneracaoSection` no novo shape; `RelationshipPicker` com criação inline.
- **E2E (Playwright)**: smoke do fluxo "/jobs/new → preencher 7 steps → publicar". Um único teste; não cobre cada campo.

Cobertura-alvo: hooks 80%+, services 90%+. Componentes sem meta numérica — só testes de smoke dos novos.

## 8. Migração / retro-compatibilidade

- Vagas já criadas no banco continuam abrindo na edição. Shape do `job_record` não muda; o que muda é como o frontend **edita** certos campos.
- Remuneração/benefícios: o frontend lê o shape canônico do Rails (`remuneration_relationships`, `benefit_relationships`). Vagas antigas que só tenham `salary_min`/`salary_max` em campos flat da `Job` aparecem com valores vazios na nova UI — a migração de dados de backend (se necessária) fica fora do escopo deste spec e é open question (§14).

## 9. Observabilidade e analytics

- `postEntityPageVisit()` já existe no legado; portar na `/jobs/new` também (tipo `entity: 'jobs_new'`).
- Toasts de sucesso em operações destrutivas (delete stage, delete evaluation) já são padrão — manter.

## 10. Edge cases tratados

Lista do legado (§13 de `MIGRATION_VAGAS_DETALHE.md`) aplicada a esta seção:

| # | Edge case | Tratamento |
|---|---|---|
| 1 | Página branca em 404 | Error boundary dedicado com CTA "voltar à listagem" |
| 4 | `setJob(job)` merge manual frágil | Substituído por `mutate` do SWR — não aplicável aqui |
| 5 | Dupla-clique em save | Botões de save desabilitam via `isSaving` (já é padrão do projeto) |
| 9 | Share URL null | Tooltip: "Link público disponível após publicar" |
| 14 | Publicar sem validar | §4.6 valida título, departamento, cidade, ≥1 stage, ≥1 skill técnica |
| 18 | Reorder sem drag-drop real | `@dnd-kit/sortable` |
| 19 | Mistura `*_attributes` (object) vs string | Schemas Zod deixam isso explícito por campo |

Edges que **não** serão resolvidos aqui (backlog do spec do kanban): 2, 3, 7, 8, 10, 11, 12, 13, 15, 16, 17, 20.

## 11. Relação com próximos specs

Ordem definida com o usuário:

1. **Este spec** — Cadastro + Edição (7 steps + publish + /jobs/new)
2. **Spec 2 — Kanban (aba Gestão):** realtime (ApplyCollection/Pipeline channels), modais granulares (schedule_interview full, send_interview_link, reject_bulk com motivos, candidate_search + resultados, similar_candidates), ações em massa (gate1, gate2, send_reject_feedback).
3. **Spec 3 — Aba Agentes** (BackgroundAgentChannel, dashboard, feedback loops; restrita a super_admin).
4. **Spec 4 — Aba Triagem** (dashboard WSI já existe; só lapidações de polling e integração com canal realtime se substituir polling).
5. **Spec 5 — Ações fora do core** (gates em massa, send_reject_feedback via LIA, relatório da vaga).

## 12. Critérios de aceite (deste spec)

1. [ ] Rota `/jobs/new` funciona e cria vaga em rascunho persistida no Rails.
2. [ ] Cada um dos 7 steps persiste via endpoints listados em §4.3, com toast de sucesso/erro e revalidação SWR.
3. [ ] Autocompletes puxam dados dinâmicos (nenhum select hardcoded dos 8 listados em §3).
4. [ ] CRUD de `selective_processes` com drag-drop real, respeitando locks de `stage_type`.
5. [ ] Remuneração e benefícios usam `bulk_upsert` polimórfico.
6. [ ] Skills (técnicas + comportamentais), idiomas e responsabilidades com CRUD por relationship + criação inline.
7. [ ] WSI generation dispara async + polling + atualiza UI quando pronto.
8. [ ] Publish valida mínimo e faz PUT correto.
9. [ ] Smoke E2E Playwright passa.
10. [ ] Lint (`npm run lint`) e type-check (`tsc --noEmit`) limpos na área tocada.

## 13. Riscos e mitigações

- **Endpoints Rails podem não existir conforme especificado.** → antes de cada workstream, `grep` no `ats_api/app/controllers/v1/users/` para confirmar; se faltar, marcar blocker e discutir.
- **Backend de `generate_wsi` ser sync ou usar WebSocket em vez de polling.** → investigar no primeiro contato com o endpoint; se for WS, reusar infraestrutura de ActionCable que já existe em `src/lib/websocket/`.
- **Migração de shape de remuneração** pode exigir `data migration` no Rails. → fora do escopo; se bloquear, abrir issue separada.
- **Escopo grande para um spec só.** Mitigação: cada workstream (step) é um PR independente, executado em ordem. Plano detalhado virá no `writing-plans`.

## 14. Open questions

- Backend aceita criar vaga com campos mínimos (só title/department/city) ou exige mais no `POST /users/jobs`?
- `jd_dimensions` é sempre populado pelo backend ou depende de trigger explícito?
- `channel_voice` é mesmo um canal de triagem ou é modo "entrevista por voz" separado? (Legado diz que é canal; confirmar.)
- Vagas antigas sem `remuneration_relationships` precisam de data migration no Rails, ou o backend já lê/escreve em ambos os formatos de forma transparente?

Estas 4 bloqueiam workstreams específicos. Resolver antes ou durante writing-plans.

---

**Próximo passo:** self-review deste spec, commit, aguardar aprovação do usuário, então invocar `writing-plans` para destrinchar em plano de implementação por workstream.
