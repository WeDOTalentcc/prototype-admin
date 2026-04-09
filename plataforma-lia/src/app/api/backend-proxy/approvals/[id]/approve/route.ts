import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PUT } = createProxyHandlers({
  backendPath: "/api/v1/approvals/:id/approve",
  methods: ["PUT"],
  auth: true,
  backendTarget: "fastapi",
})
