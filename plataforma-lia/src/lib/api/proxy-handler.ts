import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

type BackendTarget = "fastapi" | "rails"

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH"

type HandlerFn = (
  request: NextRequest,
  context?: { params: Promise<Record<string, string>> }
) => Promise<NextResponse>

type ProxyResult<M extends HttpMethod> = {
  dynamic: "force-dynamic"
} & { [K in M]: HandlerFn }

interface ProxyConfig<M extends HttpMethod> {
  /** Backend API path, e.g. "/api/v1/activities" or "/api/v1/candidates/:id/viewed" */
  backendPath: string
  /** HTTP methods to expose. Defaults to ["GET"] */
  methods?: M[]
  /** Whether to forward auth headers via getAuthHeaders. Defaults to true */
  auth?: boolean
  /** Backend target for future Rails migration. Defaults to "fastapi" */
  backendTarget?: BackendTarget
  /** Default query params appended to every request */
  defaultParams?: Record<string, string>
  /** Transform the response data before returning to the client */
  onResponse?: (data: unknown) => unknown
}

function resolvePath(
  template: string,
  params: Record<string, string>
): string {
  let resolved = template
  for (const [key, value] of Object.entries(params)) {
    resolved = resolved.replace(":" + key, encodeURIComponent(value))
  }
  return resolved
}

/**
 * Creates a set of Next.js App Router handlers (GET, POST, PUT, DELETE, PATCH)
 * that proxy requests to the backend API.
 *
 * Usage (no dynamic params):
 *   export const { dynamic, GET, POST } = createProxyHandlers({
 *     backendPath: "/api/v1/activities",
 *     methods: ["GET", "POST"],
 *   })
 *
 * Usage (with dynamic params):
 *   export const { dynamic, POST, DELETE } = createProxyHandlers({
 *     backendPath: "/api/v1/candidates/:id/viewed",
 *     methods: ["POST", "DELETE"],
 *   })
 *
 * Usage (with default params):
 *   export const { dynamic, GET } = createProxyHandlers({
 *     backendPath: "/api/v1/items",
 *     defaultParams: { status: "active", limit: "50" },
 *   })
 *
 * Usage (with response transform):
 *   export const { dynamic, GET } = createProxyHandlers({
 *     backendPath: "/api/v1/items",
 *     onResponse: (data) => (data as any).items ?? [],
 *   })
 */
export function createProxyHandlers<M extends HttpMethod = "GET">(
  config: ProxyConfig<M>
): ProxyResult<M> {
  const {
    backendPath,
    methods = ["GET"] as unknown as M[],
    auth = true,
    backendTarget: _backendTarget = "fastapi",
    defaultParams,
    onResponse,
  } = config

  const hasParams = backendPath.includes(":")

  function makeHandler(method: string): HandlerFn {
    return async (
      request: NextRequest,
      context?: { params: Promise<Record<string, string>> }
    ) => {
      try {
        const resolvedParams = hasParams && context?.params
          ? await context.params
          : {}
        const resolvedPath = hasParams
          ? resolvePath(backendPath, resolvedParams)
          : backendPath

        const { searchParams } = new URL(request.url)

        // Merge default params (request params take precedence)
        if (defaultParams) {
          for (const [key, value] of Object.entries(defaultParams)) {
            if (!searchParams.has(key)) {
              searchParams.set(key, value)
            }
          }
        }

        const queryString = searchParams.toString()
        const url = BACKEND_URL + resolvedPath + (queryString ? "?" + queryString : "")

        const headers: HeadersInit = auth
          ? getAuthHeaders(request)
          : { "Content-Type": "application/json" }

        const fetchOptions: RequestInit = { method, headers }

        if (method !== "GET" && method !== "DELETE") {
          try {
            const body = await request.json()
            fetchOptions.body = JSON.stringify(body)
          } catch {
            // No body or invalid JSON
          }
        } else if (method === "DELETE") {
          try {
            const body = await request.json()
            if (body && Object.keys(body).length > 0) {
              fetchOptions.body = JSON.stringify(body)
            }
          } catch {
            // No body for DELETE is fine
          }
        }

        const response = await fetch(url, fetchOptions)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          return NextResponse.json(
            { error: "Backend error on " + method + " " + resolvedPath, details: errorData },
            { status: response.status }
          )
        }

        const data = await response.json()
        const result = onResponse ? onResponse(data) : data
        return NextResponse.json(result)
      } catch (error) {
        return NextResponse.json(
          { error: "Erro ao conectar com o backend" },
          { status: 500 }
        )
      }
    }
  }

  const handlers = {} as Record<string, HandlerFn>
  for (const method of methods) {
    handlers[method] = makeHandler(method)
  }

  return { dynamic: "force-dynamic" as const, ...handlers } as ProxyResult<M>
}
