import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/search/archetypes/:archetypeId",
  methods: ["GET", "PUT", "DELETE"],
  auth: true,
})
