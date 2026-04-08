import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/archetypes/from-search",
  methods: ["POST"],
  auth: true,
})
