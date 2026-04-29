import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/automation-rules/trigger-types",
  methods: ["GET"],
  auth: true,
})
