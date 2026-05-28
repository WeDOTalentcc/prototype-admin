// Onda 3 F1 (2026-05-28) — proxy canonical para batch read de deployments.
//
// Backend canonical: POST /api/v1/agent-deployments/by-targets
// Body: { target_type, target_ids[] } (max 100 ids)
// Response: { deployments_by_target: { [target_id]: Deployment[] } }
//
// Substitui o N+1 da Onda 2 onde cada item de lista (vaga, stage, pool)
// chamava GET /agent-deployments?target_id=X individualmente. Agora 1
// request batch agrega tudo.
//
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/agent-deployments/by-targets",
  methods: ["POST"],
  auth: true,
})
