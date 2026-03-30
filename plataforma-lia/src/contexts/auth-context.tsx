"use client"

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"
import authService, { User, SSOUser, AuthenticatedUser, AuthMethod } from "@/services/auth-service"
import { clearSessionStorage } from "@/lib/session-cleanup"

interface AuthContextType {
  user: AuthenticatedUser | null
  authMethod: AuthMethod | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithSSO: (options: { organization?: string; connection?: string; email?: string }) => void
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  isSSO: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function JWTAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [authMethod, setAuthMethod] = useState<AuthMethod | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const currentAuthMethod = authService.getAuthMethod()

    if (currentAuthMethod === 'sso') {
      try {
        const ssoSession = await authService.checkSSOSession()
        if (ssoSession.authenticated && ssoSession.user) {
          setUser(ssoSession.user)
          setAuthMethod('sso')
        } else {
          setUser(null)
          setAuthMethod(null)
        }
      } catch {
        setUser(null)
        setAuthMethod(null)
      }
    } else if (currentAuthMethod === 'jwt' || authService.isJWTAuthenticated()) {
      try {
        const userData = await authService.getMe()
        setUser(userData)
        setAuthMethod('jwt')
      } catch {
        setUser(null)
        setAuthMethod(null)
        authService.clearTokens()
      }
    } else {
      setUser(null)
      setAuthMethod(null)
    }
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      const currentAuthMethod = authService.getAuthMethod()

      if (currentAuthMethod === 'sso') {
        try {
          const ssoSession = await authService.checkSSOSession()
          if (ssoSession.authenticated && ssoSession.user) {
            setUser(ssoSession.user)
            setAuthMethod('sso')
          } else {
            authService.clearTokens()
          }
        } catch {
          authService.clearTokens()
        }
      } else if (authService.isJWTAuthenticated()) {
        try {
          await authService.refreshToken()
          const userData = await authService.getMe()
          setUser(userData)
          setAuthMethod('jwt')
        } catch {
          authService.clearTokens()
          setUser(null)
          setAuthMethod(null)
        }
      }

      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    await authService.login(email, password)
    const userData = await authService.getMe()
    setUser(userData)
    setAuthMethod('jwt')
  }

  const loginWithSSO = (options: { organization?: string; connection?: string; email?: string }) => {
    authService.initiateSSO(options)
  }

  const register = async (email: string, password: string, name: string) => {
    await authService.register(email, password, name)
    await login(email, password)
  }

  const logout = async () => {
    clearSessionStorage()  // limpa dados de sessão do localStorage
    await authService.logout()
    setUser(null)
    setAuthMethod(null)
  }

  const value: AuthContextType = {
    user,
    authMethod,
    isAuthenticated: !!user,
    isLoading,
    login,
    loginWithSSO,
    register,
    logout,
    refreshUser,
    isSSO: authMethod === 'sso',
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useJWTAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useJWTAuth must be used within a JWTAuthProvider")
  }
  return context
}

export { AuthContext }
