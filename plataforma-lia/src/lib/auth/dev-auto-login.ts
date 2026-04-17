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
  // eslint-disable-next-line no-console
  console.error(
    `[dev-auto-login] DEMO USER LOGIN FAILED — ${detail}. Remediation: ${REMEDIATION_HINT}`,
  )
}

export async function loginDemoUser(): Promise<DevLoginResult | null> {
  const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
  const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: demoEmail, password: demoPassword }),
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
      logDevAutoLoginFailure(
        `backend ${BACKEND_URL}/api/v1/auth/login responded ${res.status} ${res.statusText} for ${demoEmail} (body: ${bodySnippet})`,
      )
      return null
    }
    const data = await res.json()
    const accessToken = data.access_token || data?.data?.access_token
    if (!accessToken) {
      logDevAutoLoginFailure(
        `backend response for ${demoEmail} is missing access_token (keys: ${Object.keys(data || {}).join(',') || 'none'})`,
      )
      return null
    }
    const refreshToken = data.refresh_token || data?.data?.refresh_token
    return { accessToken, refreshToken }
  } catch (err) {
    const message = err instanceof Error ? `${err.name}: ${err.message}` : String(err)
    logDevAutoLoginFailure(
      `network error contacting ${BACKEND_URL}/api/v1/auth/login for ${demoEmail} (${message})`,
    )
    return null
  }
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
