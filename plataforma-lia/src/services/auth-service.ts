const AUTH_API_URL = '/api/backend-proxy/auth'
const SESSION_API_URL = '/api/auth/session'
const WORKOS_SSO_URL = '/api/auth/workos/sso'
const WORKOS_SESSION_URL = '/api/auth/workos/session'

const ME_REQUEST_TIMEOUT_MS = 12000

export type AuthMethod = 'jwt' | 'sso' | 'dev-auto-login'

/**
 * WT-2022 P0.RBAC (registrado 2026-05-21):
 *
 * `User.role` aqui é a TAXONOMIA CANONICAL de autenticação — vem do JWT/backend.
 * Valores: `'admin' | 'recruiter' | 'viewer' | 'wedotalent_admin'`.
 *
 * É o que `useAuth()` expõe pro app inteiro e o que TODOS os gates de UI
 * devem consumir (`user?.role === 'wedotalent_admin'` etc.). C1 hotfix
 * (commit ed25753c4) adicionou `wedotalent_admin` para staff WeDOTalent
 * que edita tenant_overrides via admin2.wedotalent.cc.
 *
 * NÃO confundir com `UserRole` em `src/utils/permissions.ts` /
 * `src/lib/permissions.ts` — esses são taxonomias LEGADAS de
 * client-side RBAC, sem consumers externos atualmente. Sistemas paralelos
 * com semantics diferentes; ver headers desses arquivos para detalhes.
 */
export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'recruiter' | 'viewer' | 'wedotalent_admin'
  is_active: boolean
  created_at: string
  updated_at: string
  company_id?: string
  company?: string
  avatar_url?: string | null
  sso_provider?: string | null
}

export interface SSOUser {
  id: string
  email: string
  name: string
  firstName: string | null
  lastName: string | null
  organizationId: string | null
  connectionType: string
  authMethod: 'sso'
  // R-020 P0-C: SSO users may carry company_id from JWT claims
  company_id?: string
}

export type AuthenticatedUser = User | SSOUser

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthError {
  error: string
  details?: Record<string, unknown>
}

export interface SSOSessionResponse {
  authenticated: boolean
  user?: SSOUser
  reason?: string
}

function getCookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

class AuthService {
  constructor() {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('auth_method')
      } catch {
      }
    }
  }

  getAuthMethod(): AuthMethod | null {
    if (typeof window === 'undefined') return null
    return getCookieValue('lia_auth_method') as AuthMethod | null
  }

  async setTokens(accessToken: string, refreshToken: string): Promise<void> {
    const response = await fetch(SESSION_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        access_token: accessToken,
        refresh_token: refreshToken,
        auth_method: 'jwt',
      }),
    })
    if (!response.ok) {
      throw new Error(`Failed to set session tokens: ${response.status}`)
    }
  }

  async clearTokens(): Promise<void> {
    await fetch(SESSION_API_URL, {
      method: 'DELETE',
      credentials: 'include',
    })
  }

  isAuthenticated(): boolean {
    return !!getCookieValue('lia_auth_method')
  }

  isJWTAuthenticated(): boolean {
    return getCookieValue('lia_auth_method') === 'jwt'
  }

  initiateSSO(options: {
    organization?: string
    connection?: string
    email?: string
    returnTo?: string
  }): void {
    const params = new URLSearchParams()
    if (options.organization) params.set('organization', options.organization)
    if (options.connection) params.set('connection', options.connection)
    if (options.email) params.set('email', options.email)
    if (options.returnTo) params.set('returnTo', options.returnTo)

    window.location.href = `${WORKOS_SSO_URL}?${params.toString()}`
  }

  async checkSSOSession(): Promise<SSOSessionResponse> {
    try {
      const response = await fetch(WORKOS_SESSION_URL, {
        method: 'GET',
        credentials: 'include',
      })

      if (!response.ok) {
        return { authenticated: false }
      }

      const data: SSOSessionResponse = await response.json()
      if (data.authenticated && data.user) {
        await fetch(SESSION_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ access_token: '_sso_session_', auth_method: 'sso', is_sso: true }),
        })
      }
      return data
    } catch {
      return { authenticated: false }
    }
  }

  async logoutSSO(): Promise<void> {
    try {
      await fetch(WORKOS_SESSION_URL, {
        method: 'DELETE',
        credentials: 'include',
      })
    } catch {
    }
    await this.clearTokens()
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${AUTH_API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error: AuthError = await response.json().catch(() => ({ 
        error: 'Login failed' 
      }))
      throw new Error(error.error || 'Invalid email or password')
    }

    const data: TokenResponse = await response.json()
    await this.setTokens(data.access_token, data.refresh_token)
    if (typeof document !== 'undefined') {
      document.cookie = 'lia_logged_out=; path=/; max-age=0; SameSite=None; Secure'
    }
    return data
  }

  async register(email: string, password: string, name: string, role: string = 'viewer'): Promise<User> {
    const response = await fetch(`${AUTH_API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name, role }),
    })

    if (!response.ok) {
      const error: AuthError = await response.json().catch(() => ({ 
        error: 'Registration failed' 
      }))
      throw new Error(error.error || 'Failed to register')
    }

    return response.json()
  }

  async refreshToken(): Promise<void> {
    const response = await fetch(`${SESSION_API_URL}/refresh`, {
      method: 'POST',
      credentials: 'include',
      signal: AbortSignal.timeout(ME_REQUEST_TIMEOUT_MS),
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }
  }

  async getMe(): Promise<User> {
    if (!this.isAuthenticated()) {
      throw new Error('No active session')
    }

    return this.getMeDirect()
  }

  async getMeDirect(): Promise<User> {
    const response = await fetch(`${AUTH_API_URL}/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      signal: AbortSignal.timeout(ME_REQUEST_TIMEOUT_MS),
    })

    if (!response.ok) {
      throw new Error(`Failed to get user info: ${response.status}`)
    }

    return await response.json()
  }

  async logout(): Promise<void> {
    const authMethod = this.getAuthMethod()
    if (authMethod === 'sso') {
      await this.logoutSSO()
    } else {
      await this.clearTokens()
    }
    if (typeof document !== 'undefined') {
      document.cookie = 'lia_logged_out=1; path=/; max-age=86400; SameSite=None; Secure'
    }
  }
}

export const authService = new AuthService()
export default authService
