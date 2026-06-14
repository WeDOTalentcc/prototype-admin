import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { z } from "zod"

const draftUpdateSchema = z.record(z.string(), z.unknown())

export const { dynamic, GET, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/job-drafts/:id",
  methods: ["GET", "PATCH", "DELETE"],
  bodySchema: draftUpdateSchema,
})
