import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/notifications/send",
  methods: ["POST"],
  backendTarget: "fastapi",
})
