// Onda 2 F9 (2026-05-27) — proxy canonical para listar deployments por target.
// Backend canonical: GET /api/v1/agent-deployments
// Query params:
//   - target_type: 'talent_pool' | 'job' | 'pipeline_stage' | 'candidate_list'
//   - target_id: UUID/string do alvo
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-deployments",
  methods: ["GET"],
  auth: true,
})
