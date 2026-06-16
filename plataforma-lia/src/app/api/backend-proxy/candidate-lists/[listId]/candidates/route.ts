import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/candidate-lists/:listId/candidates",
  methods: ["POST", "DELETE"],
  backendTarget: "fastapi",
})
