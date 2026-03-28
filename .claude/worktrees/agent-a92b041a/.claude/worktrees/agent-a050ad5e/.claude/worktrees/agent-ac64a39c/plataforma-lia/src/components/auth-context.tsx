/**
 * @deprecated Este módulo redireciona para o contexto JWT real.
 * Use `useJWTAuth` de `@/contexts/auth-context` para novos componentes.
 * Mantido para compatibilidade com componentes legados que importam `useAuth` daqui.
 */
"use client"

import { useJWTAuth, JWTAuthProvider } from "@/contexts/auth-context"

export const AuthProvider = JWTAuthProvider

export function useAuth() {
  const ctx = useJWTAuth()
  return {
    user: ctx.user ? { name: ctx.user.name || ctx.user.email, email: ctx.user.email, role: "admin", company: "WeDo" } : null,
    login: () => {},
    logout: ctx.logout,
    isAuthenticated: ctx.isAuthenticated,
    isLoading: ctx.isLoading,
  }
}
