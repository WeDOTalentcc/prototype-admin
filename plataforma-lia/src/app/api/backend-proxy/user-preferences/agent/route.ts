import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/user-preferences/agent",
  methods: ["GET", "POST"],
  auth: true,
})
