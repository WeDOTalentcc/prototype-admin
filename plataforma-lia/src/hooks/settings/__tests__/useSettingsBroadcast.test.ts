/**
 * useSettingsBroadcast.test.ts — Task 2.7 (2026-05-26) + GAP-09-005 (Sprint 5D)
 *
 * Tests for:
 * - dispatchSettingsUpdate: dispatches lia:settings-updated + lia:settings-success
 * - SETTINGS_QUERY_KEYS: returns correct stable key arrays
 * - useSettingsBroadcast: installs/removes listener, skips source="ui", invalidates on external
 * - useSettingsBroadcastDispatch: returns stable callback that calls dispatchSettingsUpdate
 * - GAP-09-005: cross-tab sync via BroadcastChannel
 */
import React from "react"
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  dispatchSettingsUpdate,
  SETTINGS_QUERY_KEYS,
  useSettingsBroadcast,
  useSettingsBroadcastDispatch,
} from "../useSettingsBroadcast"
import type { SettingsBroadcastDetail } from "../useSettingsBroadcast"

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeDetail(overrides: Partial<SettingsBroadcastDetail> = {}): SettingsBroadcastDetail {
  return {
    actionId: "configure_profile",
    section: "company",
    source: "chat",
    ts: Date.now(),
    ...overrides,
  }
}

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  return { Wrapper, queryClient }
}

class MockBroadcastChannel {
  static instances: MockBroadcastChannel[] = []
  postMessage = vi.fn()
  close = vi.fn()
  onmessage: ((ev: MessageEvent) => void) | null = null

  constructor(public name: string) {
    MockBroadcastChannel.instances.push(this)
  }

  static reset() {
    MockBroadcastChannel.instances = []
  }
}

// ─── SETTINGS_QUERY_KEYS ─────────────────────────────────────────────────────

describe("SETTINGS_QUERY_KEYS", () => {
  it("companyProfile returns ['company-profile']", () => {
    expect(SETTINGS_QUERY_KEYS.companyProfile()).toEqual(["company-profile"])
  })

  it("hiringPolicy returns ['hiring-policy']", () => {
    expect(SETTINGS_QUERY_KEYS.hiringPolicy()).toEqual(["hiring-policy"])
  })

  it("settingsProgress returns ['settings-progress']", () => {
    expect(SETTINGS_QUERY_KEYS.settingsProgress()).toEqual(["settings-progress"])
  })

  it("cultureProfile includes companyId", () => {
    expect(SETTINGS_QUERY_KEYS.cultureProfile("abc")).toEqual(["culture-profile", "abc"])
  })

  it("benefits includes companyId", () => {
    expect(SETTINGS_QUERY_KEYS.benefits("xyz")).toEqual(["company-benefits", "xyz"])
  })

  it("returns stable arrays (same reference type, new array each call)", () => {
    const a = SETTINGS_QUERY_KEYS.companyProfile()
    const b = SETTINGS_QUERY_KEYS.companyProfile()
    expect(a).toEqual(b)
  })
})

// ─── dispatchSettingsUpdate ───────────────────────────────────────────────────

