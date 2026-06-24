import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/users/search",
  methods: ["GET"],
  backendTarget: "fastapi",
})
