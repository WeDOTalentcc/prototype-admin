/**
 * Helper canônico para desembrulhar o envelope adicionado pelo
 * `ResponseEnvelopeMiddleware` do FastAPI (lia-agent-system).
 *
 * Sucesso 2xx: `{ ok: true, data: <payload>, meta: { request_id, ts } }`
 * Erro: `{ error: true, status_code: number, message: <payload>, request_id }`
 *
 * O proxy factory `createProxyHandlers` (`src/lib/api/proxy-handler.ts` L263)
 * já faz unwrap no caminho de sucesso. Os 3 proxies manuais da aba "Descrição
 * do Cargo" (`jd/extract`, `jd/generate`, `wsi/jd-evaluate`) foram escritos
 * antes desse padrão e estavam devolvendo o envelope intacto — quebrando o
 * hook `useJDEvaluation` (que procura `data.success` no topo) e o mapper
 * `extractBackendMessage` (que procura `detail`/`message` string mas recebia
 * objeto aninhado).
 *
 * Task #1167 (3 bugs novos após #1165): canonical-fix na borda do proxy.
 */

export function unwrapEnvelopeSuccess(data: unknown): unknown {
  if (
    data &&
    typeof data === "object" &&
    !Array.isArray(data) &&
    "ok" in data &&
    "data" in data
  ) {
    return (data as Record<string, unknown>).data
  }
  return data
}

export function unwrapEnvelopeError(data: unknown): unknown {
  if (
    data &&
    typeof data === "object" &&
    !Array.isArray(data) &&
    "error" in data &&
    "message" in data
  ) {
    // Envelope de erro envelopa o payload original sob `message`. Para que o
    // mapper de erros do frontend (`extractBackendMessage`) consiga achar
    // `detail`/`message`/`lia_suggestion`, devolvemos o payload original
    // quando ele já é um objeto (FastAPI HTTPException com detail estruturado).
    // Se `message` for string, devolvemos `{ detail: string }` para o mapper
    // pegar via `typeof detail === "string"`.
    const inner = (data as Record<string, unknown>).message
    if (inner && typeof inner === "object") {
      // Cobre 2 formatos:
      //  - FastAPI HTTPException(detail={error, field, message, ...}) — objeto
      //  - Pydantic ValidationError detail=[{loc, msg, type}, ...] — array
      // Em ambos, devolvemos `{ detail: inner }` para casar com o formato
      // canônico que o mapper espera (`{ detail: { message: "..." } }` ou
      // `{ detail: [...] }`).
      return { detail: inner }
    }
    if (typeof inner === "string") {
      return { detail: inner }
    }
  }
  return data
}
