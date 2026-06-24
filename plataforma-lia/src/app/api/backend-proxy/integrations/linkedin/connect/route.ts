import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PUT } = createProxyHandlers({
  backendPath: "/api/v1/integrations/linkedin/connect",
  methods: ["PUT"],
})
