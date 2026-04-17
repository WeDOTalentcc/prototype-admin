import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/search/:searchId/discarded",
  methods: ["GET"],
  auth: true,
})
