import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/:id/generate-public-link",
  methods: ["POST"],
  backendTarget: "fastapi",
})