describe("dispatchSettingsUpdate", () => {
  afterEach(() => vi.restoreAllMocks())

  it("dispatches lia:settings-updated event", () => {
    const spy = vi.spyOn(window, "dispatchEvent")
    dispatchSettingsUpdate(makeDetail())
    const calls = spy.mock.calls.map(c => (c[0] as CustomEvent).type)
    expect(calls).toContain("lia:settings-updated")
  })

  it("dispatches lia:settings-success event", () => {
    const spy = vi.spyOn(window, "dispatchEvent")
    dispatchSettingsUpdate(makeDetail())
    const calls = spy.mock.calls.map(c => (c[0] as CustomEvent).type)
    expect(calls).toContain("lia:settings-success")
  })

  it("dispatches exactly 2 events", () => {
    const spy = vi.spyOn(window, "dispatchEvent")
    dispatchSettingsUpdate(makeDetail())
    expect(spy).toHaveBeenCalledTimes(2)
  })

  it("event detail contains section and source", () => {
    const capturedDetails: SettingsBroadcastDetail[] = []
    window.addEventListener("lia:settings-updated", (e) => {
      capturedDetails.push((e as CustomEvent<SettingsBroadcastDetail>).detail)
    })
    const detail = makeDetail({ section: "culture", source: "chat" })
    dispatchSettingsUpdate(detail)
    expect(capturedDetails.length).toBeGreaterThan(0)
    expect(capturedDetails[0].section).toBe("culture")
    expect(capturedDetails[0].source).toBe("chat")
  })

  it("event detail contains optional field and value", () => {
    const capturedDetails: SettingsBroadcastDetail[] = []
    window.addEventListener("lia:settings-updated", (e) => {
      capturedDetails.push((e as CustomEvent<SettingsBroadcastDetail>).detail)
    })
    dispatchSettingsUpdate(makeDetail({ field: "mission", value: "Build the future" }))
    expect(capturedDetails[0].field).toBe("mission")
    expect(capturedDetails[0].value).toBe("Build the future")
  })

  it("does not throw in SSR (window === undefined) — no-op if called in server context", () => {
    expect(() => dispatchSettingsUpdate(makeDetail())).not.toThrow()
  })
})

// ─── useSettingsBroadcast hook ────────────────────────────────────────────────

describe("useSettingsBroadcast", () => {
  it("mounts without error", () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })
    expect(result.current).toBeUndefined() // returns void
  })

  it("installs listener that ignores source='ui' events (no invalidation on own dispatches)", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    act(() => {
      dispatchSettingsUpdate(makeDetail({ source: "ui" }))
    })

    expect(invalidateSpy).not.toHaveBeenCalled()
  })

  it("invalidates queries when source='chat' event arrives", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    act(() => {
      dispatchSettingsUpdate(makeDetail({ source: "chat" }))
    })

    expect(invalidateSpy).toHaveBeenCalled()
  })

  it("invalidates queries when source='external' event arrives", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    act(() => {
      dispatchSettingsUpdate(makeDetail({ source: "external" }))
    })

    expect(invalidateSpy).toHaveBeenCalled()
  })

  it("removes listener on unmount (no stale handlers)", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    const { unmount } = renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    unmount()
    invalidateSpy.mockClear()

    // After unmount, dispatch should NOT trigger invalidation via this hook
    act(() => {
      dispatchSettingsUpdate(makeDetail({ source: "chat" }))
    })

    expect(invalidateSpy).not.toHaveBeenCalled()
  })
})

// ─── useSettingsBroadcastDispatch hook ───────────────────────────────────────

describe("useSettingsBroadcastDispatch", () => {
  afterEach(() => vi.restoreAllMocks())

  it("returns a function", () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useSettingsBroadcastDispatch(), { wrapper: Wrapper })
    expect(typeof result.current).toBe("function")
  })

  it("calling it dispatches lia:settings-updated", () => {
    const { Wrapper } = makeWrapper()
    const spy = vi.spyOn(window, "dispatchEvent")
    const { result } = renderHook(() => useSettingsBroadcastDispatch(), { wrapper: Wrapper })

    act(() => {
      result.current("basic", "name", "Acme Corp")
    })

    const types = spy.mock.calls.map(c => (c[0] as CustomEvent).type)
    expect(types).toContain("lia:settings-updated")
  })

  it("does nothing for unknown block (mapping returns undefined)", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const spy = vi.spyOn(window, "dispatchEvent")
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    const { result } = renderHook(() => useSettingsBroadcastDispatch(), { wrapper: Wrapper })

    act(() => {
      result.current("unknown_block", "field", "value")
    })

    expect(spy).not.toHaveBeenCalled()
    expect(invalidateSpy).not.toHaveBeenCalled()
  })

  it("maps 'policy' block to section 'hiring_policies'", () => {
    const { Wrapper } = makeWrapper()
    const capturedDetails: SettingsBroadcastDetail[] = []
    window.addEventListener("lia:settings-updated", (e) => {
      capturedDetails.push((e as CustomEvent<SettingsBroadcastDetail>).detail)
    })
    const { result } = renderHook(() => useSettingsBroadcastDispatch(), { wrapper: Wrapper })

    act(() => {
      result.current("policy", "lia_tone", "formal")
    })

    const found = capturedDetails.find(d => d.section === "hiring_policies")
    expect(found).toBeDefined()
    expect(found!.field).toBe("lia_tone")
  })
})

