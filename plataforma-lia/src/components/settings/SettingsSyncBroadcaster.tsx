"use client"

import { useEffect } from "react"

/**
 * SettingsSyncBroadcaster — Task #712
 *
 * Bidirectional sync glue: intercepts successful writes to
 * `/api/backend-proxy/company/...` and `/api/backend-proxy/workforce`
 * endpoints (the ones used by the settings hubs) and broadcasts:
 *
 *   - `lia:settings-success` — picked up by the OnboardingActionOrchestrator
 *     to advance the state machine.
 *   - `lia:settings-updated` — picked up by the chat context assembly to
 *     inject a silent "system note" into LIA's next turn (so the assistant
 *     knows the user just edited settings via the UI).
 *
 * Implemented as a fetch wrapper installed once at app shell mount time.
 * The original window.fetch is preserved and called through. We never
 * mutate request/response bodies — only observe successful PUT/PATCH/POST
 * to the relevant endpoints.
 */

const ENDPOINT_TO_ACTION: Array<{
  match: RegExp
  actionId: string
  section: string
}> = [
  {
    match: /\/api\/backend-proxy\/company\/culture-profile(\/|$|\?)/,
    actionId: "configure_culture",
    section: "culture",
  },
  {
    match: /\/api\/backend-proxy\/company\/benefits(\/|$|\?)/,
    actionId: "configure_benefits",
    section: "benefits",
  },
  {
    match: /\/api\/backend-proxy\/company\/profile(\/|$|\?)/,
    actionId: "configure_profile",
    section: "profile",
  },
  {
    match: /\/api\/backend-proxy\/company\/tech-stack(\/|$|\?)/,
    actionId: "configure_tech_stack",
    section: "tech_stack",
  },
  {
    match: /\/api\/backend-proxy\/workforce(\/|$|\?)/,
    actionId: "configure_workforce",
    section: "workforce",
  },
  {
    match: /\/api\/backend-proxy\/company\/hiring-policies(\/|$|\?)/,
    actionId: "configure_culture",
    section: "hiring_policies",
  },
]

const WRITE_METHODS = new Set(["POST", "PUT", "PATCH"])

let installed = false

function installInterceptor() {
  if (typeof window === "undefined") return
  if (installed) return
  installed = true
  const original = window.fetch.bind(window)
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const method = (init?.method || (typeof input !== "string" && "method" in (input as Request) ? (input as Request).method : "GET") || "GET").toUpperCase()
    const url = typeof input === "string"
      ? input
      : input instanceof URL
        ? input.toString()
        : (input as Request).url

    const response = await original(input, init)

    try {
      if (
        WRITE_METHODS.has(method) &&
        response.ok &&
        typeof url === "string"
      ) {
        const match = ENDPOINT_TO_ACTION.find((e) => e.match.test(url))
        if (match) {
          // Best-effort body parsing for the chat note.
          let bodySummary: unknown = undefined
          try {
            if (init?.body && typeof init.body === "string") {
              bodySummary = JSON.parse(init.body)
            }
          } catch {
            bodySummary = undefined
          }
          window.dispatchEvent(
            new CustomEvent("lia:settings-success", {
              detail: {
                actionId: match.actionId,
                section: match.section,
                source: "ui",
                url,
                method,
              },
            }),
          )
          window.dispatchEvent(
            new CustomEvent("lia:settings-updated", {
              detail: {
                actionId: match.actionId,
                section: match.section,
                source: "ui",
                url,
                method,
                payload: bodySummary,
                ts: Date.now(),
              },
            }),
          )
        }
      }
    } catch {
      // Never let observability break the actual response flow.
    }

    return response
  }
}

export function SettingsSyncBroadcaster() {
  useEffect(() => {
    installInterceptor()
  }, [])
  return null
}
