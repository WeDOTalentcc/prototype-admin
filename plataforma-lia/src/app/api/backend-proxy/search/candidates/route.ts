import { createProxyHandlers } from "@/lib/api/proxy-handler"

// POST (hybrid search) pode levar ate 18s (SEARCH_CANDIDATES_DEADLINE_SECONDS no backend).
// Timeout do proxy deve ser maior que o deadline do backend (25s > 18s) para que o backend
// entregue resposta degradada em vez do proxy cortar antes e causar 504 em cascata.
const postHandlers = createProxyHandlers({
  backendPath: "/api/v1/search/candidates",
  methods: ["POST"],
  backendTarget: "fastapi",
  timeoutMs: 25000,
})

const getHandlers = createProxyHandlers({
  backendPath: "/api/v1/search/candidates/local",
  methods: ["GET"],
  backendTarget: "fastapi",
})

export const dynamic = "force-dynamic"
export const POST = postHandlers.POST
export const GET = getHandlers.GET
