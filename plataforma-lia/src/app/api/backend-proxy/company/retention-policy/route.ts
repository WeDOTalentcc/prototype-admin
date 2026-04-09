import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/company/retention-policy",
  methods: ["GET", "PATCH"],
  auth: true,
  backendTarget: "fastapi",
})
