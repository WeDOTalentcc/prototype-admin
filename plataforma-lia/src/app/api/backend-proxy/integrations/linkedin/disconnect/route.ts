import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/integrations/linkedin/disconnect",
  methods: ["DELETE"],
})
