// Onda 1 F7 (2026-05-27) — Studio Control Room proxy.
// Backend canonical: GET /api/v1/agent-monitoring/recent-executions
// Suporta query params: limit, agent_id, surface, status.
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/recent-executions",
  methods: ["GET"],
  auth: true,
})
