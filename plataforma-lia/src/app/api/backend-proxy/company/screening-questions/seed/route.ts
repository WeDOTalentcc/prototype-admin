import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/screening-questions/seed",
  methods: ["POST"],
  auth: true,
})
