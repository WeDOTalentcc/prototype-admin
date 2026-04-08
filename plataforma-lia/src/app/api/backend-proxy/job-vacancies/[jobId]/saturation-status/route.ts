import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:jobId/saturation-status",
  methods: ["GET"],
  backendTarget: "rails",
})
