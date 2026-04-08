import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/workforce/entries",
  methods: ["GET", "PUT"],
  auth: true,
})
