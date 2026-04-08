import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:jobId/unlock-pipeline",
  methods: ["POST"],
  backendTarget: "rails",
})
