import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/jobs/qualification/classify",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