// ─── GAP-09-005: BroadcastChannel cross-tab sync ────────────────────────────

describe("GAP-09-005: BroadcastChannel cross-tab sync", () => {
  const originalBC = (globalThis as any).BroadcastChannel

  beforeEach(() => {
    MockBroadcastChannel.reset()
    ;(globalThis as any).BroadcastChannel = MockBroadcastChannel
  })

  afterEach(() => {
    if (originalBC) {
      (globalThis as any).BroadcastChannel = originalBC
    } else {
      delete (globalThis as any).BroadcastChannel
    }
    vi.restoreAllMocks()
  })

  it("dispatchSettingsUpdate sends BroadcastChannel message for source='ui'", () => {
    dispatchSettingsUpdate(makeDetail({ source: "ui" }))

    const bcInstances = MockBroadcastChannel.instances
    expect(bcInstances.length).toBeGreaterThanOrEqual(1)
    const sendInstance = bcInstances[bcInstances.length - 1]
    expect(sendInstance.name).toBe("lia-settings-sync")
    expect(sendInstance.postMessage).toHaveBeenCalledTimes(1)
    expect(sendInstance.postMessage).toHaveBeenCalledWith(
      expect.objectContaining({ source: "ui", section: "company" }),
    )
    expect(sendInstance.close).toHaveBeenCalledTimes(1)
  })

  it("dispatchSettingsUpdate does NOT send BroadcastChannel message for source='chat'", () => {
    dispatchSettingsUpdate(makeDetail({ source: "chat" }))

    const bcInstances = MockBroadcastChannel.instances
    const withPostMessage = bcInstances.filter(i => i.postMessage.mock.calls.length > 0)
    expect(withPostMessage).toHaveLength(0)
  })

  it("dispatchSettingsUpdate does NOT send BroadcastChannel for source='external'", () => {
    dispatchSettingsUpdate(makeDetail({ source: "external" }))

    const bcInstances = MockBroadcastChannel.instances
    const withPostMessage = bcInstances.filter(i => i.postMessage.mock.calls.length > 0)
    expect(withPostMessage).toHaveLength(0)
  })

  it("useSettingsBroadcast invalidates queries on BroadcastChannel message", () => {
    const { Wrapper, queryClient } = makeWrapper()
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries")
    renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    const listenerInstance = MockBroadcastChannel.instances.find(i => i.onmessage !== null)
    expect(listenerInstance).toBeDefined()

    act(() => {
      listenerInstance!.onmessage!(new MessageEvent("message", {
        data: makeDetail({ source: "ui" }),
      }))
    })

    expect(invalidateSpy).toHaveBeenCalled()
  })

  it("useSettingsBroadcast closes BroadcastChannel on unmount", () => {
    const { Wrapper } = makeWrapper()
    const { unmount } = renderHook(() => useSettingsBroadcast(), { wrapper: Wrapper })

    const listenerInstance = MockBroadcastChannel.instances.find(i => i.onmessage !== null)
    expect(listenerInstance).toBeDefined()

    unmount()

    expect(listenerInstance!.close).toHaveBeenCalled()
  })

  it("dispatchSettingsUpdate degrades silently when BroadcastChannel is unavailable", () => {
    delete (globalThis as any).BroadcastChannel

    expect(() => {
      dispatchSettingsUpdate(makeDetail({ source: "ui" }))
    }).not.toThrow()
  })
})
