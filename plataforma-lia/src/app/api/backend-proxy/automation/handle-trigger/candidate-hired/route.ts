import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/automation/handle-trigger/candidate-hired",
  methods: ["POST"],
  auth: true,
})
