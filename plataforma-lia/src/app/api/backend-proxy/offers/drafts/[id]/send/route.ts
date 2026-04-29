import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/offers/drafts/:id/send_auto",
  methods: ["POST"],
  backendTarget: "fastapi",
})
