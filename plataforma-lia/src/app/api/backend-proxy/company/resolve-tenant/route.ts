import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/resolve-tenant",
  methods: ["GET"],
  backendTarget: "fastapi",
})
