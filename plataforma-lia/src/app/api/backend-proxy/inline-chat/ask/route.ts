import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/inline-chat/ask",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
  timeoutMs: 20000,
})
