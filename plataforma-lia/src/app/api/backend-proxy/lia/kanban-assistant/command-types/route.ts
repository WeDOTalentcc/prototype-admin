import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/lia/kanban-assistant/command-types",
  methods: ["GET"],
})
