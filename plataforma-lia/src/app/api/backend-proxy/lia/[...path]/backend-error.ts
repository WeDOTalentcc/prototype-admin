// Extraido de route.ts: route handlers do Next so podem exportar
// GET/POST/etc + config. Helper movido para modulo irmao (Task #1177).

export function isBackendUnavailableError(error: unknown): {
  unavailable: boolean
  code: string
} {
  if (!error) return { unavailable: false, code: 'unknown' }
  const err = error as { name?: unknown; code?: unknown; cause?: unknown; message?: unknown }
  const name = typeof err.name === 'string' ? err.name : ''
  const message = typeof err.message === 'string' ? err.message : ''
  const directCode = typeof err.code === 'string' ? err.code : ''
  const causeCode =
    err.cause && typeof err.cause === 'object' && err.cause !== null
      ? (() => {
          const c = err.cause as { code?: unknown }
          return typeof c.code === 'string' ? c.code : ''
        })()
      : ''
  const code = directCode || causeCode || ''
  if (name === 'AbortError' || name === 'TimeoutError') {
    return { unavailable: true, code: code || 'TIMEOUT' }
  }
  if (
    code === 'ECONNREFUSED' ||
    code === 'ENOTFOUND' ||
    code === 'ECONNRESET' ||
    code === 'EAI_AGAIN' ||
    code === 'UND_ERR_SOCKET' ||
    code === 'UND_ERR_CONNECT_TIMEOUT'
  ) {
    return { unavailable: true, code }
  }
  // `undici` raises a bare TypeError("fetch failed") whose .cause carries
  // the syscall info; if we made it here without matching a code but the
  // message looks like a connection failure, treat it as transient.
  if (name === 'TypeError' && /fetch failed/i.test(message)) {
    return { unavailable: true, code: code || 'FETCH_FAILED' }
  }
  return { unavailable: false, code: code || name || 'unknown' }
}
