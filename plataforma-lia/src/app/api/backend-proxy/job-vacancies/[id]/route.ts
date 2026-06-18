import { z } from "zod"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

const jobUpdateBodySchema = z.record(z.string(), z.unknown())

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:id",
  methods: ["GET", "PUT"],
  bodySchema: jobUpdateBodySchema,
  timeoutMs: 15000,
})
