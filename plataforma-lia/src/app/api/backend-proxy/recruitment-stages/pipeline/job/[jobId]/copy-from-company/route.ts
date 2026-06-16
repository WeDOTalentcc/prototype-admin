import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/pipeline/job/:jobId/copy-from-company",
  methods: ["POST"],
  backendTarget: "fastapi",
})
