import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/estimate",
  methods: ["POST"],
  auth: true,
})
