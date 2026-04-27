import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/offers/drafts/:id",
  methods: ["GET", "PATCH", "DELETE"],
  backendTarget: "fastapi",
})
