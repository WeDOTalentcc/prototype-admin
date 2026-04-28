/**
 * apiFetch — wrapper canônico para chamadas autenticadas ao backend.
 *
 * Política explícita (Audit Configurações Fase 3 — D-4):
 * - `credentials: 'include'`: garante envio de cookies HttpOnly mesmo em
 *   cenários cross-origin (deploy multi-domínio, preview branches, mobile
 *   webview). Same-origin já enviaria por padrão; tornar explícito documenta
 *   a intenção de segurança e evita regressões silenciosas.
 *
 * Uso obrigatório em qualquer fetch contra `/api/backend-proxy/...` ou
 * endpoints autenticados. Para chamadas públicas (CDN, recursos estáticos),
 * use o `fetch` nativo.
 *
 * Compatível com `Request | URL | string` e RequestInit completo. Headers
 * passados pelo caller têm precedência sobre os padrões.
 */
export function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, {
    credentials: "include",
    ...init,
  })
}
