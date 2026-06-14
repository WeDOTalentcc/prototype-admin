import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-readiness/job/:jobId/reactivate",
  methods: ["POST"],
  backendTarget: "fastapi",
})
