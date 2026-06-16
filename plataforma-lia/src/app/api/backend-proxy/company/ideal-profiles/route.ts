import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/ideal-profiles",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
