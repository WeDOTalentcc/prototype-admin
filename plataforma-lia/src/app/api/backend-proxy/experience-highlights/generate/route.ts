import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/experience-highlights/generate",
  methods: ["POST"],
  auth: true,
})
