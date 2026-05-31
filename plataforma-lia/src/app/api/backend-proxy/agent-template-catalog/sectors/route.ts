import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/agent-template-catalog/sectors",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
