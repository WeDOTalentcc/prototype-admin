// Onda 3 F3/F4 (2026-05-28) — proxy canonical para /api/v1/jobs/{job_id}/agents.
// Backend canonical: app/api/v1/jobs_agents.py
//   GET    → lista deployments + joined agent metadata
//   POST   → acopla um agente existente à vaga
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/jobs/:id/agents",
  methods: ["GET", "POST"],
  auth: true,
})
