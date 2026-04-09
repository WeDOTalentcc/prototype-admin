import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/notifications/:id/read",
  methods: ["POST"],
  backendTarget: "fastapi",
})
