// Onda 1 F7 (2026-05-27) — Studio Control Room proxy.
// Backend canonical: GET /api/v1/agent-monitoring/active-executions
// Suporta query param ?surface=talent_pool|job|pipeline_stage|candidate_list.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/active-executions",
  methods: ["GET"],
  auth: true,
})
