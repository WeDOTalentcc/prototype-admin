"use client"

import { createContext, useContext, useEffect, ReactNode } from "react"
import { useAuthStore } from "@/stores/auth-store"
import type { AuthenticatedUser, AuthMethod } from "@/services/auth-service"

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
  const user = useAuthStore((s) => s.user)
  const authMethod = useAuthStore((s) => s.authMethod)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLoading = useAuthStore((s) => s.isLoading)
  const isSSO = useAuthStore((s) => s.isSSO)
  const login = useAuthStore((s) => s.login)
  const loginWithSSO = useAuthStore((s) => s.loginWithSSO)
  const register = useAuthStore((s) => s.register)
  const logout = useAuthStore((s) => s.logout)
  const refreshUser = useAuthStore((s) => s.refreshUser)
  const initAuth = useAuthStore((s) => s.initAuth)

  useEffect(() => {
    initAuth()
  }, [initAuth])

  const value: AuthContextType = {
    user,
    authMethod,
    isAuthenticated,
    isLoading,
    login,
    loginWithSSO,
    register,
    logout,
    refreshUser,
    isSSO,
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


export function useAuth() {
  const ctx = useJWTAuth()
  return {
    user: ctx.user ? {
      name: ctx.user.name || ctx.user.email,
      email: ctx.user.email,
      role: ("role" in ctx.user ? ctx.user.role : null) ?? null,
      company: ("company" in ctx.user ? ctx.user.company : null) ?? null,
      avatar_url: ("avatar_url" in ctx.user ? ctx.user.avatar_url : null) ?? null,
      sso_provider: ("sso_provider" in ctx.user ? ctx.user.sso_provider : null) ?? null,
    } : null,
    login: ctx.login,
    logout: ctx.logout,
    refreshUser: ctx.refreshUser,
    isAuthenticated: ctx.isAuthenticated,
    isLoading: ctx.isLoading,
  }
}

export { AuthContext }
