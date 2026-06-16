import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/wsi/async/:token/answer",
  methods: ["POST"],
  auth: true,
})
