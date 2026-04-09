import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, DELETE, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/candidate-lists/:listId",
  methods: ["GET", "DELETE", "PATCH"],
  backendTarget: "fastapi",
})
