import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/culture-profile/analyze",
  methods: ["POST"],
  auth: true,
})
