import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/data-requests/config/collection-settings",
  methods: ["GET", "POST"],
  auth: true,
})
