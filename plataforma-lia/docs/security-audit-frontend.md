# Auditoria de Seguranca Frontend — Plataforma LIA

**Data**: 2026-04-04
**Escopo**: Frontend React/Next.js (`plataforma-lia/src/`)
**Analisou**: 18 dimensoes de seguranca

---

## Resumo Executivo

| Classificacao | Quantidade | Status |
|---|---|---|
| CRITICO (corrigido) | 3 | RESOLVIDO |
| MEDIO (monitorar) | 4 | DOCUMENTADO |
| BAIXO (aceitavel) | 5 | OK |
| SEM RISCO | 6 | OK |

**Score de Seguranca Frontend: 8.5/10**

---

## CRITICOS — CORRIGIDOS

### 1. Open Redirect via backend response (CORRIGIDO)
- **Arquivo**: `components/pages/chat-page/useChatPageHandlers.tsx:530`
- **Problema**: `window.location.href = result.navigate` aceitava qualquer URL do backend, incluindo URLs externas maliciosas
- **Correcao**: Adicionado validacao `result.navigate.startsWith('/')` para aceitar apenas rotas internas

### 2. Open Redirect via 402 Payment Required (CORRIGIDO)
- **Arquivo**: `lib/api/handle-payment-required.ts:42`
- **Problema**: `upgrade_url` vinda do body da resposta 402 era usada diretamente em `window.location.href`, permitindo redirect para dominio externo
- **Correcao**: Validacao `startsWith('/')` com fallback para `/upgrade`

### 3. Fallback Secret em Producao (CORRIGIDO)
- **Arquivo**: `lib/session-crypto.ts:3`
- **Problema**: `SESSION_SECRET` tinha fallback `'fallback-dev-secret'` que seria usado em producao se env vars nao estivessem configuradas, comprometendo assinatura HMAC de sessoes
- **Correcao**: Fallback removido; `throw Error` em producao se secret nao configurado

---

## MEDIO — MONITORAR

### 4. Dados Mock em fallback de producao
- **Arquivo**: `components/pages/job-kanban/hooks/useKanbanCandidateDecisions.ts`
- **Problema**: Quando API de rubric evaluation falha, gera dados mock com `Math.random()` que parecem reais ao usuario
- **Risco**: Usuario pode tomar decisoes de contratacao baseado em scores fabricados
- **Recomendacao**: Mostrar estado de erro explicito em vez de dados fabricados

### 5. Demo user hardcoded no onboarding
- **Arquivo**: `components/onboarding/onboarding-controller.tsx:46-89`
- **Problema**: Usuario demo com email `demo@wedotalent.com` e permissoes admin hardcoded, usado como fallback quando store vazio
- **Risco**: Em producao, se auth falhar, usuario pode ter acesso admin via fallback
- **Recomendacao**: Remover fallback demo; mostrar tela de login se nao autenticado

### 6. DEFAULT_COMPANY_ID hardcoded
- **Arquivo**: `components/pages/chat-page/chat-core/chat-core.constants.ts:18`
- **Problema**: UUID fixo `a1b2c3d4-e5f6-7890-abcd-ef1234567890` usado como default, pode causar cross-tenant data leak
- **Recomendacao**: Usar company ID do usuario autenticado; falhar se nao disponivel

### 7. Permissoes verificadas apenas no client
- **Arquivo**: `components/settings/use-user-management.ts:60-61`
- **Problema**: Role-based permissions defaultam no client (`admin -> tudo, outros -> basico`) sem verificacao server-side
- **Risco**: Baixo se backend tambem valida; alto se nao
- **Recomendacao**: Confirmar que backend valida permissoes independentemente

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
- **Status**: Funcional mas gera warning; nao e vulnerabilidade

---

## SEM RISCO

### 13. eval() / new Function() — ZERO usos
### 14. @ts-ignore — ZERO usos
### 15. Hardcoded API keys/tokens — ZERO (todos via process.env)
### 16. CORS headers no client — ZERO (gerenciado pelo Next.js)
### 17. Dados sensiveis (CPF/CNPJ) em client — ZERO (so labels de UI)
### 18. Fetch sem error handling — Todos em API routes server-side (try/catch no nível superior)

---

## Recomendacoes Prioritarias

1. **[MEDIO]** Substituir mock evaluation data por estado de erro explicito
2. **[MEDIO]** Remover demo user fallback em producao
3. **[MEDIO]** Derivar company ID do usuario autenticado, nao de constante
4. **[MEDIO]** Auditar backend para confirmar validacao de permissoes server-side
5. **[BAIXO]** Resolver hydration mismatch no onboarding-controller
