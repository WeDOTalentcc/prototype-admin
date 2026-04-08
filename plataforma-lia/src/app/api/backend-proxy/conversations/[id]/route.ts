import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/conversations/:id",
  methods: ["GET", "DELETE"],
})
