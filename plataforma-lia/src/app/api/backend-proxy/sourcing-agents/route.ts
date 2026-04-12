import { createProxyHandlers } from "@/lib/api/proxy-handler"

const handlers = createProxyHandlers({
  backendPath: "/api/v1/sourcing-agents",
  methods: ["GET", "POST"],
})

export const dynamic = "force-dynamic"
export const GET = handlers.GET
export const POST = handlers.POST
