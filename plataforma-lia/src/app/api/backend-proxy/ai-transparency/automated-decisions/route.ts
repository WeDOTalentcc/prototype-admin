import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/ai-transparency/automated-decisions",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
