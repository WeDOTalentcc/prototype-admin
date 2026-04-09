import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/goals/by-user/:userId",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
