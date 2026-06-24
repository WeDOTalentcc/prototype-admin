import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/integrations/linkedin/publish/:jobId",
  methods: ["POST"],
})
