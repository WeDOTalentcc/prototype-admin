import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/screening-questions",
  methods: ["GET", "POST", "PUT", "DELETE"],
  auth: true,
})
