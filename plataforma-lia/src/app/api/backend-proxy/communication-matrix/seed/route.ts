import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/communication-matrix/seed",
  methods: ["POST"],
  auth: true,
})
