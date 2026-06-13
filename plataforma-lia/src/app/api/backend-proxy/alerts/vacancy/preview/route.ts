import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/alerts/vacancy/preview",
  methods: ["GET"],
  auth: true,
})
