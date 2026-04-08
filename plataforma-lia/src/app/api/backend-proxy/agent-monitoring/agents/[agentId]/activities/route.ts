import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/agents/:agentId/activities",
  methods: ["GET"],
  auth: true,
})
