import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/agent-marketplace",
  methods: ["GET", "POST", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
