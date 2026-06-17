import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, POST } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/ats-mappings",
  methods: ["GET", "POST"],
  auth: true,
  backendTarget: "fastapi",
})
