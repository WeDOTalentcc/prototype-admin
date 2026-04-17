/**
 * Bug #303 / Task #305 — shared helpers for handling session-expired (401/403)
 * and error normalization on `/api/lia/*` calls. Extracted so any LIA-API
 * module can reuse the same behavior:
 *   - normalize backend errors into `Error & { status }`
 *   - preserve `detail` / `error` payloads when present
 *   - on 401/403, redirect to `/login?reason=session_expired` (same target as
 *     `useSessionRefresh`), avoiding the Next dev overlay and silent failures
 *     in production.
 */

export function handleSessionExpiredRedirect(): void {
  if (typeof window === 'undefined') return
  if (window.location.pathname.startsWith('/login')) return
  window.location.href = '/login?reason=session_expired'
}

export type LiaApiError = Error & { status: number }

export async function buildLiaApiError(
  response: Response,
  fallbackMessage: string,
): Promise<LiaApiError> {
  let message = fallbackMessage
  try {
    const body = await response.json()
    if (body?.detail && typeof body.detail === 'string') message = body.detail
    else if (body?.error && typeof body.error === 'string') message = body.error
  } catch {
    if (response.statusText) message = `${fallbackMessage}: ${response.statusText}`
  }
  const err = new Error(message) as LiaApiError
  err.status = response.status
  return err
}

export async function throwLiaApiError(
  response: Response,
  fallbackMessage: string,
): Promise<never> {
  const err = await buildLiaApiError(response, fallbackMessage)
  if (response.status === 401 || response.status === 403) {
    handleSessionExpiredRedirect()
  }
  throw err
}
