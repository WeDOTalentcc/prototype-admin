import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/integrations/linkedin/status",
  methods: ["GET"],
})
