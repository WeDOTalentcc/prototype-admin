import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/email-templates/:id/send",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
