import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/pipeline-templates/:id/archive",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
