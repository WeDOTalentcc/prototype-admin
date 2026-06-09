import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/custom-agents",
  methods: ["GET", "POST", "PATCH", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
