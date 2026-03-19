const AUTH_API_URL = '/api/backend-proxy/auth'
const WORKOS_SSO_URL = '/api/auth/workos/sso'
const WORKOS_SESSION_URL = '/api/auth/workos/session'

const TOKEN_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  AUTH_METHOD: 'auth_method',
}

export type AuthMethod = 'jwt' | 'sso'

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'recruiter' | 'viewer'
  is_active: boolean
  created_at: string
  updated_at: string
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
  details?: Record<string, any>
}

export interface SSOSessionResponse {
  authenticated: boolean
  user?: SSOUser
  reason?: string
}

class AuthService {
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
  }

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
  }

  getAuthMethod(): AuthMethod | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEYS.AUTH_METHOD) as AuthMethod | null
  }

  setAuthMethod(method: AuthMethod): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEYS.AUTH_METHOD, method)
  }

  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
    localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    this.setAuthMethod('jwt')
  }

  clearTokens(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(TOKEN_KEYS.AUTH_METHOD)
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
        this.setAuthMethod('sso')
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
    } catch (error) {
      console.error('SSO logout error:', error)
    }
    this.clearTokens()
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
    this.setTokens(data.access_token, data.refresh_token)
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

  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = this.getRefreshToken()
    
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await fetch(`${AUTH_API_URL}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      this.clearTokens()
      const error: AuthError = await response.json().catch(() => ({ 
        error: 'Token refresh failed' 
      }))
      throw new Error(error.error || 'Failed to refresh token')
    }

    const data: TokenResponse = await response.json()
    this.setTokens(data.access_token, data.refresh_token)
    return data
  }

  async getMe(): Promise<User> {
    const accessToken = this.getAccessToken()
    
    if (!accessToken) {
      throw new Error('No access token available')
    }

    const response = await fetch(`${AUTH_API_URL}/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      if (response.status === 401) {
        try {
          await this.refreshToken()
          return this.getMe()
        } catch {
          this.clearTokens()
          throw new Error('Session expired')
        }
      }
      const error: AuthError = await response.json().catch(() => ({ 
        error: 'Failed to get user info' 
      }))
      throw new Error(error.error || 'Failed to get user info')
    }

    return response.json()
  }

  async logout(): Promise<void> {
    const authMethod = this.getAuthMethod()
    if (authMethod === 'sso') {
      await this.logoutSSO()
    } else {
      this.clearTokens()
    }
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken() || this.getAuthMethod() === 'sso'
  }

  isJWTAuthenticated(): boolean {
    return !!this.getAccessToken()
  }
}

export const authService = new AuthService()
export default authService
