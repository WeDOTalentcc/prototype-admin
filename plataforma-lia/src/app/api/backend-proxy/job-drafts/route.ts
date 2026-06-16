import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { z } from "zod"

const draftCreateSchema = z.object({
  raw_input: z.string().min(1),
  conversation_id: z.string().optional(),
})

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-drafts",
  methods: ["GET", "POST"],
  bodySchema: draftCreateSchema,
})
