// Onda C4.2 (2026-05-29) — proxy canonical para Daily Digest / Morning Brief.
// Backend canonical: GET /api/v1/agent-monitoring/daily-digest
// Suporta query params:
//   - since_hours: 1..168 (default 24)
//   - limit: 1..20 (default 8)
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/daily-digest",
  methods: ["GET"],
  auth: true,
})
