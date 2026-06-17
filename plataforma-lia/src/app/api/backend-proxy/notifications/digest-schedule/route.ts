import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/notifications/digest-schedule",
  methods: ["GET", "PUT", "DELETE"],
})
