import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search-assistant/analyze",
  methods: ["POST"],
  auth: true,
})
