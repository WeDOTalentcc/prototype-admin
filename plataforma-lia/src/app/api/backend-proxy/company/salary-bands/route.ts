import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/salary-bands/",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
