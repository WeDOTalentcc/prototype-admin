# F0 — Mapa de Verdade (audit completo)

**Data:** 2026-05-23
**Branch develop monorepo:** `01fd786be 2026-05-20 Merge #58`
**Modo:** audit-only no clone local (read-only). Nada modificado.

---

## 1. Inventário de endpoints (FastAPI lia-agent-system + proxies Next)

### Endpoints FastAPI confirmados existir

| Endpoint FastAPI | Arquivo | Linha |
|---|---|---|
| `GET /candidates/{id}/files` | `lia-agent-system/app/api/v1/attachments.py` | :350 |
| `POST /candidates/{id}/files` (upload) | `attachments.py` | :258 |
| `GET /candidates/{id}/files/download/{filename}` | `attachments.py` | :407 |
| `DELETE /candidates/{id}/files/{attachment_id}` | `attachments.py` | :454 |
| `GET /candidates/{candidate_id}` | `candidates/candidates_crud.py` | :367 |
| `PUT /candidates/{candidate_id}` | `candidates/candidates_crud.py` | :530 |
| `DELETE /candidates/{candidate_id}` | `candidates/candidates_crud.py` | :785 |
| `PATCH /candidates/{candidate_id}/stage` | `candidates/candidates_crud.py` | :582 |
| `GET /opinions/candidate/{candidate_id}/summary` | `opinions.py` | :67 |
| `GET /opinions/candidate/{candidate_id}/history` | `opinions.py` | :121 |
| `GET /opinions/candidate/{candidate_id}` | `opinions.py` | :144 |
| `POST /opinions/` | `opinions.py` | :207 |
| `GET /lia/profile-analysis/candidate/{id}` | `lia_profile_analysis.py` | :246 |
| `DELETE /lia/profile-analysis/candidate/{id}/{type}` | `lia_profile_analysis.py` | :296 |
| `GET /activities` | `activities.py` | :26 |
| `POST /chat/actions/candidate-field-update` | `chat.py` | :1027 |
| `GET /candidates/{id}/cultural-fit` | `cultural_fit.py` | :26 |

### Proxies Next confirmados

| Proxy Next path | Backend target | Arquivo |
|---|---|---|
| `/api/backend-proxy/candidates/[id]` (GET/PUT/DELETE) | **Rails** `/v1/users/candidates/:id` | `candidates/[id]/route.ts` |
| `/api/backend-proxy/candidates/[id]/files` (GET/POST) | **FastAPI** `BACKEND_URL/api/v1/candidates/{id}/files` | `candidates/[id]/files/route.ts` |
| `/api/backend-proxy/candidates/[id]/files/[attachmentId]` (DELETE) | **Rails** `/v1/users/data_files/{id}` | `candidates/[id]/files/[attachmentId]/route.ts` |
| `/api/backend-proxy/candidates/[id]/activities` (GET) | (a confirmar) | `candidates/[id]/activities/route.ts` |
| `/api/backend-proxy/candidates/[id]/favorite` (PUT/DELETE) | Rails | `candidates/[id]/favorite/route.ts` |
| `/api/backend-proxy/candidates/[id]/hide` (PUT) | Rails | `candidates/[id]/hide/route.ts` |
| `/api/backend-proxy/candidates/[id]/stage` (PATCH) | (a confirmar) | `candidates/[id]/stage/route.ts` |
| `/api/backend-proxy/opinions/candidate/[id]/history` (GET) | (a confirmar) | `opinions/candidate/[id]/history/route.ts` |
| `/api/backend-proxy/opinions/candidate/[id]/summary` (GET) | (a confirmar) | `opinions/candidate/[id]/summary/route.ts` |
| `/api/backend-proxy/lia/profile-analysis/...` (GET/POST) | (a confirmar) | `lia/profile-analysis/...` |
| `/api/backend-proxy/chat/actions/candidate-field-update` (POST) | **FastAPI** `BACKEND_URL/api/v1/chat/actions/candidate-field-update` | `chat/actions/candidate-field-update/route.ts` |

### Proxies que NÃO existem (gaps)

🔴 `/api/backend-proxy/data_files/` — proxy **NÃO EXISTE** mas Surface 1 (`useCandidateFiles.tsx:83`) chama ele. **Bug ativo confirmado.**

---

## 2. Arquitetura mista (realidade do código)

Apesar do CLAUDE.md do monorepo afirmar "frontend só fala com Rails", **a realidade é mista:**

