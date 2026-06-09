import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/custom-agents",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
