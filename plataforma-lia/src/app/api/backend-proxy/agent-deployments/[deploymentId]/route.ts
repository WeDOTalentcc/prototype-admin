// Onda 3 F4 (2026-05-28) — proxy canonical para PATCH/DELETE em deployment by id.
// Backend canonical: agent_deployments.py target_router
//   PATCH  /agent-deployments/{deployment_id}  → update (is_active, schedule_cron, etc.)
//   DELETE /agent-deployments/{deployment_id}  → remove
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/agent-deployments/:deploymentId",
  methods: ["PATCH", "DELETE"],
  auth: true,
})
