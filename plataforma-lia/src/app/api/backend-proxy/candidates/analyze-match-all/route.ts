import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/candidates/analyze-match-all",
  methods: ["POST"],
  auth: true,
})
