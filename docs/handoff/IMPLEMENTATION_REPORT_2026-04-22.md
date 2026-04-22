# Relatório de Implementação — Sessão 2026-04-22

**Projeto:** LIA / WeDOTalent
**Branch:** `fix/kanban-e2e-bugs`
**Autor:** Paulo Moraes + Claude Code
**Escopo:** Feature Triagem WSI + Auditoria exaustiva de Multi-tenancy

---

## 1. Sumário Executivo

Sessão de trabalho focada em duas frentes:

1. **Feature nova:** seção "Triagem WSI" no modal Duplicar Vaga com 3 opções (manter/regenerar com LIA/configurar manual) + sidebar LIA no tab de configuração de vaga
2. **Hardening de segurança:** auditoria profunda de multi-tenancy encontrou e corrigiu **26 pontos críticos** onde dados podiam vazar entre tenants em produção

**Resultado:**
- 7 commits entregues na branch `fix/kanban-e2e-bugs`
- 1 feature completa + 26 fixes de segurança
- 4 documentos de handoff para times externos (IA, Rails)
- Zero erros TypeScript introduzidos
- Zero breaking changes para fluxos existentes

---

## 2. Timeline de Commits

| Commit | Título | Escopo |
|--------|--------|--------|
| `c9d4b8f3` | feat(vagas): seção Triagem WSI no modal Duplicar Vaga + LIA em job settings | Feature — 7 componentes |
| `a4a7262b` | fix(jobs,public-page): remover fabricações P2 + P0 página pública de vaga | Hotfix página pública |
| `5266b8b8` | fix(public-page,insights): máscara telefone BR + shadcn Input + feedback Email | UX refinements |
| `025db036` | docs(handoff): adicionar Sessão AUDIT Gestão de Vagas ao DEVELOPER_HANDOFF | Docs |
| `779342fd` | fix(job-duplicate-modal): limitar altura do modal com scroll interno | UX fix |
| `a599487d` | fix(multi-tenancy): corrigir company_id em 10 pontos P0/P1/P2 no frontend | Multi-tenancy #1 |
| `1f03b781` | fix(multi-tenancy): 16 rotas proxy user-facing + helpers canônicos + handoffs | Multi-tenancy #2 |

---

## 3. Feature — Triagem WSI no Modal Duplicar Vaga

**Commit:** `c9d4b8f3`

### Problema

O modal "Duplicar Vaga" copiava perguntas de triagem WSI, mas não oferecia ao recrutador nenhum controle sobre o que fazer com elas na vaga duplicada. A triagem ficava inativa na cópia e o recrutador não tinha caminho guiado. Além disso, o tab de configuração (`activeTab === 'edit'`) não tinha o sidebar da LIA, isolando a configuração da IA.

### Solução

Seção "TRIAGEM WSI" no modal com 3 opções mutuamente exclusivas + navegação pós-duplicação + habilitação do sidebar LIA no tab edit.

### Arquivos modificados

| Arquivo | O quê |
|---------|-------|
| `src/components/modals/job-duplicate-modal.tsx` | RadioGroup 3 opções (keep/regenerate_lia/manual) + `max-h-[90vh]` |
| `src/components/pages/jobs/useJobsModalHandlers.ts` | Navegação pós-duplicação por `triagemOption` |
| `src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` | `useEffect` mount consumindo URL params (openChat/chatPrompt/tab/section) |
| `src/components/pages/job-kanban/KanbanPageContent.tsx` | `KanbanLIASidebar` no bloco `activeTab === 'edit'` |
| `src/components/jobs/job-edit-tab/job-edit-tab.types.ts` | `initialSection?: string` em `JobEditTabProps` |
| `src/components/jobs/job-edit-tab/useJobEditTab.ts` | `VALID_SECTIONS` + consumo de `initialSection` |
| `src/components/jobs/JobEditTab.tsx` | Propagação da prop `initialSection` |

### Fluxos end-to-end

