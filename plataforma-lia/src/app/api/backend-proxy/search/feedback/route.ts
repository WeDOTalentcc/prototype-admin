import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/feedback",
  methods: ["GET", "POST"],
  auth: true,
})
