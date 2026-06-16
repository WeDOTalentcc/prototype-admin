export const dynamic = "force-dynamic"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { GET } = createProxyHandlers({
  backendPath: "/api/v1/offers/drafts/:id/status",
  methods: ["GET"],
  backendTarget: "fastapi",
})
