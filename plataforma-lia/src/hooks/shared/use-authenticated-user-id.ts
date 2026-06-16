"use client"

/**
 * useAuthenticatedUserId — Hook central para obter o user_id autenticado com
 * flag `isReady` para que componentes possam *gatear* (gate) fetches até o
 * auth ter hidratado.
 *
 * Motivação (BUG-08 do QA 2026-04-15):
 *   Vários pontos do código usavam fallback `|| 'default_user'` em requests
 *   (briefing, notifications, sidebar). Antes do auth resolver, o frontend
 *   disparava requests com `user_id=default_user`; depois, com o email real.
 *   Resultado: dobra de requests + contadores contaminados + logs sujos.
 *
 * Uso preferido:
 *
 *   const { userId, isReady } = useAuthenticatedUserId()
 *   useEffect(() => {
 *     if (!isReady) return
 *     fetch(`/api/.../?user_id=${userId}`)
 *   }, [isReady, userId])
 *
 * Onde backward-compat é necessária (componentes legados que recebem userId
 * como prop), use o helper `resolveUserId` para evitar "default_user":
 *
 *   const userId = resolveUserId(authUser)  // string | null (null enquanto carrega)
 */

import { useAuth } from "@/contexts/auth-context"
import type { AuthenticatedUser } from "@/services/auth-service"

export interface UseAuthenticatedUserIdReturn {
  /** ID estável do usuário (id UUID preferido, fallback email). `null` enquanto auth não hidratou. */
  userId: string | null
  /** true quando auth terminou de carregar E há usuário autenticado. */
  isReady: boolean
}

export function useAuthenticatedUserId(): UseAuthenticatedUserIdReturn {
  const { user, isLoading, isAuthenticated } = useAuth()
  return {
    userId: resolveUserId(user as AuthenticatedUser | null | undefined),
    isReady: !isLoading && isAuthenticated && user != null,
  }
}

/**
 * Versão sem hook para usar em callbacks/stores onde não há contexto React.
 * Retorna `null` para forçar o caller a tratar o estado pré-auth explicitamente,
 * em vez de silenciosamente virar "default_user".
 */
export function resolveUserId(user: AuthenticatedUser | null | undefined): string | null {
  if (!user) return null
  const u = user as { id?: string; email?: string }
  return u.id || u.email || null
}
