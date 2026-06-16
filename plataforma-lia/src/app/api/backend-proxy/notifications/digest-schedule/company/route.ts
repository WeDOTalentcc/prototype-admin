import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/notifications/digest-schedule/company",
  methods: ["GET", "PUT"],
})
