import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/hiring-nps/respond",
  methods: ["GET"],
  auth: false,
  backendTarget: "fastapi",
})
