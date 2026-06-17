/**
 * Pure helpers para mensagens de erro PT-BR dos endpoints de JD (geração + avaliação).
 *
 * Canonical-fix #1165 (Bugs A + B): callsites do frontend mascaravam status reais do
 * backend num único `setEvaluation(null)` / "Faltam dados...". Estes helpers
 * discriminam os caminhos (rede / 401-403 / 422 / 5xx / 200-malformado) e
 * preservam mensagem real do backend quando o erro vem do FairnessGuard.
 *
 * Mantenha SEM fallback silencioso: cada bucket retorna uma mensagem específica
 * para que o recrutador entenda o que aconteceu.
 */

type Detail422 = {
  message?: unknown
  lia_suggestion?: unknown
  detail?: unknown
}

/**
 * Extrai uma mensagem textual do payload 422 do backend, cobrindo os 3 formatos
 * vistos em produção:
 *   1. `{ detail: { message: "..." } }` (FairnessGuard / serviços internos)
 *   2. `{ detail: [{ loc, msg, type }, ...] }` (Pydantic validation)
 *   3. `{ detail: "..." }` ou `{ message: "..." }` (variantes legadas)
 */
export function extractBackendMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null
  const p = payload as Detail422
  if (typeof p.message === "string" && p.message.trim()) return p.message.trim()
  if (typeof p.lia_suggestion === "string" && p.lia_suggestion.trim())
    return p.lia_suggestion.trim()

  const detail = p.detail
  if (typeof detail === "string" && detail.trim()) return detail.trim()
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const inner = detail as Detail422
    if (typeof inner.message === "string" && inner.message.trim())
      return inner.message.trim()
    if (typeof inner.lia_suggestion === "string" && inner.lia_suggestion.trim())
      return inner.lia_suggestion.trim()
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: unknown }
    if (first && typeof first.msg === "string" && first.msg.trim())
      return first.msg.trim()
  }
  return null
}

/**
 * Mapeia status + body do POST /jd/generate para uma mensagem PT-BR específica.
 * Bug B (Task #1165): antes, qualquer 422 mostrava "Faltam dados na vaga..."
 * mesmo quando o backend devolvia uma razão real do FairnessGuard.
 */
export function mapJDGenerateErrorMessage(
  status: number,
  payload: unknown
): string {
  if (status === 401 || status === 403) {
    return "Sua sessão expirou. Recarregue a página e tente novamente."
  }
  if (status === 422) {
    const backendMsg = extractBackendMessage(payload)
    if (backendMsg) return backendMsg
    return "Faltam dados na vaga para gerar a descrição. Preencha responsabilidades e competências antes de tentar novamente."
  }
  if (status >= 500) {
    return "Tivemos um problema no servidor ao gerar a descrição. Tente novamente em alguns instantes."
  }
  return "Não consegui gerar a descrição agora. Tente novamente em instantes."
}

/**
 * Mapeia status do POST /wsi/jd-evaluate para mensagem PT-BR específica.
 * Bug A (Task #1165): antes, qualquer não-422/não-ok virava `setEvaluation(null)`
 * silencioso. Agora classificamos rede / auth / 5xx separadamente.
 */
export function mapJDEvaluationErrorMessage(
  status: number | "network"
): string {
  if (status === "network") {
    return "Falha de conexão ao avaliar a descrição. Verifique sua internet e tente novamente."
  }
  if (status === 401 || status === 403) {
    return "Sua sessão expirou. Recarregue a página e tente novamente."
  }
  if (status >= 500) {
    return "Tivemos um problema no servidor ao avaliar a descrição. Tente novamente em alguns instantes."
  }
  return "Não foi possível avaliar a descrição agora. Tente novamente."
}
