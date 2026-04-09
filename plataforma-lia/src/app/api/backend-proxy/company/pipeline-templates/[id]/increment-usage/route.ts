import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/pipeline-templates/:id/increment-usage",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
