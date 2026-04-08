import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/lia/learning/skills-deduplicated",
  methods: ["POST"],
  auth: true,
})
