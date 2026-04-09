import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/stages/reorder",
  methods: ["POST"],
  backendTarget: "fastapi",
})
