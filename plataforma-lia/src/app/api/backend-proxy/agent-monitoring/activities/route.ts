import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/agent-monitoring/activities",
  methods: ["POST"],
  auth: true,
})
