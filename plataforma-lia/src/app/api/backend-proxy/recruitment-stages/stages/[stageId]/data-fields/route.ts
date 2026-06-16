import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/stages/:stageId/data-fields",
  methods: ["PATCH"],
  auth: true,
  backendTarget: "fastapi",
})
