/**
 * Canonical contract tests for status-config (Sprint 7B-3a part 2).
 *
 * Locks: canonical names (getAgentStatusConfig, AgentStatus, STATUS_MAP)
 * + backward-compat aliases (getSourcingAgentStatusConfig, SourcingAgentStatus, SOURCING_MAP)
 * point to the same canonical implementation.
 */
import { describe, it, expect } from "vitest"
import {
  getAgentStatusConfig,
  getSourcingAgentStatusConfig,
  STATUS_MAP,
  SOURCING_MAP,
} from "../status-config"

describe("status-config canonical", () => {
  it("getAgentStatusConfig retorna shape canonical pra status active", () => {
    const cfg = getAgentStatusConfig("active")
    expect(cfg).toBeDefined()
    expect(cfg).toHaveProperty("dot")
    expect(cfg).toHaveProperty("bg")
    expect(cfg).toHaveProperty("text")
    expect(cfg).toHaveProperty("badge")
    expect(cfg).toHaveProperty("pulse")
    expect(cfg.pulse).toBe(true)
  })

  it("alias getSourcingAgentStatusConfig === getAgentStatusConfig (mesma referência)", () => {
    expect(getSourcingAgentStatusConfig).toBe(getAgentStatusConfig)
  })

  it("alias SOURCING_MAP === STATUS_MAP (mesma referência)", () => {
    expect(SOURCING_MAP).toBe(STATUS_MAP)
  })
})