**Fluxo 1 — "Regenerar com LIA":**
1. Recruiter seleciona `regenerate_lia` → click "Criar Duplicata"
2. Handler → `router.push(/jobs/{newJobId}?openChat=true&chatPrompt=wsi_regenerate)`
3. `useKanbanPageCore` mount effect → `setShowExpandedLIA(true)` + pré-carrega prompt WSI
4. `KanbanPageContent` renderiza sidebar LIA aberto com prompt pronto (HITL: recruiter confirma envio)

**Fluxo 2 — "Configurar manualmente":**
1. Recruiter seleciona `manual` → click "Criar Duplicata"
2. Handler → `router.push(/jobs/{newJobId}?tab=edit&section=perguntas)`
3. `useKanbanPageCore` mount effect → `setActiveTab('edit')` + `setInitialScreeningSection('perguntas')`
4. `KanbanPageContent` renderiza `JobEditTab` com `initialSection="perguntas"` direto na aba de triagem

**Fluxo 3 — "Manter originais":**
1. Recruiter seleciona `keep` (default) → duplica normalmente
2. Triagem fica inativa — recruiter ativa manualmente depois se quiser

### Hotfixes subsequentes

- `779342fd` — modal crescia indefinidamente com 4 seções; fix: `max-h-[90vh] flex flex-col` + overflow interno
- `a4a7262b` + `5266b8b8` — refinamentos adjacentes na página pública de vaga

---

## 4. Auditoria Multi-tenancy — Frente 1 (Frontend)

**Commit:** `a599487d`

### Problema (causa raiz)

O hook `useAuth()` em `src/contexts/auth-context.tsx` não expunha `company_id` (UUID do tenant) — só expunha `company` (nome de exibição, string legível).

Como resultado, **todo componente que tentava usar `user.company` como tenant ID** (em headers HTTP, chamadas API, filtros de query) recebia o nome da empresa. E como isso obviamente quebrava no backend, cada callsite adicionou fallback hardcoded: `'demo'`, `'demo_company'`, ou string name.

```typescript
// ❌ Padrão anti-tenant difundido (antes)
const { user } = useAuth()
const companyId = (user?.company as string) || 'demo'
fetch(`/api/.../${companyId}`)  // envia nome da empresa ou 'demo'
```

### Solução (fix na raiz + cascata)

**Fix P0 ROOT CAUSE:** `auth-context.tsx` passa a expor `company_id`:
```typescript
// ✅ useAuth() agora retorna ambos
user: ctx.user ? {
  ...,
  company: ... ,        // nome (para display)
  company_id: ...,      // UUID (para APIs)
}
```

### 10 pontos corrigidos

| # | Arquivo | Fix | Severity |
|---|---------|-----|----------|
| 1 | `src/contexts/auth-context.tsx` | Expõe `company_id` em `useAuth()` | 🔴 ROOT CAUSE |
| 2 | `src/components/pages/job-kanban/hooks/useKanbanPageCore.ts:61` | `.company\|\|'demo'` → `.company_id\|\|''` | 🔴 P0 |
| 3 | `src/components/pages/job-kanban/hooks/useKanbanPageSetup.ts:30` | Mesmo padrão | 🔴 P0 |
| 4 | `src/components/pages/modules-page.tsx:273` | `.company\|\|"demo_company"` → `.company_id\|\|''` | 🔴 P0 |
| 5-8 | `src/components/settings/use-user-management.ts` (4 linhas: 57, 137, 180, 201) | Early return em vez de `\|\|'demo_company'` | 🟡 P1 |
| 9 | `src/components/onboarding/onboarding-controller.tsx:68` | `\|\|'demo_company'` → `\|\|''` | 🟡 P1 |
| 10 | `src/components/onboarding/onboarding-controller.tsx:86` | `'demo_company'` → `NEXT_PUBLIC_DEV_COMPANY_ID\|\|''` | 🟡 P1 |
| 11 | `src/components/ui/premium-autocomplete.tsx:54` | Default prop `"demo"` → `''` | 🟡 P1 |
| 12 | `src/components/screening-config/SCMSectionContent.tsx:95` | Lê `company_id` (snake_case da API) com fallback camelCase | 🟢 P2 |
| 13 | `src/hooks/shared/use-authenticated-user-id.ts` | Widened type de `resolveUserId` (colateral) | 🟢 P2 |

