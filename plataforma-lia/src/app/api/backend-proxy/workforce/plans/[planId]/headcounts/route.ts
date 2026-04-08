import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/workforce/plans/:planId/headcounts",
  methods: ["GET", "POST"],
  auth: true,
})
