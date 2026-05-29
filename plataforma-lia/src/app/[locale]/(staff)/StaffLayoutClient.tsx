"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DashboardApp } from "@/components/dashboard-app"

/**
 * Client wrapper para route group `(staff)/`.
 *
 * Gate canonical:
 * - `user.role === 'wedotalent_admin'` → renderiza children dentro do
 *   shell DashboardApp (mesma chrome do app, recrutador-style, mas
 *   visualmente diferenciado por banner topo "Área WeDo Admin").
 * - Qualquer outra role → redirect para `/acesso-negado`.
 * - Loading state (isLoading) → fallback simples.
 *
 * Por que reaproveitar DashboardApp:
 * - Sidebar fica oculta no `(staff)/` (Sidebar checa role internamente
 *   na PR seguinte; por enquanto exibimos sem entries para Fairness/
 *   Governanca movidos — ainda nada se moveu nesta PR).
 * - LIA chat continua disponível.
 *
 * Skill aplicada: harness-engineering [guide + sensor]
 *   - Guide: este wrapper documenta a expectativa de role
 *   - Sensor (PR futura): test verifica redirect em recruiter
 */
export default function StaffLayoutClient({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)
  const isLoading = useAuthStore((s) => s.isLoading)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated || !user) {
      router.replace("/login")
      return
    }
    if (!("role" in user) || user.role !== "wedotalent_admin") {
      router.replace("/acesso-negado")
    }
  }, [isLoading, isAuthenticated, user, router, pathname])

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, retry: 2, refetchOnWindowFocus: false } },
      }),
  )

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary">
        <div className="text-lia-text-secondary text-sm">Verificando acesso...</div>
      </div>
    )
  }

  if (!isAuthenticated || !user || !("role" in user) || user.role !== "wedotalent_admin") {
    // Mantém UI mínima enquanto o redirect via useEffect dispara.
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary">
        <div className="text-lia-text-secondary text-sm">Redirecionando...</div>
      </div>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <DashboardApp initialPage="WeDo Admin">{children}</DashboardApp>
    </QueryClientProvider>
  )
}
