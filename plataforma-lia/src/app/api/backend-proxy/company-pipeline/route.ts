import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/company-pipeline",
  methods: ["GET", "PUT"],
})
