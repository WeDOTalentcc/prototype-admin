import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/manager-alignments/:id/respond",
  methods: ["PATCH"],
  auth: false,
  backendTarget: "fastapi",
})
