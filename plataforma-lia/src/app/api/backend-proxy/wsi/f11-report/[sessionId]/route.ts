import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/wsi/f11-report/:sessionId",
  methods: ["GET"],
  auth: true,
})
