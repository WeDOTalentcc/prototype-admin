import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/users/:userId/resend-invitation",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
