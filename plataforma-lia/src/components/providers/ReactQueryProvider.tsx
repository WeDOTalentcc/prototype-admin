"use client"

import { useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

/**
 * ReactQueryProvider — thin client boundary para o QueryClient global.
 *
 * Usado em [locale]/layout.tsx (Server Component raiz) pois QueryClient
 * requer useState (client-side). DashboardLayoutClient e StaffLayoutClient
 * têm instâncias próprias que SOBREPÕEM esta via nested provider —
 * React Query usa o provider mais interno, então não há conflito.
 *
 * Por que aqui: [locale]/page.tsx renderiza DashboardApp fora de (dashboard)/,
 * logo fora do DashboardLayoutClient. Sem este provider, useQuery nessas
 * rotas falha com "No QueryClient set".
 */
export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      }),
  )

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
