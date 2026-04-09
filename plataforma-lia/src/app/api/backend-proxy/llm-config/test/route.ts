import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/admin/llm-config/test",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
