import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/admin/llm-config/providers",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
