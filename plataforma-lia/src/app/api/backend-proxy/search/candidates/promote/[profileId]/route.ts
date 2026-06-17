import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/promote/:profileId",
  methods: ["POST"],
  auth: true,
})
