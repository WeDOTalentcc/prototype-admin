import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/:companyId/check-completeness",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
