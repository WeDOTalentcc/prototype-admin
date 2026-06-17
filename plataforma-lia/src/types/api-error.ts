export interface ApiErrorResponse {
  detail?: string
  error?: string
  message?: string
  request_id?: string
  [key: string]: unknown
}

export function extractRequestId(error: unknown): string {
  if (!error || typeof error !== "object") return "unknown"
  const e = error as Record<string, unknown>
  if (typeof e["request_id"] === "string") return e["request_id"]
  const resp = e["response"]
  if (resp && typeof resp === "object") {
    const data = (resp as Record<string, unknown>)["data"]
    if (data && typeof data === "object") {
      const rid = (data as Record<string, unknown>)["request_id"]
      if (typeof rid === "string") return rid
    }
    const headers = (resp as Record<string, unknown>)["headers"]
    if (headers && typeof headers === "object") {
      const xrid = (headers as Record<string, unknown>)["x-request-id"]
      if (typeof xrid === "string") return xrid
    }
  }
  return "unknown"
}
