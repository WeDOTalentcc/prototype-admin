import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/persist-revealed",
  methods: ["POST"],
  auth: true,
})
