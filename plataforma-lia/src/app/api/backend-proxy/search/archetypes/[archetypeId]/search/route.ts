import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/archetypes/:archetypeId/search",
  methods: ["POST"],
  auth: true,
})
