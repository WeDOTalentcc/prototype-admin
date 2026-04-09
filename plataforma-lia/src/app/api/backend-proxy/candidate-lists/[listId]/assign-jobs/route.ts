import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/candidate-lists/:listId/assign-jobs",
  methods: ["POST"],
  backendTarget: "fastapi",
})
