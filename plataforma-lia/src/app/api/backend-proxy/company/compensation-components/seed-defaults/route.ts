import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/company/compensation-components/seed-defaults",
  methods: ["POST"],
  auth: true,
  backendTarget: "fastapi",
})
