import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { z } from "zod"

const publishSchema = z.object({
  status: z.string().optional(),
  priority: z.string().optional(),
})

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-drafts/:id/publish",
  methods: ["POST"],
  bodySchema: publishSchema,
  timeoutMs: 20000,
})
