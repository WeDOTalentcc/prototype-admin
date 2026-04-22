const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const DEV_AUTO_LOGIN_ENABLED = process.env.NODE_ENV !== 'production'

const DEV_TOKEN_TTL_MS = 25 * 60 * 1000

export interface DevLoginResult {
  accessToken: string
  refreshToken?: string
}

let cachedDevToken: { token: string; expiresAt: number } | null = null

export function isDevAutoLoginEnabled(): boolean {
  return DEV_AUTO_LOGIN_ENABLED
}

const REMEDIATION_HINT =
  'check DEV_AUTO_LOGIN_EMAIL/DEV_AUTO_LOGIN_PASSWORD env vars or re-seed the demo user in lia-backend'

let lastFailureLogAt = 0
const FAILURE_LOG_THROTTLE_MS = 30 * 1000

function logDevAutoLoginFailure(detail: string): void {
  const now = Date.now()
  if (now - lastFailureLogAt < FAILURE_LOG_THROTTLE_MS) return
  lastFailureLogAt = now
  // [Task #801 C3] degradado para `warn`: cold-start temporário de backend
  // não é erro acionável (é retentado automaticamente). Mantemos throttle
  // para sinalizar quando a indisponibilidade persiste >30s.
  // eslint-disable-next-line no-console
  console.warn(
    `[dev-auto-login] demo user login unavailable — ${detail}. Remediation: ${REMEDIATION_HINT}`,
  )
}

// Task #801 (C3): backend cold-start no Replit demora ~3-15s. Uma única
// tentativa de login falha sob TypeError("Failed to fetch") e o front fica
// sem token até o próximo focus(), gerando o sintoma "Funil sem candidatos".
// Reententamos com backoff até ~31s.
const DEV_LOGIN_BACKOFFS_MS = [1000, 2000, 4000, 8000, 16000] as const

function isTransientFetchError(err: unknown): boolean {
  if (err instanceof TypeError) {
    const m = (err.message || '').toLowerCase()
    return (
      m.includes('failed to fetch') ||
      m.includes('networkerror') ||
      m.includes('load failed') ||
      m.includes('fetch failed')
    )
  }
  if (err instanceof DOMException && err.name === 'TimeoutError') return true
  if (err && typeof err === 'object' && 'cause' in err) {
    return isTransientFetchError((err as { cause?: unknown }).cause)
  }
  return false
}

async function attemptLogin(
  url: string,
  email: string,
  password: string,
): Promise<{ ok: true; data: any } | { ok: false; transient: boolean; detail: string }> {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      signal: AbortSignal.timeout(15000),
    })
    if (!res.ok) {
      let bodySnippet = ''
      try {
        const text = await res.text()
        bodySnippet = text.slice(0, 200)
      } catch {
        bodySnippet = '<unreadable body>'
      }
      return {
        ok: false,
        transient: res.status >= 500 || res.status === 502 || res.status === 503,
        detail: `responded ${res.status} ${res.statusText} (body: ${bodySnippet})`,
      }
    }
    const data = await res.json()
    return { ok: true, data }
  } catch (err) {
    const message = err instanceof Error ? `${err.name}: ${err.message}` : String(err)
    return {
      ok: false,
      transient: isTransientFetchError(err),
      detail: `network error (${message})`,
    }
  }
}

export async function loginDemoUser(): Promise<DevLoginResult | null> {
  const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
  const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'
  const url = `${BACKEND_URL}/api/v1/auth/login`

  let lastDetail = ''
  for (let attempt = 0; attempt <= DEV_LOGIN_BACKOFFS_MS.length; attempt++) {
    const result = await attemptLogin(url, demoEmail, demoPassword)
    if (result.ok) {
      const data = result.data
      const accessToken = data.access_token || data?.data?.access_token
      if (!accessToken) {
        logDevAutoLoginFailure(
          `backend response for ${demoEmail} is missing access_token (keys: ${Object.keys(data || {}).join(',') || 'none'})`,
        )
        return null
      }
      const refreshToken = data.refresh_token || data?.data?.refresh_token
      return { accessToken, refreshToken }
    }

    lastDetail = result.detail
    // Erro determinístico (4xx etc.) ou último attempt: desiste.
    if (!result.transient || attempt === DEV_LOGIN_BACKOFFS_MS.length) break
    const delay = DEV_LOGIN_BACKOFFS_MS[attempt]
    await new Promise(r => setTimeout(r, delay))
  }

  logDevAutoLoginFailure(
    `backend ${url} unreachable for ${demoEmail} after ${DEV_LOGIN_BACKOFFS_MS.length + 1} attempts: ${lastDetail}`,
  )
  return null
}

export async function getDevToken(): Promise<string | null> {
  if (cachedDevToken && cachedDevToken.expiresAt > Date.now()) {
    return cachedDevToken.token
  }
  const result = await loginDemoUser()
  if (!result) return null
  cachedDevToken = {
    token: result.accessToken,
    expiresAt: Date.now() + DEV_TOKEN_TTL_MS,
  }
  return result.accessToken
}

export function clearCachedDevToken(): void {
  cachedDevToken = null
}
