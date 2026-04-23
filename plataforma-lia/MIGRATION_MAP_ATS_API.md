# Mapa de migração — FastAPI → ats_api (Rails)

Status dos proxies em `src/app/api/backend-proxy/` quanto ao backend alvo.

Totais:
- **31 proxies** já usam Rails (`/v1/users/*`, `/v1/admin/*`)
- **447 proxies** ainda usam FastAPI (`BACKEND_URL`)

A infra de migração já existe: `createProxyHandlers({ backendTarget: "rails" | "fastapi" })` em `src/lib/api/proxy-handler.ts:88`. Migrar um proxy é trocar o target + path.

---

## Já em Rails (31) — não mexer

| Proxy | Path Rails | Observação |
|---|---|---|
| `activities/` | `/v1/users/activities` | Atividades do sistema |
| `alerts/` | `/v1/users/alerts` | Alertas |
| `briefing/` | `/v1/users/briefing` | Briefing diário |
| `candidates/` + subrotas | `/v1/users/candidates` | CRUD + files + favorite + hide + activities |
| `interviews/` | `/v1/users/interviews` | Entrevistas CRUD |
| `job-vacancies/` | `/v1/users/jobs` | Vagas — transforma JSONAPI inline |
| `lia/profile-analysis/candidate/[id]/` | `/v1/users/lia/...` | Análise de perfil |
| `llm-config/` + providers + test | `/v1/admin/llm_configuration` | Configuração LLM |
| `onboarding/[...path]/` | `/v1/users/onboarding/*` | Fluxo de onboarding |
| `opinions/` | `/v1/users/opinions` | Opiniões sobre candidatos |
| `shared-searches/` | `/v1/users/shared_searches` | Buscas compartilhadas |
| `talent-pools/` + subrotas | `/v1/users/talent_pools` | Talent pools |
| `tasks/` + `tasks/summary` | `/v1/users/tasks` | Tarefas |

---

## Migráveis para Rails (equivalente existe)

| Proxy atual (FastAPI) | Endpoint Rails equivalente | Rota Rails | Prioridade | Notas |
|---|---|---|---|---|
| `email-templates/` | sim | `/v1/users/email_templates` (`routes.rb:298`) | alta | CRUD + render + send. Trivial. |
| `communication/` | sim (parcial) | `/v1/users/messages`, `/v1/users/dispatches` | alta | Mensagens e dispatches |
| `benefits/` | sim | `/v1/users/benefit_relationships` | alta | Já há `bulk_upsert` no Rails |
| `company/` | sim | `/v1/users/account` | alta | Perfil da empresa |
| `calendar/` | sim | `/v1/users/calendar_events` | média | Eventos de calendário |
| `analytics/` (por job) | sim | `/v1/users/jobs/:id/analytics` (`routes.rb:97`) | média | Específico por job |
| `default-templates/` | sim | `/v1/users/email_templates` com filter | média | Filtrar no Rails |
| `departments/` | sim | `/v1/users/departments` | alta | Hierárquico |
| `teams/` | sim | `/v1/users/teams` | média | Equipes |
| `goals/` | sim | `/v1/users/goals` | baixa | Objetivos (se existir) |
| `health/`, `health-check/` | sim | Rails tem endpoint base | baixa | Trivial |
| `evaluations/` | sim | `/v1/evaluations/*` | alta | Entrevistas/testes; rotas públicas e autenticadas |
| `candidate-lists/` | sim | `/v1/users/lists` | alta | Listas dinâmicas |
| `audit-logs/` | sim | `/v1/users/activity_logs` | média | Audit trail |
| `approvals/` | sim | `/v1/users/approval_requests` | alta | Cadeia de aprovação |
| `billing/` | parcial | `/v1/admin/search_credits` | média | Só créditos, falta subscription |
| `clients/` | sim | `/v1/users/account` (para clients) | baixa | Dependente do modelo de cliente |
| `data-requests/`, `data-subject-requests/`, `consent/` | sim | `/v1/users/data_requests` (?) | alta | Compliance LGPD — Rails deve ter |

---

## Não migráveis (IA/LLM — responsabilidade do agente)

Esses devem permanecer na FastAPI ou, melhor, serem roteados para o `recruiter_agent_v5` (que é o componente de agente de IA no ecossistema WeDO):

- `agent-chat/`, `agent-memory/`, `agent-approvals/`, `agent-marketplace/`, `agent-templates/`, `agent-monitoring/`
- `chat/`, `conversations/`, `enhance-prompt/`
- `custom-agents/`
- `digital-twins/`
- `drift/`, `explainability/`, `fairness-report/`, `early-warning/`
- `big-five/`, `analysis/`, `cv/` (parsing IA), `experience-highlights/`
- `ai-credits/` — tracking de LLM
- `voice/` (STT/TTS) — `recruiter_agent_v5` tem Gemini Live API
- `lia/*` — branding do agente atual

Para o ecossistema WeDO coerente, esses deveriam ir para `recruiter_agent_v5` endpoints eventualmente (via callback HTTP ao Rails ou chamada direta).

---

## Proxies que não revisei ainda

447 − (migráveis listadas ≈ 20) − (IA ≈ 30) = ~400 proxies ainda não classificados. Próximos passos:

1. Identificar mais domínios com equivalente claro no Rails (lookup em `routes.rb`).
2. Migrar em lotes pequenos (1 domínio por PR).
3. Testes E2E Playwright existentes em `e2e/tests/` cobrem muitos fluxos — rodar após cada migração.

---

## Como migrar um proxy

Exemplo: `email-templates/route.ts` de FastAPI para Rails.

**Antes:**
```ts
export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/email-templates",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
```

**Depois:**
```ts
export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/v1/users/email_templates",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "rails",
})
```

Rails retorna JSONAPI (`{ data: [...], meta: {...} }`). Se o frontend espera formato plano, adicionar `onResponse`:

```ts
onResponse: (data: unknown) => {
  const body = data as { data?: Array<{ id: string; attributes: Record<string, unknown> }>, meta?: { total?: number } }
  const items = (body.data ?? []).map(item => ({ id: item.id, ...item.attributes }))
  return { items, total: body.meta?.total ?? items.length }
}
```

Para rotas com parâmetros dinâmicos, o `backendPath` aceita `:id`:
```ts
backendPath: "/v1/users/email_templates/:id"
```

---

## Auth e multi-tenancy

Rails usa JWT emitido em `POST /v1/sessions` (`routes.rb:32`). Frontend já manda `Authorization: Bearer <token>` via `getAuthHeaders()`.

Multi-tenancy: Rails usa Apartment gem — tenant é resolvido automaticamente do JWT, switch feito pelo `Authenticable` concern. Frontend não precisa mandar `X-Tenant-ID` (mas pode, para mismatch detection).

Para login direto contra Rails em dev:
```env
RAILS_BACKEND_URL=http://localhost:8080
```
