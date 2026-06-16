import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/ai-performance/experiments/:name/history",
  methods: ["GET"],
})
