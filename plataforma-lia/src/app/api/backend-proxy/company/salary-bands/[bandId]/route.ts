import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/salary-bands/:bandId",
  methods: ["GET", "PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
