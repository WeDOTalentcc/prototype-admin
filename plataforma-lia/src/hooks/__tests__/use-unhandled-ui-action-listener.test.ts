/**
 * PR-D — useUnhandledUIActionListener tests
 */

import { useUnhandledUIActionListener } from "@/hooks/chat/useUnhandledUIActionListener";
import { UNHANDLED_UI_ACTION_EVENT } from "@/types/ui-action";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("useUnhandledUIActionListener", () => {
  it("invoca handler quando lia:unhandled_ui_action é dispatched", () => {
    const handler = vi.fn();
    renderHook(() => useUnhandledUIActionListener(handler));

    window.dispatchEvent(
      new CustomEvent(UNHANDLED_UI_ACTION_EVENT, {
        detail: { action: "move_candidate", params: { candidate_id: "c1" } },
      }),
    );

    expect(handler).toHaveBeenCalledWith("move_candidate", {
      candidate_id: "c1",
    });
  });

  it("não invoca handler se evento sem detail.action", () => {
    const handler = vi.fn();
    renderHook(() => useUnhandledUIActionListener(handler));

    window.dispatchEvent(
      new CustomEvent(UNHANDLED_UI_ACTION_EVENT, { detail: {} }),
    );

    expect(handler).not.toHaveBeenCalled();
  });

  it("desregistra listener on unmount", () => {
    const handler = vi.fn();
    const { unmount } = renderHook(() => useUnhandledUIActionListener(handler));

    unmount();

    window.dispatchEvent(
      new CustomEvent(UNHANDLED_UI_ACTION_EVENT, {
        detail: { action: "move_candidate", params: {} },
      }),
    );

    expect(handler).not.toHaveBeenCalled();
  });

  it("usa versão mais recente do handler (ref pattern)", () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    const { rerender } = renderHook(
      ({ h }) => useUnhandledUIActionListener(h),
      { initialProps: { h: handler1 } },
    );

    rerender({ h: handler2 });

    window.dispatchEvent(
      new CustomEvent(UNHANDLED_UI_ACTION_EVENT, {
        detail: { action: "x", params: {} },
      }),
    );

    expect(handler1).not.toHaveBeenCalled();
    expect(handler2).toHaveBeenCalledWith("x", {});
  });

  it("ignora handler null/undefined sem crash", () => {
    expect(() =>
      renderHook(() => useUnhandledUIActionListener(null)),
    ).not.toThrow();

    expect(() =>
      window.dispatchEvent(
        new CustomEvent(UNHANDLED_UI_ACTION_EVENT, {
          detail: { action: "x", params: {} },
        }),
      ),
    ).not.toThrow();
  });
});
