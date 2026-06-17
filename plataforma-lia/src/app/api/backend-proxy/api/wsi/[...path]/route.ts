import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

// ---------------------------------------------------------------------------
// Proxy canônico do domínio WSI (triagem) — 2026-06-05
// ---------------------------------------------------------------------------
// Bug corrigido: TODAS as chamadas do front a `/api/backend-proxy/api/wsi/*`
// (modal de triagem: results/candidate, results/{id}/details, ranking,
//  candidate/{id}/ranking, feedback-status, trigger-feedback, generate-questions,
//  analyze-response, calculate-wsi, sessions, candidates/{vac}/scores, etc.)
// retornavam HTTP 404 porque não existia NEM route handler NEM rewrite no
// next.config para esse caminho. Resultado visível: o modal "Triagem WSI" exibia
// "Erro ao carregar dados da triagem." (o front recebia 404 e jogava o erro).
//
// Este catch-all encaminha tudo sob `/api/backend-proxy/api/wsi/*` para o
// FastAPI em `/api/wsi/*` (router prefix `APIRouter(prefix="/api/wsi")`),
// injetando o Bearer via `getAuthHeaders(request)` — mesma auth canônica do
// REST que já funciona (cookie lia_access_token / workos_session / Authorization
// injetado pelo middleware). Padrão espelha o proxy custom de
// `backend-proxy/chat/[session_id]/stream/route.ts`.
// ---------------------------------------------------------------------------

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

async function forward(
  request: NextRequest,
  paramsPromise: Promise<{ path: string[] }>,
  method: string,
): Promise<NextResponse> {
  const { path } = await paramsPromise
  const suffix = (path || []).map(encodeURIComponent).join("/")
  const search = request.nextUrl.search || ""
  const auth = getAuthHeaders(request) as Record<string, string>
  const hasBody = !["GET", "HEAD", "DELETE"].includes(method)
  const body = hasBody ? await request.text() : undefined

  let upstream: Response
  try {
    upstream = await fetch(`${BACKEND_URL}/api/v1/wsi/${suffix}${search}`, {
      method,
      headers: { ...auth, "Content-Type": "application/json" },
      ...(body ? { body } : {}),
    })
  } catch (err) {
    return NextResponse.json(
      { error: "upstream_unreachable", detail: String(err) },
      { status: 502 },
    )
  }

  const text = await upstream.text()
  const ct = upstream.headers.get("content-type") || "application/json"
  // Unwrap do envelope do backend ({ok, data, meta}) — espelha o
  // createProxyHandlers (proxy-handler.ts). O front consome o shape interno.
  if (upstream.ok && ct.includes("application/json")) {
    try {
      const parsed = JSON.parse(text)
      if (parsed && typeof parsed === "object" && "ok" in parsed && "data" in parsed) {
        return NextResponse.json((parsed as Record<string, unknown>).data, {
          status: upstream.status,
        })
      }
    } catch {
      // não-JSON / parse falhou → passthrough abaixo
    }
  }
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": ct },
  })
}

export async function GET(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return forward(request, ctx.params, "GET")
}
export async function POST(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return forward(request, ctx.params, "POST")
}
export async function PUT(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return forward(request, ctx.params, "PUT")
}
export async function PATCH(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return forward(request, ctx.params, "PATCH")
}
export async function DELETE(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return forward(request, ctx.params, "DELETE")
}
