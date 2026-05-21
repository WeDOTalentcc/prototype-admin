import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/bias-audit/annual/:reportId/publish",
  methods: ["PATCH"],
  auth: true,
  backendTarget: "fastapi",
})
