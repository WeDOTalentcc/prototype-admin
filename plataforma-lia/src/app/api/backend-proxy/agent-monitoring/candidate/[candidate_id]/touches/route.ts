// Onda 2 F9 (2026-05-27) — proxy canonical para "candidato tocado por agente".
// Backend canonical: GET /api/v1/agent-monitoring/candidate/{candidate_id}/touches
// Query param: since_hours (1..168, default 24).
// Multi-tenancy fail-closed: header X-Company-ID + 404 cross-tenant.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/candidate/:candidate_id/touches",
  methods: ["GET"],
  auth: true,
})
