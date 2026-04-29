const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

/**
 * Dev auto-login is OFF by default — opt-in via explicit env var.
 *
 * Rationale (post-mortem 2026-04-29 wizard-domain-hint-leak audit):
 *   The previous default ("ON whenever NODE_ENV !== 'production'") masked
 *   real bugs in identity propagation. With auto-login enabled, every dev
 *   session impersonated a generic demo user — bypassing the actual JWT
 *   flow used in production. Symptoms observed in production-like Replit
 *   sessions:
 *     - Settings modal: "Empresa não identificada" (company_id missing
 *       because demo user JWT lacks it).
 *     - WS handshake: /api/auth/ws-token fetch failed × 3 (demo user not
 *       seeded → backend 401 → loop).
 *     - Backend handlers silently fall back to {company_id: "",
 *       user_id: "anonymous"} — direct violation of CLAUDE.md global rule
 *       #1 (multi-tenancy via JWT).
 *
 * Inverting the default to "OFF unless explicitly enabled" forces the
 * dev environment to exercise the same auth flow as production. Bugs in
 * identity propagation surface immediately instead of being masked.
 *
 * To re-enable for offline / CI / load-testing scenarios, set
 *   LIA_DEV_AUTO_LOGIN=true
 * AND ensure the demo user (DEV_AUTO_LOGIN_EMAIL / DEV_AUTO_LOGIN_PASSWORD,
 * or defaults demo@wedotalent.com / demo123) is seeded in the backend.
 *
 * Skill canônica: harness-engineering [guide computacional].
 */
const DEV_AUTO_LOGIN_ENABLED =
  process.env.LIA_DEV_AUTO_LOGIN === 'true' &&
  process.env.NODE_ENV !== 'production'

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
