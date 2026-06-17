import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/departments/:departmentId",
  methods: ["PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
