import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/pipeline-templates/:id",
  methods: ["GET", "PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
