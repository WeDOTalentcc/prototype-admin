/**
 * WT-2022 Fase 4 — useUIAction settings_open_tab bridge tests
 *
 * Garante que dispatcher `settings_open_tab` (chat tools toggle_learning_loop,
 * toggle_lia_field, record_dsr_action) emite os 2 CustomEvents canonical:
 *   1. `lia:settings-action` (canonical — consumido por SettingsPageEnhanced:327)
 *   2. `settings-open-tab` (legado paralelo — backcompat com handlers antigos)
 *
 * Padrão de testes baseado em `plataforma-lia/src/hooks/__tests__/use-ui-action.test.ts`
 * (PR-D, skill lia-testing PARTE 1 — Vitest + @testing-library/react).
 *
 * Ref:
 * - `~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2022-policy-engine-migration.md`
 *   (companion ADR Fase 4 settings bridge)
 * - `plataforma-lia/src/hooks/chat/useUIAction.ts:147-187` (impl canonical)
 */

import { useUIAction } from "@/hooks/chat/useUIAction";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ─── Mocks ───────────────────────────────────────────────────────────────

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn(), back: vi.fn() }),
}));

let dispatchEventSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  pushMock.mockClear();
  dispatchEventSpy = vi.spyOn(window, "dispatchEvent");
});

afterEach(() => {
  dispatchEventSpy.mockRestore();
});

// ─── Helpers ─────────────────────────────────────────────────────────────

function eventsOfType(
  spy: ReturnType<typeof vi.spyOn>,
  type: string,
): CustomEvent[] {
  return spy.mock.calls
    .map(([event]) => event as CustomEvent)
    .filter((event) => event && typeof event === "object" && event.type === type);
}

// ─── Suites ──────────────────────────────────────────────────────────────

describe("useUIAction — settings_open_tab bridge (WT-2022 Fase 4)", () => {
  it("dispatches `lia:settings-action` CustomEvent with full payload", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatch("settings_open_tab", {
        section: "minha-empresa",
        subsection: "learning-loops",
        field: "bigfive_company_culture",
      });
    });

    const liaEvents = eventsOfType(dispatchEventSpy, "lia:settings-action");
    expect(liaEvents.length).toBeGreaterThanOrEqual(1);

    const detail = liaEvents[0].detail as {
      actionId: string;
      section: string;
      subsection?: string;
      field?: string;
      source: string;
    };
    expect(detail.actionId).toBe("settings_open_tab");
    expect(detail.section).toBe("minha-empresa");
    expect(detail.subsection).toBe("learning-loops");
    expect(detail.field).toBe("bigfive_company_culture");
    expect(detail.source).toBe("chat");
  });

  it("also dispatches legacy `settings-open-tab` event in parallel (backcompat)", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatch("settings_open_tab", { section: "governanca" });
    });

    const legacyEvents = eventsOfType(dispatchEventSpy, "settings-open-tab");
    expect(legacyEvents.length).toBeGreaterThanOrEqual(1);
    expect(legacyEvents[0].detail).toBe("governanca");
  });

  it("returns true (handled) when action is `settings_open_tab` with valid section", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = false;
    act(() => {
      handled = result.current.dispatch("settings_open_tab", {
        section: "fairness-compliance",
      });
    });

    expect(handled).toBe(true);
  });

  it("router.push deep-link `/configuracoes?section=...&subsection=...&field=...`", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatch("settings_open_tab", {
        section: "minha-empresa",
        subsection: "learning-loops",
        field: "bigfive_company_culture",
      });
    });

    expect(pushMock).toHaveBeenCalledTimes(1);
    const calledWith = pushMock.mock.calls[0][0] as string;
    expect(calledWith).toContain("/configuracoes?");
    expect(calledWith).toContain("section=minha-empresa");
    expect(calledWith).toContain("subsection=learning-loops");
    expect(calledWith).toContain("field=bigfive_company_culture");
  });

  it("returns false when section param is missing (fail-soft)", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = true;
    act(() => {
      handled = result.current.dispatch("settings_open_tab", {});
    });

    expect(handled).toBe(false);
    // Nenhum CustomEvent canonical emitido quando section ausente
    const liaEvents = eventsOfType(dispatchEventSpy, "lia:settings-action");
    expect(liaEvents.length).toBe(0);
  });

  it("omits subsection/field from detail when not provided", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatch("settings_open_tab", { section: "governanca" });
    });

    const liaEvents = eventsOfType(dispatchEventSpy, "lia:settings-action");
    const detail = liaEvents[0].detail as Record<string, unknown>;
    expect(detail.section).toBe("governanca");
    expect(detail.subsection).toBeUndefined();
    expect(detail.field).toBeUndefined();
  });
});
