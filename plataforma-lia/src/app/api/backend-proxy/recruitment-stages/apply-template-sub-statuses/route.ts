import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/apply-template-sub-statuses",
  methods: ["POST"],
  backendTarget: "fastapi",
})
