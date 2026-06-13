export const dynamic = "force-dynamic"
import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { GET } = createProxyHandlers({
  backendPath: "/api/v1/offers/by-candidate/:candidateId",
  methods: ["GET"],
  backendTarget: "fastapi",
})
