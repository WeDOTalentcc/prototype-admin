import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/custom-agents/studio/compliance-summary",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
