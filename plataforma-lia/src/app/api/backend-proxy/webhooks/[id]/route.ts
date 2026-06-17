import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/webhooks/:id",
  methods: ["PATCH", "DELETE"],
})
