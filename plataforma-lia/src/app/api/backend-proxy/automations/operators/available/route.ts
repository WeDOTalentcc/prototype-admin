import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/automations/operators/available",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