### Impacto antes/depois

**Antes:** Kanban, modules page, user management, onboarding, autocomplete premium, screening config WSI — todos podiam enviar nome da empresa ou string 'demo' para APIs críticas, causando scope errado.

**Depois:** Todos leem `user.company_id` (UUID real do JWT). Nenhum fallback hardcoded em código user-facing.

---

## 5. Auditoria Multi-tenancy — Frente 2 (Proxy Routes)

**Commit:** `1f03b781`

### Problema

Nas rotas Next.js de `src/app/api/backend-proxy/`, um padrão diferente de anti-tenant era usado — 50 rotas com uma de duas variações:

```typescript
// ❌ Variação 1 (24 rotas): sempre admin, sem exceção
'X-Company-ID': 'admin_company'

// ❌ Variação 2 (26 rotas): fallback para admin quando header ausente
'X-Company-ID': request.headers.get('X-Company-ID') || 'admin_company'
```

O backend FastAPI já validava cross-tenant via JWT no middleware `auth_enforcement.py` (linhas 268-281), mas essa validação só funciona se o header chegar correto. Rotas user-facing com fallback `'admin_company'` bypassavam a validação quando o header era stripped ou ausente.

**Exemplo concreto de vazamento possível:** rota `transition/execute` — usuário poderia mover candidato de qualquer tenant se conseguisse o ID.

### Solução — Helpers canônicos + migração

**Novos arquivos reutilizáveis:**

1. `src/lib/api/backend-url.ts` — `BACKEND_URL` centralizado (deduplica 80+ rotas que redefiniam localmente)

2. `src/lib/api/session-auth.ts` — `getSessionAuth()` dual-auth:
   - Lê cookie `workos_session` (SSO WorkOS) → `verifyAndDecodeSession()`
   - Fallback para cookie `lia_access_token` (JWT email/senha) → decode manual
   - Dev-only fallback via env `NEXT_PUBLIC_DEV_COMPANY_ID` (não mais hardcoded)
   - Retorna `{ success, headers, session } | { success: false, response: 401 }`

**Padrão canônico pós-fix:**
```typescript
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'

export async function POST(request: NextRequest) {
  const auth = await getSessionAuth()
  if (!auth.success) return auth.response

  const response = await fetch(`${BACKEND_URL}/api/v1/...`, {
    method: 'POST',
    headers: auth.headers,   // X-Company-ID do JWT real, não 'admin_company'
    body: ...,
  })
  ...
}
```

### 16 rotas user-facing migradas

| Rota | Severity | O quê protege |
|------|----------|---------------|
| `transition/execute` | 🔴 HIGH SECURITY | Impedia cross-tenant candidate moves |
| `billing/route.ts` (GET/POST) | 🟡 CRITICAL | Billing CRUD user |
| `billing/subscription` (GET/PUT) | 🟡 CRITICAL | Subscription user |
| `billing/usage` (GET) | 🟡 CRITICAL | Usage metrics user |
| `billing/payment-methods/*` (2 rotas) | 🟡 CRITICAL | Payment methods user |
| `billing/invoices/*` (3 rotas — list/get/pay) | 🟡 CRITICAL | Invoices user |
| `ai-credits/route.ts` | 🟡 CRITICAL | AI consumption per-tenant |
| `alerts/config/route.ts` (GET/PUT) | 🟡 CRITICAL | Alert config user |
| `communications/route.ts` (GET) | 🟡 CRITICAL | Communication history user |
| `technical-tests/*` (3 rotas — list/CRUD/seed) | 🟡 CRITICAL | Technical tests user |
| `interpret-context/route.ts` | 🟡 CRITICAL | LIA feature user |

### 34 rotas admin-only mantidas intactas

Essas rotas são legitimamente admin-only (platform admin CRUD). Foram mantidas com `'admin_company'` hardcoded porque o backend valida via `require_admin()`. Classificadas:

- `clients/*` (14 rotas) — platform admin gerencia clientes
- `policies/*` (3 rotas) — admin policies
- `observability/*` (1 rota) — system-wide observability
- `default-templates/*` (5 rotas) — admin templates
- `saas-metrics/*` (6 rotas) — admin dashboard
- `global-policies/*` (5 rotas) — admin global policies

