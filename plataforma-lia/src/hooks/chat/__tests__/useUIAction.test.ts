import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useUIAction } from "@/hooks/chat/useUIAction";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ locale: "pt" }),
}));

describe("useUIAction — apply_table_state (Fase 2 slice 1)", () => {
  let dispatchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    dispatchSpy = vi.spyOn(window, "dispatchEvent");
  });

  afterEach(() => {
    dispatchSpy.mockRestore();
  });

  it("despacha lia:apply_table_state com surface+patch e retorna true", () => {
    const { result } = renderHook(() => useUIAction());

    const handled = result.current.dispatch("apply_table_state", {
      surface: "candidates",
      patch: { search: "João" },
    });

    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:apply_table_state",
      );
    expect(ev).toBeDefined();
    expect(ev!.detail).toEqual({
      surface: "candidates",
      patch: { search: "João" },
    });
  });

  it("despacha surface jobs (lista de Vagas) e retorna true", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("apply_table_state", {
      surface: "jobs",
      patch: { search: "backend", filter: "ativas" },
    });
    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:apply_table_state",
      );
    expect(ev!.detail).toEqual({
      surface: "jobs",
      patch: { search: "backend", filter: "ativas" },
    });
  });

  it("rejeita surface desconhecida", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("apply_table_state", {
      surface: "kanban",
      patch: { search: "x" },
    });
    expect(handled).toBe(false);
  });

  it("rejeita patch ausente/inválido", () => {
    const { result } = renderHook(() => useUIAction());
    expect(
      result.current.dispatch("apply_table_state", { surface: "candidates" }),
    ).toBe(false);
  });
});
