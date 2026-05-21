import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/ai-transparency/human-oversight/:decisionId/override",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