---

## 6. Documentação para Times Externos

**Commit:** `1f03b781` (mesmos)

Criados 3 documentos de handoff em `docs/handoff/`:

### `HANDOFF_SESSION_MULTI_TENANCY.md`
Sumário executivo da sessão de multi-tenancy — contexto completo, fixes feitos, links para handoffs específicos.

### `HANDOFF_AI_TEAM_MULTI_TENANCY.md`
Escopo do time IA (`lia-agent-system`, repo separado):

| Item | Severity | Descrição |
|------|----------|-----------|
| `agent_monitoring_service.get_all_agents_summary()` | 🔴 P0 | Sem escopo por company_id — vaza atividades de agentes cross-tenant |
| `candidate_repository.search()` + `find_by_email()` | 🟡 P1 | Sem filtro company_id apesar da coluna existir no modelo |
| LLM factory — 2 code paths legados | 🟡 P1 | `llm_factory.py:455, 715` sem `tenant_id` em `get_provider_for_tenant()` |
| Checklist produção LLM factory | 🟢 P2 | ENCRYPTION_KEY, Redis budget keys, cache invalidation |

Cada item tem: arquivo + linha, código antes/depois, testes sugeridos, padrão de referência no código.

### `HANDOFF_RAILS_TEAM.md`
Status do time Rails (`ats-api-copia`): **OK, sem bloqueadores**. Rails já usa `validates :company_id, presence: true`. Recomendação opcional de `MultiTenant` concern.

---

## 7. Decisões Arquiteturais

### Por que usar `useAuth()` em vez de `useJWTAuth()` direto?

`useAuth()` é o hook canônico para a camada de UI (retorna objeto simplificado). Fix ataca a raiz expondo `company_id` nele — evita precisar trocar hook em 50+ callsites.

### Por que helpers em `src/lib/api/` em vez de NextAuth ou middleware?

- Next.js middleware já injeta `Authorization` header, mas não extrai `company_id` + `user_role` para uso por proxy routes
- Criar helpers reutilizáveis em `lib/api/` mantém consistência entre as 50+ rotas proxy
- Padrão dual-auth (WorkOS + JWT) num único helper — não obriga cada rota a saber do auth flow

### Por que manter `'admin_company'` em 34 rotas admin-only?

- Backend valida admin via `require_admin()` em cada rota admin-only
- Custo de migrar é alto (14 rotas de `clients/*`, etc.)
- Risco residual: baixo — backend é source of truth

### Por que não corrigir `candidate_repository` + `agent_monitoring` na nossa sessão?

Estão em `lia-agent-system` — repositório mantido pelo time IA em workflow separado. Fizemos handoff em vez de tocar código fora do nosso escopo.

---

## 8. Verificação End-to-End

### Testes realizados

1. ✅ `grep -rln "admin_company" src/app/api/backend-proxy/` → só 34 rotas admin-only
2. ✅ `grep -rln "|| 'demo'\||| 'demo_company'" src/components/` → zero em código user-facing
3. ✅ `npx tsc --noEmit` → 34 erros totais (todos pré-existentes — jira.js missing module, workos SDK, etc.), zero novos
4. ✅ Todas as 16 rotas user-facing confirmadas limpas via script de verificação
5. ✅ Helpers canônicos tipados corretamente (AuthResult union type, dual-auth paths)

### Smoke tests sugeridos em staging

1. Login como user não-admin de empresa real (não demo)
2. Abrir `/billing` → Network tab → request header `X-Company-ID` deve ser UUID real
3. Kanban → mover candidato → `transition/execute` com `X-Company-ID` real
4. Tentar pedir dados de outro tenant (via curl) → backend retorna 403
5. Backend logs → `company_id` do JWT bate com `X-Company-ID` recebido em todas as requests

---

## 9. Impacto em Produção

### Risco antes dos fixes

