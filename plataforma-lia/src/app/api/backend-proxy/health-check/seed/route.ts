import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/health-check/seed",
  methods: ["POST"],
  auth: false,
})
