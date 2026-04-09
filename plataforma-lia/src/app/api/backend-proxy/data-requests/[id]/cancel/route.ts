import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/data-requests/:id/cancel",
  methods: ["POST"],
  backendTarget: "fastapi",
})
