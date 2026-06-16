import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/custom-agents/studio/quota",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
