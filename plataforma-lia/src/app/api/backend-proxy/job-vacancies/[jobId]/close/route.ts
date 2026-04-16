import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { jobStatusSchema } from "@/lib/schemas"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:jobId/close",
  methods: ["POST"],
  bodySchema: jobStatusSchema,
})
