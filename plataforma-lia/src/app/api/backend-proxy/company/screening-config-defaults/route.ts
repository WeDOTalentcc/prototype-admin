import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/company-hiring-policy/:companyId/screening-config-defaults",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})
