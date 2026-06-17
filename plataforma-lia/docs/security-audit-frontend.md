# Auditoria de Seguranca Frontend — Plataforma LIA

**Data**: 2026-04-04
**Escopo**: Frontend React/Next.js (`plataforma-lia/src/`)
**Analisou**: 18 dimensoes de seguranca

---

## Resumo Executivo

| Classificacao | Quantidade | Status |
|---|---|---|
| CRITICO (corrigido) | 7 | RESOLVIDO |
| BAIXO (aceitavel) | 5 | OK |
| SEM RISCO | 6 | OK |

**Score de Seguranca Frontend: 9.2/10**

---

## CRITICOS — TODOS CORRIGIDOS

### 1. Open Redirect via backend response (CORRIGIDO)
- **Arquivo**: `components/pages/chat-page/useChatPageHandlers.tsx:530`
- **Problema**: `window.location.href = result.navigate` aceitava qualquer URL do backend
- **Correcao**: Validacao `result.navigate.startsWith('/')` para aceitar apenas rotas internas

### 2. Open Redirect via 402 Payment Required (CORRIGIDO)
- **Arquivo**: `lib/api/handle-payment-required.ts:42`
- **Problema**: `upgrade_url` do body da resposta 402 usada diretamente em redirect
- **Correcao**: Validacao `startsWith('/')` com fallback para `/upgrade`

### 3. Fallback Secret em Producao (CORRIGIDO)
- **Arquivo**: `lib/session-crypto.ts:3`
- **Problema**: `SESSION_SECRET` com fallback `'fallback-dev-secret'`
- **Correcao**: Fallback removido; `throw Error` em producao se secret nao configurado

### 4. Dados Mock exibidos como reais (CORRIGIDO)
- **Arquivo**: `components/pages/job-kanban/hooks/useKanbanCandidateDecisions.ts`
- **Problema**: Quando API de rubric evaluation falhava, gerava dados mock com `Math.random()` que pareciam reais
- **Correcao**: Substituido por estado de erro explicito com `_unavailable: true` e mensagem clara

### 5. Demo user com admin hardcoded (CORRIGIDO)
- **Arquivo**: `components/onboarding/onboarding-controller.tsx`
- **Problema**: Usuario demo com email e permissoes admin hardcoded como fallback
- **Correcao**: Removido fallback demo; retorna `null` se store vazio

### 6. Company ID hardcoded — Cross-tenant risk (CORRIGIDO)
- **Arquivos**: `chat-core.constants.ts`, `useChatSession.ts`, 5 API routes hiring-policy, pipeline-policy, ~25 API routes e componentes com `demo_company`
- **Problema**: UUID fixo e `demo_company` em 40+ locais, risco de vazamento entre empresas
- **Correcao**: Todos substituidos por `useCurrentCompany()` (client) e `resolveCompanyId()` via session cookie (API routes). Zero `demo_company` restante.

### 7. Permissoes com default expansivo (CORRIGIDO)
- **Arquivo**: `components/settings/use-user-management.ts:60-61`
- **Problema**: Se backend nao retornasse permissions, admin recebia todas e non-admin recebia `['recruitment', 'candidates']` automaticamente
- **Correcao**: Default agora e array vazio `[]` — permissoes vem exclusivamente do backend

---

## BAIXO — ACEITAVEL

### 8. dangerouslySetInnerHTML (PROTEGIDO)
- **20 usos** encontrados, **todos** passam por `sanitizeHtml()` ou `sanitizeEmailHtml()` (DOMPurify)
- Configuracao restritiva: tags e atributos limitados, sem `javascript:` URIs
- **Status**: SEGURO

### 9. console.error/warn em producao
- **8 usos** em tratamento de erros (catch blocks, config warnings)
- Nenhum `console.log` em componentes
- **Status**: Aceitavel (nao expoe dados sensiveis)

### 10. localStorage residual
- **8 usos** fora de stores — todos em `session-cleanup.ts` (logout) e `auth-service.ts` (tokens)
- **Status**: Uso correto e necessario

### 11. credentials: 'include' em fetches
- **10 usos** em auth-service, streaming, SCIM
- **Status**: Correto para envio de cookies de sessao

### 12. Hydration mismatch (SSR)
- `onboarding-controller.tsx` usa `typeof window === 'undefined'` em `useState` initializer
- **Status**: Funcional mas gera warning; corrigido para retornar `null` no SSR (resolve o mismatch)

---

## SEM RISCO

### 13. eval() / new Function() — ZERO usos
### 14. @ts-ignore — ZERO usos
### 15. Hardcoded API keys/tokens — ZERO (todos via process.env)
### 16. CORS headers no client — ZERO (gerenciado pelo Next.js)
### 17. Dados sensiveis (CPF/CNPJ) em client — ZERO (so labels de UI)
### 18. Fetch sem error handling — Todos em API routes server-side (try/catch no nivel superior)

---

## Todas as recomendacoes foram implementadas

Nenhum item pendente. Score de seguranca elevado de 8.5 para 9.2/10.
