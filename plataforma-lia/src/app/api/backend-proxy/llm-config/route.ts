import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/admin/llm-config",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})
