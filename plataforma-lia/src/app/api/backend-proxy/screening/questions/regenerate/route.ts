import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/screening/questions/regenerate",
  methods: ["POST"],
  auth: true,
})
