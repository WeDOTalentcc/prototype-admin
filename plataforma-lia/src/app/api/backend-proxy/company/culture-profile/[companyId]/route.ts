import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/culture-profile/:companyId",
  methods: ["GET", "PUT", "DELETE"],
  auth: true,
})
