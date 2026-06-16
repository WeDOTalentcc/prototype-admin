import { NextRequest, NextResponse } from "next/server"
import type { ZodSchema } from "zod"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const RAILS_BACKEND_URL = process.env.RAILS_BACKEND_URL || ""

type BackendTarget = "fastapi" | "rails"

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH"

type HandlerFn = (
  request: NextRequest,
  context: { params: Promise<Record<string, string>> }
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
  /** Backend target for Rails migration. Defaults to "fastapi". When "rails" AND RAILS_BACKEND_URL is set, routes to Rails. */
  backendTarget?: BackendTarget
  /** Default query params appended to every request */
  defaultParams?: Record<string, string>
  /** Transform the response data before returning to the client */
  onResponse?: (data: unknown) => unknown
  /** Optional Zod schema to validate the request body for non-GET/DELETE methods. Returns 400 on failure. */
  bodySchema?: ZodSchema<unknown>
  /** Override the default 10s proxy timeout for slow endpoints (e.g. AI search). In ms. */
  timeoutMs?: number
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

function resolveBackendUrl(target: BackendTarget): string {
  if (target === "rails" && RAILS_BACKEND_URL) {
    return RAILS_BACKEND_URL
  }
  return BACKEND_URL
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
 *
 * Usage (explicit FastAPI target):
 *   export const { dynamic, GET, POST } = createProxyHandlers({
 *     backendPath: "/api/v1/candidates",
 *     methods: ["GET", "POST"],
 *     backendTarget: "fastapi",
 *   })
 */
export function createProxyHandlers<M extends HttpMethod = "GET">(
  config: ProxyConfig<M>
): ProxyResult<M> {
  const {
    backendPath,
    methods = ["GET"] as unknown as M[],
    auth = true,
    backendTarget = "fastapi",
    defaultParams,
    onResponse,
    bodySchema,
    timeoutMs = 10000,
  } = config

  const hasParams = backendPath.includes(":")

  function makeHandler(method: string): HandlerFn {
    return async (
      request: NextRequest,
      context: { params: Promise<Record<string, string>> }
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
        const baseUrl = resolveBackendUrl(backendTarget)
        const url = baseUrl + resolvedPath + (queryString ? "?" + queryString : "")

        const headers: HeadersInit = auth
          ? getAuthHeaders(request)
          : { "Content-Type": "application/json" }

        const fetchOptions: RequestInit = { method, headers }

        if (method !== "GET" && method !== "DELETE") {
          if (bodySchema) {
            let raw: unknown
            try {
              raw = await request.json()
            } catch {
              return NextResponse.json(
                { error: "Invalid JSON body" },
                { status: 400 }
              )
            }
            const parsed = bodySchema.safeParse(raw)
            if (!parsed.success) {
              return NextResponse.json(
                { error: "Validation error", details: parsed.error.flatten() },
                { status: 400 }
              )
            }
            fetchOptions.body = JSON.stringify(parsed.data)
          } else {
            try {
              const body = await request.json()
              fetchOptions.body = JSON.stringify(body)
            } catch {
              // No body or invalid JSON
            }
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

        const response = await fetch(url, { ...fetchOptions, signal: AbortSignal.timeout(timeoutMs) })

        if (!response.ok) {
          // Pass the backend response through verbatim — preserve status, body
          // and content-type. The UI needs the original payload (request_id,
          // code, errors, warning_message, etc.) to react correctly to 4xx/5xx.
          let errText = ""
          try {
            errText = await response.text()
          } catch (readErr) {
            // Backend closed the socket mid-response (UND_ERR_SOCKET / stream
            // aborted). Treat as a structured 502 instead of letting the
            // exception bubble up and abort the Next response stream.
            return NextResponse.json(
              {
                error: "Backend disconnected",
                detail: "Backend closed the connection while streaming the error body",
                path: backendPath,
                method,
              },
              { status: 502 }
            )
          }
          const errCt = response.headers.get("content-type") || ""
          if (!errText) {
            return new NextResponse(null, { status: response.status })
          }
          if (errCt.includes("application/json")) {
            return new NextResponse(errText, {
              status: response.status,
              headers: { "Content-Type": "application/json" },
            })
          }
          return new NextResponse(errText, {
            status: response.status,
            headers: { "Content-Type": errCt || "text/plain" },
          })
        }

        // 204/205 (and any explicitly empty body) — pass status through with no JSON.
        if (response.status === 204 || response.status === 205) {
          return new NextResponse(null, { status: response.status })
        }

        let rawText = ""
        try {
          rawText = await response.text()
        } catch (readErr) {
          // Backend closed the socket mid-response. Map to 502 so the UI can
          // render an empty-state instead of seeing a network error in the
          // browser.
          return NextResponse.json(
            {
              error: "Backend disconnected",
              detail: "Backend closed the connection while streaming the response body",
              path: backendPath,
              method,
            },
            { status: 502 }
          )
        }
        if (!rawText) {
          return new NextResponse(null, { status: response.status })
        }

        // If the backend returned non-JSON, pass it through verbatim with its content-type.
        const contentType = response.headers.get("content-type") || ""
        if (!contentType.includes("application/json")) {
          return new NextResponse(rawText, {
            status: response.status,
            headers: { "Content-Type": contentType || "text/plain" },
          })
        }

        let data: unknown
        try {
          data = JSON.parse(rawText)
        } catch {
          return new NextResponse(rawText, {
            status: response.status,
            headers: { "Content-Type": "application/json" },
          })
        }

        // Unwrap FastAPI envelope: {ok: true, data: ..., meta: {}}
        const unwrapped = (data && typeof data === 'object' && 'ok' in data && 'data' in data) ? (data as Record<string, unknown>).data : data
        const result = onResponse ? onResponse(unwrapped) : unwrapped
        return NextResponse.json(result)
      } catch (error) {
        // AbortSignal.timeout fires DOMException name="TimeoutError" (or
        // AbortError on older runtimes). Map to a structured 504 so the UI
        // can distinguish "backend trava" from "backend caiu".
        const isTimeout =
          error instanceof DOMException &&
          (error.name === "TimeoutError" || error.name === "AbortError")
        if (isTimeout) {
          const timeoutSeconds = Math.round(timeoutMs / 1000)
          return NextResponse.json(
            {
              error: "Backend timeout",
              detail: `Backend did not respond within ${timeoutSeconds}s`,
              path: backendPath,
              method,
            },
            { status: 504 }
          )
        }
        return NextResponse.json(
          { error: "Erro ao conectar com o backend" },
          { status: 502 }
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