- **Rails:** `/candidates/[id]` (GET/PUT/DELETE), `/candidates/[id]/files/[attachmentId]` (delete), `/candidates/[id]/favorite`, `/candidates/[id]/hide`, `/candidates/[id]/viewed`, `/candidates/[id]/toon`, bulk actions
- **FastAPI lia-agent-system:** `/candidates/[id]/files` (list/upload), `/chat/actions/candidate-field-update`, e provavelmente opinions + profile-analysis + activities (a confirmar via proxy reads)

**Per memory Paulo 2026-05-23:** Replit (lia-agent-system + plataforma-lia) é canonical de produção. CLAUDE.md monorepo está desatualizado. Aceito a realidade — não vou tentar mudar arquitetura.

---

## 3. Edit infra — comparativo das 2 opções

### Opção A: `POST /chat/actions/candidate-field-update` ([chat.py:1027](lia-agent-system/app/api/v1/chat.py:1027))

**Como funciona:**
```json
POST /api/backend-proxy/chat/actions/candidate-field-update
{
  "candidate_id": "abc-123",  // ou candidate_name como fallback
  "fields": { "phone": "+55...", "email": "...", "linkedin_url": "..." }
}
→ Response: { success, updated_count, total, results: [{field, value, status, message}] }
```

**Características:**
- Multi-tenant fail-closed: linha 1075 `check_candidate_ownership` → 403 se candidato fora da company
- Multi-field numa request (batch save bom para "salvar tudo" do form)
- Demo mode pula tenant check (linha 1073)
- Vai por `ACTIONABLE_INTENTS["atualizar_campo_candidato"]` → `action_executor._execute_action`
- Proxy Next já existe + aponta pra FastAPI

**Pros pra D7 (inline lápis):**
- ✅ Não precisa criar proxy novo
- ✅ Multi-tenant garantido
- ✅ Pertence ao FastAPI (Replit canonical per Paulo)
- ✅ Built pra UI de confirmação (per docstring linha 1035)

**Cons:**
- ⚠️ Whitelist de fields fica no `action_executor` — preciso confirmar quais fields são permitidos
- ⚠️ Camada extra (action_executor) vs PUT direto

---

### Opção B: `PUT /candidates/{id}` ([candidates_crud.py:530](lia-agent-system/app/api/v1/candidates/candidates_crud.py:530))

**Como funciona:**
```json
PUT /api/backend-proxy/candidates/{id}
CandidateUpdate { phone?, email?, linkedin_url?, ... }  // partial via exclude_unset=True
→ Response: { id, name, email, status, updated_at, message }
```

