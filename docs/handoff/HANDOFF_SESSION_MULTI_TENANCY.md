# Handoff — Sessão Multi-tenancy Production Readiness

**Data:** 2026-04-22
**Autor:** Paulo Moraes + Claude Code
**Branch:** `fix/kanban-e2e-bugs`
**Commits:** `a599487d` + `<novo commit desta sessão>`

---

## Sumário Executivo

Esta sessão fechou uma auditoria exaustiva de multi-tenancy na plataforma LIA. Foram corrigidos **26 pontos** no frontend (10 hooks/components + 16 proxy routes) que expunham dados cross-tenant via fallbacks hardcoded `'demo'` / `'demo_company'` / `'admin_company'`.

Três frentes ainda pendentes foram documentadas em handoffs específicos para os times responsáveis (IA e Rails).

---

## O que foi feito nesta sessão

### 1. Fixes de `company_id` em hooks e components (commit `a599487d`)

**Causa raiz:** `useAuth()` hook em `auth-context.tsx` não expunha `company_id` (só `company` = nome da empresa). Todos os consumidores faziam fallback para strings hardcoded.

| Arquivo | Fix | Severity |
|---------|-----|----------|
| `src/contexts/auth-context.tsx` | `useAuth()` passa a expor `company_id` (UUID) | P0 ROOT CAUSE |
| `src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` | `.company\|\|'demo'` → `.company_id\|\|''` | P0 |
| `src/components/pages/job-kanban/hooks/useKanbanPageSetup.ts` | Mesmo padrão | P0 |
| `src/components/pages/modules-page.tsx` | `.company\|\|"demo_company"` → `.company_id\|\|''` | P0 |
| `src/components/settings/use-user-management.ts` (4x) | Early return em vez de `\|\|'demo_company'` | P1 |
| `src/components/onboarding/onboarding-controller.tsx` (2x) | `\|\|'demo_company'` → `\|\|''` / env var | P1 |
| `src/components/ui/premium-autocomplete.tsx` | Default `"demo"` → `''` | P1 |
| `src/components/screening-config/SCMSectionContent.tsx` | Lê `company_id` (snake_case API) com fallback | P2 |
| `src/hooks/shared/use-authenticated-user-id.ts` | Widened type de `resolveUserId` | P2 |

### 2. Fixes de rotas proxy Next.js (commit novo)

**Padrão corrigido:**
```typescript
// ANTES — X-Company-ID sempre 'admin_company'
'X-Company-ID': request.headers.get('X-Company-ID') || 'admin_company'

// DEPOIS — extrai do JWT da sessão (WorkOS ou email/senha)
const auth = await getSessionAuth()
if (!auth.success) return auth.response
// fetch(..., { headers: auth.headers })
```

**Novos helpers canônicos criados:**
- `src/lib/api/backend-url.ts` — `BACKEND_URL` centralizado
- `src/lib/api/session-auth.ts` — `getSessionAuth()` com dual-auth (WorkOS SSO + JWT email/senha)

**16 rotas user-facing corrigidas:**

| Rota | Impacto |
|------|---------|
| `transition/execute/route.ts` | 🔴 HIGH SECURITY — prevenia mover candidato cross-tenant |
| `billing/route.ts`, `billing/subscription`, `billing/usage` | Billing user vazava admin |
| `billing/payment-methods/*` (2 rotas) | Payment methods cross-tenant |
| `billing/invoices/*` (3 rotas) | Invoices cross-tenant |
| `ai-credits/route.ts` | AI consumption cross-tenant |
| `alerts/config/route.ts` | Alert config cross-tenant |
| `communications/route.ts` | Communications cross-tenant |
| `technical-tests/*` (3 rotas) | Tests técnicos cross-tenant |
| `interpret-context/route.ts` | LIA feature cross-tenant |

**34 rotas admin-only mantidas intactas** (clients/*, policies/*, observability, default-templates/*, saas-metrics/*, global-policies/*) — backend valida via `require_admin()`.

### 3. Feature Triagem WSI — 100% implementada

7 componentes verificados no código real:
- Modal Duplicar Vaga com seção "TRIAGEM WSI" (3 opções: keep / regenerate_lia / manual)
- Navegação pós-duplicação via URL params
- LIA sidebar ativado no tab "edit" do job kanban
- `initialSection` prop propagado através de `JobEditTab` → `useJobEditTab`

---

## O que fica pendente — Handoffs

### Time IA (`lia-agent-system` — repo separado)

**Documento:** [HANDOFF_AI_TEAM_MULTI_TENANCY.md](./HANDOFF_AI_TEAM_MULTI_TENANCY.md)

Escopo:
1. `agent_monitoring_service.get_all_agents_summary()` — falta escopo por company_id (P0)
2. `candidate_repository.search()` e `find_by_email()` — falta filtro company_id (P1)
3. LLM factory — 2 code paths legados sem `company_id` em `get_provider_for_tenant()` (P1)
4. Checklist de produção para LLM factory (ENCRYPTION_KEY, Redis budget keys, cache invalidation)

### Time Rails (`ats-api-copia` — repo separado)

**Documento:** [HANDOFF_RAILS_TEAM.md](./HANDOFF_RAILS_TEAM.md)

Rails está OK — nenhum gap identificado. Recomendação opcional de `MultiTenant` concern.

---

## Verificação da nossa parte

1. ✅ `grep -rln "admin_company" src/app/api/backend-proxy/` — só aparece em 34 rotas admin-only
2. ✅ `npx tsc --noEmit` — 34 erros totais (pré-existentes, sem novos)
3. ✅ Todas as 16 rotas user-facing confirmadas limpas
4. ✅ Helpers canônicos (`backend-url.ts`, `session-auth.ts`) tipados corretamente

---

## Como testar em produção

1. Login como usuário não-admin de empresa não-demo
2. Abrir `/billing` → Network tab: `X-Company-ID` deve ser UUID real, não `'admin_company'`
3. Abrir Kanban → mover candidato → Network tab em `transition/execute`: `X-Company-ID` real
4. Verificar logs backend: `company_id` do JWT bate com `X-Company-ID` em todas as requests
5. Tentar acessar recurso de outro tenant (ID de outra empresa) → backend retorna 403

---

## Arquitetura restante para produção

Estes itens foram identificados mas estão fora do escopo do frontend:

- **Backend `auth_enforcement.py`** está correto — valida JWT vs X-Company-ID com cross-tenant check (linhas 268-281)
- **Backend `tenant_guard.py`** expõe `get_verified_company_id()` — dependency injection padrão
- **LLM factory** em geral está production-grade (BYOK com Fernet encryption, TenantProviderRegistry)

Os gaps remanescentes estão documentados nos handoffs por time.
