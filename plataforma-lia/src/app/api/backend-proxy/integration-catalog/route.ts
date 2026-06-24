import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/integration-catalog",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
