import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

vi.mock("../TransportModeIndicator", () => ({
  TransportModeIndicator: () => null,
}));

import { UnifiedChatHeader } from "../UnifiedChatHeader";

function renderHeader(props: Partial<React.ComponentProps<typeof UnifiedChatHeader>> = {}) {
  const onDelete = props.onDelete ?? vi.fn();
  const merged: React.ComponentProps<typeof UnifiedChatHeader> = {
    mode: "sidebar",
    onModeChange: vi.fn(),
    onClose: vi.fn(),
    onNewChat: vi.fn(),
    conversationTitle: "Conversa atual",
    isConnected: true,
    onDelete,
    ...props,
  };
  const utils = render(<UnifiedChatHeader {...merged} />);
  return { ...utils, onDelete };
}

function openOptionsAndClickDelete() {
  // Both the title button and the kebab open the same menu — the kebab is
  // labelled `optionsLabel` (mocked translator returns the key).
  const optionsButtons = screen.getAllByLabelText("optionsLabel");
  fireEvent.click(optionsButtons[0]);
  const deleteItem = screen.getByText("delete");
  fireEvent.click(deleteItem);
}

describe("UnifiedChatHeader — delete conversation dialog", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does NOT use window.confirm anymore", () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const { onDelete } = renderHeader();
    openOptionsAndClickDelete();
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(onDelete).not.toHaveBeenCalled();
  });

  it("opens the AlertDialog when the delete menu item is clicked", () => {
    renderHeader();
    openOptionsAndClickDelete();
    expect(screen.getByTestId("delete-conversation-dialog")).toBeTruthy();
    expect(screen.getByText("deleteTitle")).toBeTruthy();
    expect(screen.getByText("deleteDescription")).toBeTruthy();
  });

  it("cancelling the dialog does NOT invoke onDelete", async () => {
    const { onDelete } = renderHeader();
    openOptionsAndClickDelete();
    fireEvent.click(screen.getByText("deleteCancel"));
    await waitFor(() => {
      expect(screen.queryByTestId("delete-conversation-dialog")).toBeNull();
    });
    expect(onDelete).not.toHaveBeenCalled();
  });

  it("confirming the dialog invokes onDelete exactly once and closes the dialog", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    renderHeader({ onDelete });
    openOptionsAndClickDelete();
    await act(async () => {
      fireEvent.click(screen.getByTestId("delete-conversation-confirm"));
    });
    expect(onDelete).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.queryByTestId("delete-conversation-dialog")).toBeNull();
    });
  });

  it("keeps the dialog open while the async onDelete is pending", async () => {
    let resolveDelete: (() => void) | null = null;
    const onDelete = vi.fn(
      () => new Promise<void>((resolve) => {
        resolveDelete = resolve;
      }),
    );
    renderHeader({ onDelete });
    openOptionsAndClickDelete();
    fireEvent.click(screen.getByTestId("delete-conversation-confirm"));
    // Dialog still visible while promise is pending
    expect(screen.getByTestId("delete-conversation-dialog")).toBeTruthy();
    expect(onDelete).toHaveBeenCalledTimes(1);
    await act(async () => {
      resolveDelete?.();
    });
    await waitFor(() => {
      expect(screen.queryByTestId("delete-conversation-dialog")).toBeNull();
    });
  });
});
