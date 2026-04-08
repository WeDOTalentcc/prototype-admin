import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/semantic-search/:domain",
  methods: ["POST"],
  auth: true,
})
