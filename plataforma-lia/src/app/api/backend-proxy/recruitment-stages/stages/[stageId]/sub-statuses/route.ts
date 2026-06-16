import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/stages/:stageId/sub-statuses",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
