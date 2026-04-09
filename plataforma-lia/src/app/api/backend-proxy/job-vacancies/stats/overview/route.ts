import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/stats/overview",
  methods: ["GET"],
  backendTarget: "fastapi",
})