**Características:**
- Multi-tenant: `_assert_tenant_scope(candidate, current_user)` linha 555
- Idempotency: `reject_duplicate_async` (Task #478, ADR 003)
- Partial update via Pydantic `exclude_unset=True`
- Loop setattr nos fields enviados (linhas 557-559)

**Pros:**
- ✅ REST puro, single source of truth pro modelo
- ✅ Idempotency built-in
- ✅ Pydantic schema `CandidateUpdate` define schema dos fields editáveis

**Cons:**
- 🔴 **Proxy Next atual aponta pra Rails**, não FastAPI. Para usar FastAPI direto, precisa:
  - (a) trocar `backendTarget: "rails"` → `"fastapi"` no proxy, OU
  - (b) criar proxy novo paralelo, OU
  - (c) chamar Rails (que pode ou não ter `PUT /v1/users/candidates/:id` espelhando o FastAPI)

---

### 🎯 Recomendação F0: usar Opção A (`candidate-field-update`)

Razões:
1. **Proxy Next + FastAPI já wired** — zero infra nova
2. **Multi-tenant fail-closed garantido** (`check_candidate_ownership` 403)
3. **Multi-field batch** — útil pra "salvar várias edits ao mesmo tempo"
4. **Pertence ao FastAPI Replit** (foco confirmado por Paulo)
5. **Naming "structured endpoint"** sugere uso pra UI (não NL chat)

**Fallback:** se `candidate-field-update` não cobrir algum field necessário, usar `PUT /candidates/{id}` via Rails (proxy existente) como caso especial.

---

## 4. LGPD field policy proposta

Baseado em ADR-LGPD-001 + REGRA ZERO + CLAUDE.md global do Paulo:

### Fields NUNCA editáveis pela UI (D7 não exibe lápis)

| Field | Razão |
|---|---|
| `race` / `raça` | LGPD dado sensível — não coletar/usar em AI |
| `gender` / `gênero` | Idem |
| `marital_status` / `estado_civil` | Idem |
| `religion` / `religião` | Idem |
| `health_data` / `dados_saúde` | Idem |
| `ethnic_origin` / `origem_étnica` | Idem |
| `political_opinion` / `opinião_política` | Idem |
| `sexual_orientation` / `orientação_sexual` | Idem |
| `union_membership` / `filiação_sindical` | Idem |
| `date_of_birth` / `data_nascimento` (direto) | Idade derivada read-only; editar DoB risca cálculos LGPD |
| `cpf` / `rg` / `passport` | PII forte — políticas específicas |
| `id` / `candidate_id` | Imutável por design |
| `company_id` / `account_id` | Multi-tenancy invariant |
| `created_at` / `updated_at` / `created_by` | Audit metadata |

### Fields editáveis (D7 mostra lápis)

| Field | Tipo | Validação |
|---|---|---|
| `name` / `nome` | text | required, min 2 chars |
| `email` | email | format valid + unique check (backend) |
| `phone` / `telefone` | phone | format +55... |
| `linkedin_url` | URL | https://linkedin.com/in/... |
| `github_url` | URL | https://github.com/... |
| `portfolio_url` / `website` | URL | https:// |
| `location` / `cidade` / `estado` | text | livre |
| `headline` / `current_title` | text | max 200 chars |
| `summary` / `resumo` | textarea | max 2000 chars |
| `current_company` / `empresa_atual` | text | livre |
| `years_of_experience` | number | 0-50 |
| `salary_expectation` | number | > 0 (currency separado) |
| `currency` | select | BRL/USD/EUR |
| `skills` (add/remove) | tag list | dedupe |
| `experiences[]` | array of objects | per-row edit |
| `education[]` | array of objects | per-row edit |
| `languages[]` | array of objects | per-row edit |

### Fields com edit restrito (precisa confirmação 2 vezes ou audit log obrigatório)

| Field | Razão |
|---|---|
| `status` (do candidato) | Pode afetar pipeline — usar PATCH /stage |
| `is_blacklisted` / `is_hidden` | Hard impact — usar endpoints específicos |

---

## 5. SWR cache key matrix proposta

```ts
const SWR_CONFIG = {
  dedupingInterval: 30000,      // 30s
  revalidateOnFocus: false,     // não revalidar ao trocar tab do browser
  revalidateOnReconnect: true,
}

// Keys:
useCandidate(id)            → ["candidate", id]
useCandidateFiles(id)       → ["candidate-files", id]
useCandidateOpinions(id)    → ["candidate-opinions", id, "history"]
useCandidateOpinionsSummary(id) → ["candidate-opinions", id, "summary"]
useCandidateActivities(id)  → ["candidate-activities", id]
useCandidateAnalysis(id)    → ["candidate-analysis", id]
useCandidateBigFive(id)     → ["candidate-big-five", id]
```

**Mutate após edit:**
- `useCandidateFieldUpdate.save()` → mutate `["candidate", id]` optimistic
- Erro 4xx/5xx → rollback automático SWR

---

## 6. LGPD erasure cascade — gap

Não consegui confirmar via audit estático se delete de candidato cascateia em:
- `data_files` ? (Rails owns? FastAPI owns?)
- `opinions` ? (FastAPI)
- `profile-analysis` ? (FastAPI)
- `activities` ? (FastAPI)

**Sinal positivo:** `DELETE /candidates/{id}` existe em ([candidates_crud.py:785](lia-agent-system/app/api/v1/candidates/candidates_crud.py:785)) e em Rails. Provavelmente foreign keys com CASCADE no Postgres ou soft-delete.

**Probe necessário:** rodar Replit, deletar candidato de teste, verificar tabelas no Postgres. **Defer pra F2 P0 transversal** ou tratar como teste isolado em fase própria (ver risco).

---

## 7. Bug Surface 1 Files — confirmação documental

[useCandidateFiles.tsx:83](plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx:83):
```ts
const url = `/api/backend-proxy/data_files?${params.toString()}`
```

`src/app/api/backend-proxy/data_files/` — **pasta vazia**, sem `route.ts`. Significa Next responde 404 nesse path.

**Implicação prática:** ao abrir o drawer (Surface 1) e clicar na tab "Arquivos", o `fetchCandidateFiles` falha silenciosamente (catch em [linha 95-98](plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx:95) mostra toast de erro). Recrutador vê tab vazia + toast vermelho.

**Fix em F2.a:** trocar linha 83 de `/api/backend-proxy/data_files?reference_type=Candidate&reference_id=...` para `/api/backend-proxy/candidates/{candidateId}/files?company_id=...`.

---

## 8. Schemas Zod canonical (a criar em F1)

Em `src/schemas/candidate-canonical.zod.ts`:

```ts
// CandidateFile (de /candidates/[id]/files)
const CandidateFileSchema = z.object({
  id: z.string(),
  file_name: z.string(),
  file_type: z.enum(['cv', 'portfolio', 'video', 'certificate', 'transcript', 'document']),
  file_size: z.number(),
  mime_type: z.string().optional(),
  file_url: z.string(),
  description: z.string().optional(),
  screening_id: z.string().optional(),  // para router de modal
  created_at: z.string(),
})

// Opinion (de /opinions/candidate/[id]/history)
const OpinionSchema = z.object({
  id: z.string(),
  score: z.number().min(0).max(10),       // canonical 0-10 (Task #512)
  wsi_score: z.number().min(0).max(10).optional(),
  job_vacancy_id: z.string().optional(),
  job_vacancy_title: z.string().optional(),
  archetype: z.string().optional(),
  recommendation: z.enum(['aprovar', 'reprovar', 'considerar']).optional(),
  summary: z.string().optional(),
  strengths: z.array(z.string()).optional(),
  weaknesses: z.array(z.object({ text: z.string(), severity: z.enum(['ALTA', 'MÉDIA', 'BAIXA']).optional() })).optional(),
  created_at: z.string(),
})

// Activity (de /candidates/[id]/activities)
const ActivitySchema = z.object({
  id: z.string(),
  type: z.string(),
  title: z.string(),
  author: z.string().optional(),
  date: z.string(),
  status: z.string().optional(),
  summary: z.string().optional(),
  details: z.record(z.unknown()).optional(),
})

// AiFeedback (de opinions response)
const AiFeedbackSchema = z.object({
  summary: z.string().optional(),
  strengths: z.array(z.string()).optional(),
  weaknesses: z.array(z.object({ text: z.string(), severity: z.enum(['ALTA', 'MÉDIA', 'BAIXA']).optional() })).optional(),
  recommendation: z.string().optional(),
  recommendation_justification: z.string().optional(),
  next_steps: z.array(z.string()).optional(),
  skills_analysis: z.array(z.object({
    skill_name: z.string(),
    competence_type: z.enum(['technical', 'behavioral']),
    bloom_achieved: z.string().optional(),
    dreyfus_level: z.string().optional(),
    star_evidences: z.array(z.string()).optional(),
  })).optional(),
  big_five: z.object({
    openness: z.number().min(0).max(10),
    conscientiousness: z.number().min(0).max(10),
    extraversion: z.number().min(0).max(10),
    agreeableness: z.number().min(0).max(10),
    neuroticism: z.number().min(0).max(10),
  }).optional(),
})
```

---

## 9. Sumário — F0 status

| Item | Status |
|---|---|
| Endpoint inventory FastAPI | ✅ confirmado |
| Endpoint inventory proxies Next | ✅ confirmado |
| Bug Surface 1 Files | ✅ confirmado documentalmente |
| Edit infra (Opção A vs B) | ✅ recomendação clara |
| LGPD field policy | ✅ proposta inicial |
| SWR cache matrix | ✅ proposta inicial |
| Zod schemas | ✅ proposta inicial |
| LGPD erasure cascade | ⚠️ probe pendente (Replit live) |
| Audit trail de field changes | ⚠️ a confirmar |
| RBAC de edit | ⚠️ a confirmar |
| `ACTIONABLE_INTENTS["atualizar_campo_candidato"]` whitelist | ⚠️ a confirmar (próximo grep) |

---

## 10. 2 perguntas para Paulo antes de F1

1. **Confirma Opção A (`POST /chat/actions/candidate-field-update`) como endpoint de edit canonical?** Razões: proxy + multi-tenant + multi-field já wired.

2. **Confirma LGPD field policy?** Lista de bloqueados (race/gender/marital/religion/health/orientação/política/etnia/sindicato/DoB direto/CPF/RG) e editáveis (name/email/phone/linkedin/skills/exp/edu/etc.). Algum ajuste?

3. **(bônus)** Os 3 itens "⚠️ a confirmar" (LGPD cascade probe, audit trail, RBAC) — quer que F0 continue até resolver, ou tratamos como riscos em F1+ e seguimos?
