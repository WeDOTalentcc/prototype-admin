import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/enhance-prompt",
  methods: ["POST"],
  auth: true,
})
