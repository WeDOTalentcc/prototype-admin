/**
 * Extrai a mensagem de erro mais legível possível de uma resposta do backend
 * passando pelo proxy `createProxyHandlers` (src/lib/api/proxy-handler.ts).
 *
 * O proxy envia 4xx/5xx como:
 *   { error: "Backend error on POST /...", details: { status_code, message, ... } }
 *
 * Handlers FastAPI podem retornar `detail` (string) ou `{ message, detail, ... }`.
 * Essa função cobre os três formatos e devolve sempre uma string.
 *
 * Uso:
 *   if (!res.ok) {
 *     const errBody = await res.json().catch(() => ({}))
 *     throw new Error(extractErrorMessage(errBody, res.status))
 *   }
 */
export function extractErrorMessage(errorBody: unknown, statusCode?: number): string {
  if (!errorBody || typeof errorBody !== "object") {
    return statusCode ? `Erro ${statusCode}` : "Erro desconhecido"
  }

  const body = errorBody as Record<string, unknown>

  // Formato envelopado pelo nosso proxy: { error, details: { message | detail | ... } }
  const details = body.details
  if (details && typeof details === "object") {
    const d = details as Record<string, unknown>
    if (typeof d.message === "string" && d.message) return d.message
    if (typeof d.detail === "string" && d.detail) return d.detail
    if (typeof d.error === "string" && d.error) return d.error
  }

  // Formato direto do FastAPI: { detail: "..." } ou { detail: { message } }
  if (typeof body.detail === "string" && body.detail) return body.detail
  if (body.detail && typeof body.detail === "object") {
    const dd = body.detail as Record<string, unknown>
    if (typeof dd.message === "string" && dd.message) return dd.message
  }

  // Formato simples: { message: "..." } ou { error: "..." }
  if (typeof body.message === "string" && body.message) return body.message
  if (typeof body.error === "string" && body.error) return body.error

  return statusCode ? `Erro ${statusCode}` : "Erro desconhecido"
}
