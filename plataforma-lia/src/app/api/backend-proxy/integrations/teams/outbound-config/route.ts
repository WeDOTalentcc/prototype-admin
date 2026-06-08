import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/integrations/teams/outbound-config",
  methods: ["GET", "PUT"],
})
