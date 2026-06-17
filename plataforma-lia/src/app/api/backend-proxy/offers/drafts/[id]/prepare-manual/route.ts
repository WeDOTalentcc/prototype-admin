import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, POST } = createProxyHandlers({
  backendPath: "/api/v1/offers/drafts/:id/prepare_manual",
  methods: ["POST"],
  backendTarget: "fastapi",
})
