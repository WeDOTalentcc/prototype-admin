import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/profile/:profileId/generate-evp",
  methods: ["POST"],
  auth: true,
})
