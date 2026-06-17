import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/calibration/feedback",
  methods: ["POST"],
  auth: true,
})
