import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/stages/:stageId/remove",
  methods: ["DELETE"],
  backendTarget: "fastapi",
})
