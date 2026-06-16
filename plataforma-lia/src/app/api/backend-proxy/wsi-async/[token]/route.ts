import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/wsi/async/:token",
  methods: ["GET", "POST"],
  auth: true,
})
