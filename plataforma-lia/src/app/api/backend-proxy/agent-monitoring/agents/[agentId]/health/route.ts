import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/agents/:agentId/health",
  methods: ["GET"],
  auth: true,
})
