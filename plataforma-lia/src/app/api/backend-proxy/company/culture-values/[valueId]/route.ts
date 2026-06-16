import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/company/culture-values/:valueId",
  methods: ["PUT", "DELETE"],
  auth: true,
  backendTarget: "fastapi",
})
