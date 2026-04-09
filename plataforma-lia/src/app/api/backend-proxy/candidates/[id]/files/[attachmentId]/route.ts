import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/candidates/:id/files/:attachmentId",
  methods: ["GET", "DELETE"],
  backendTarget: "fastapi",
})
