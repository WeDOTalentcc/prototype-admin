import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/talent-funnel/wrf-config",
  methods: ["GET", "POST"],
  auth: true,
})
