// Onda 2 F9 (2026-05-27) — proxy canonical para AgentsCard no Decidir + indicador global.
// Backend canonical: GET /api/v1/agent-monitoring/active-summary
// Suporta query params:
//   - surface: 'decidir' | 'pool' | 'job' | 'funil' | 'all' (default 'decidir')
//   - limit: 1..20 (default 5)
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/active-summary",
  methods: ["GET"],
  auth: true,
})
