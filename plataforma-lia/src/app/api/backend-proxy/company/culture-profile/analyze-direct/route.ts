import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/culture-profile/analyze-direct",
  methods: ["POST"],
  auth: true,
})
