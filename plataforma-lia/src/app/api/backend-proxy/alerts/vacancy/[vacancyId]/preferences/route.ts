import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/alerts/vacancy/:vacancyId/preferences",
  methods: ["GET", "PUT"],
  auth: true,
})
