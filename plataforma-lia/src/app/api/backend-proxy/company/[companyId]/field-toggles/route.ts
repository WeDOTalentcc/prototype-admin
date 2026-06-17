import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/company/:companyId/field-toggles",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})
