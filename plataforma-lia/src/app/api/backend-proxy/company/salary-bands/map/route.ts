import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/salary-bands/map",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
