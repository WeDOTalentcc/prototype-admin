// P1-W3-14: migrated from hardcoded 127.0.0.1:8001 to canonical createProxyHandlers
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/webhooks/events",
  methods: ["GET"],
})
