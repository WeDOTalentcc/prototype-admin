import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/bias-audit/job/:jobId",
  methods: ["GET"],
  auth: true,
})
