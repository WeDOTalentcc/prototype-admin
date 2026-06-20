import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/search/calibration/feedback",
  methods: ["POST"],
  auth: true,
})