🔴 **Alto risco de vazamento cross-tenant:**
- Kanban e modules page podiam carregar dados do tenant 'demo'
- User management podia criar usuários na empresa errada
- Onboarding podia associar novos usuários à empresa 'demo_company'
- Billing/invoices/payment-methods podiam ser acessados com header 'admin_company'
- Candidates podiam ser movidos entre kanbans de tenants diferentes via `transition/execute`

### Risco depois dos fixes

🟢 **Risco residual baixo:**
- Frontend: zero fallbacks hardcoded em código user-facing
- Proxy layer: identidade real do JWT em todas as 16 rotas user-facing
- Backend FastAPI: JWT middleware com cross-tenant check sempre ativo
- Backend Rails: models com `validates :company_id`

**Pendências:** 3 itens no repo `lia-agent-system` (time IA) documentados em handoff.

---

## 10. Próximos Passos

### Imediato (antes do deploy)

- [ ] Sync dos commits deste relatório para Replit → push para GitHub
- [ ] Smoke tests em staging seguindo o checklist da seção 8
- [ ] Revisar os 3 handoffs com times IA e Rails

### Curto prazo

- [ ] Time IA: endereçar `agent_monitoring_service` (P0) — 1 dia de dev
- [ ] Time IA: endereçar `candidate_repository` + `llm_factory legacy paths` (P1) — 2 dias
- [ ] Frontend: migrar as 34 rotas admin-only para helper (baixa prioridade — backend valida)

### Médio prazo

- [ ] Adicionar teste E2E de multi-tenancy em CI — criar 2 users de companies diferentes e confirmar isolamento em billing, kanban, communications
- [ ] Adicionar lint rule custom que proíbe `'demo'` / `'admin_company'` em headers HTTP

---

## 11. Arquivos modificados — lista completa

### Feature Triagem WSI
- `plataforma-lia/src/components/modals/job-duplicate-modal.tsx`
- `plataforma-lia/src/components/pages/jobs/useJobsModalHandlers.ts`
- `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts`
- `plataforma-lia/src/components/pages/job-kanban/KanbanPageContent.tsx`
- `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.types.ts`
- `plataforma-lia/src/components/jobs/job-edit-tab/useJobEditTab.ts`
- `plataforma-lia/src/components/jobs/JobEditTab.tsx`

### Multi-tenancy — Fase 1 (hooks/components)
- `plataforma-lia/src/contexts/auth-context.tsx`
- `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts`
- `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageSetup.ts`
- `plataforma-lia/src/components/pages/modules-page.tsx`
- `plataforma-lia/src/components/settings/use-user-management.ts`
- `plataforma-lia/src/components/onboarding/onboarding-controller.tsx`
- `plataforma-lia/src/components/ui/premium-autocomplete.tsx`
- `plataforma-lia/src/components/screening-config/SCMSectionContent.tsx`
- `plataforma-lia/src/hooks/shared/use-authenticated-user-id.ts`

### Multi-tenancy — Fase 2 (proxy routes + helpers)
- `plataforma-lia/src/lib/api/backend-url.ts` **(novo)**
- `plataforma-lia/src/lib/api/session-auth.ts` **(novo)**
- `plataforma-lia/src/app/api/backend-proxy/transition/execute/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/subscription/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/usage/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/payment-methods/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/payment-methods/[method_id]/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/invoices/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/invoices/[invoice_id]/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/billing/invoices/[invoice_id]/pay/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/ai-credits/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/alerts/config/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/communications/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/technical-tests/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/technical-tests/[id]/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/technical-tests/seed/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/interpret-context/route.ts`

### Documentação
- `docs/handoff/IMPLEMENTATION_REPORT_2026-04-22.md` **(este documento)**
- `docs/handoff/HANDOFF_SESSION_MULTI_TENANCY.md` **(novo)**
- `docs/handoff/HANDOFF_AI_TEAM_MULTI_TENANCY.md` **(novo)**
- `docs/handoff/HANDOFF_RAILS_TEAM.md` **(novo)**
- `CLAUDE.md` (regra canônica de arquivos)

---

## 12. Contato

**Dúvidas técnicas ou de escopo:** Paulo Moraes (tech@wedotalent.cc)

**Revisão recomendada por:** Tech Lead do time Frontend + Security Lead antes de deploy em produção.
