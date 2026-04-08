import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/wsi/async/invite",
  methods: ["POST"],
  auth: false,
})
