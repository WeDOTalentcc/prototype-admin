import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/ai-performance/experiments/:name/promote-winner",
  methods: ["POST"],
})
