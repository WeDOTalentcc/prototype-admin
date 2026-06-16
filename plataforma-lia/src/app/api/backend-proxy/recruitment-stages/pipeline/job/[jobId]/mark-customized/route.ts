import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/pipeline/job/:jobId/mark-customized",
  methods: ["POST"],
  backendTarget: "fastapi",
})
