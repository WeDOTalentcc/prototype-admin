import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/candidates/:id/quick-ask",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
