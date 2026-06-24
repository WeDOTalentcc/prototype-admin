import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { jobCreateSchema } from "@/lib/schemas"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies",
  methods: ["GET", "POST"],
  bodySchema: jobCreateSchema,
  timeoutMs: 30000,
})
