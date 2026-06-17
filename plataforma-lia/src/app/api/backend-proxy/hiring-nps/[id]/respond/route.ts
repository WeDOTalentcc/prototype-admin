import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/hiring-nps/:id/respond",
  methods: ["PATCH"],
  auth: false,
  backendTarget: "fastapi",
})
