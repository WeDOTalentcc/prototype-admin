import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/policy-engine/rate-limit-rules",
  methods: ["POST"],
  auth: true,
})
