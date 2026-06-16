// Onda 3 F4 (2026-05-28) — proxy canonical para DELETE /jobs/{job_id}/agents/{deployment_id}.
// Backend canonical: app/api/v1/jobs_agents.py:detach_agent_from_job.
// Multi-tenancy fail-closed: header X-Company-ID via getAuthHeaders/JWT.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/jobs/:id/agents/:deploymentId",
  methods: ["DELETE"],
  auth: true,
})
