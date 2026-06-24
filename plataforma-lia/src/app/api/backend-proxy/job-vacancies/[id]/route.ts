import { z } from "zod"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

const jobUpdateBodySchema = z.record(z.string(), z.unknown())

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:id",
  methods: ["GET", "PUT", "DELETE"],
  bodySchema: jobUpdateBodySchema,
  timeoutMs: 15000,
})
