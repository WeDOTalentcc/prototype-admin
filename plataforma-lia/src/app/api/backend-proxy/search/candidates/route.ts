import { createProxyHandlers } from "@/lib/api/proxy-handler"

const postHandlers = createProxyHandlers({
  backendPath: "/api/v1/search/candidates",
  methods: ["POST"],
  backendTarget: "fastapi",
})

const getHandlers = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/local",
  methods: ["GET"],
  backendTarget: "fastapi",
})

export const dynamic = "force-dynamic"
export const POST = postHandlers.POST
export const GET = getHandlers.GET
