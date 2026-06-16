import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/shared-searches/:id/resend",
  methods: ["POST"],
  backendTarget: "fastapi",
})
