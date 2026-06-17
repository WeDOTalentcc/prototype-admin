import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST, PUT } = createProxyHandlers({
  backendPath: "/api/v1/alerts/preferences",
  methods: ["GET", "POST", "PUT"],
  auth: true,
})
