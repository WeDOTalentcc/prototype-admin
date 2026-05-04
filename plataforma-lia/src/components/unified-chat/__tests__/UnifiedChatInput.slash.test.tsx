import React, { useRef, useState } from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, act } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/components/ui/audio-record-button", () => ({
  AudioRecordButton: () => <button data-testid="audio-mock" />,
}))

vi.mock("../ChatSuggestionsPanel", () => ({
  ChatSuggestionsPanel: () => null,
}))

vi.mock("../ContextConfigPanel", () => ({
  ContextConfigPanel: () => null,
}))

import { UnifiedChatInput } from "../UnifiedChatInput"

function Harness({
  onExecuteSlashCommand,
}: { onExecuteSlashCommand?: (id: string) => void } = {}) {
  const [text, setText] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  return (
    <UnifiedChatInput
      mode="floating"
      inputText={text}
      setInputText={setText}
      onSend={() => {}}
      isStreaming={false}
      isCreating={false}
      isDisabled={false}
      attachedFile={null}
      setAttachedFile={() => {}}
      fileInputRef={fileInputRef}
      onFileButtonClick={() => {}}
      onFileAttach={() => {}}
      onExecuteSlashCommand={onExecuteSlashCommand}
    />
  )
}

describe("UnifiedChatInput — /slash command dropdown", () => {
  beforeEach(() => {
    // jsdom polyfills
    if (!HTMLTextAreaElement.prototype.setSelectionRange) {
      HTMLTextAreaElement.prototype.setSelectionRange = vi.fn()
    }
  })

  it("renders without crashing", () => {
    render(<Harness />)
    expect(screen.getByTestId("chat-input")).toBeTruthy()
  })

  it("opens slash dropdown when user types '/' at start of line", () => {
    render(<Harness />)
    const ta = screen.getByTestId("chat-input") as HTMLTextAreaElement

    act(() => {
      fireEvent.change(ta, { target: { value: "/" } })
    })

    // The dropdown header label is "Comandos" — rendered when items exist.
    expect(screen.getByText("Comandos")).toBeTruthy()
    // At least one canonical command should appear (e.g. "Criar vaga").
    expect(screen.getByText("Criar vaga")).toBeTruthy()
  })

  it("filters dropdown by query after the slash", () => {
    render(<Harness />)
    const ta = screen.getByTestId("chat-input") as HTMLTextAreaElement

    act(() => {
      fireEvent.change(ta, { target: { value: "/aju" } })
    })

    // "/ajuda" should match; "Criar vaga" should not.
    expect(screen.getByText("O que posso fazer?")).toBeTruthy()
    expect(screen.queryByText("Criar vaga")).toBeNull()
  })

  it("closes dropdown on Escape and remounts cleanly", () => {
    const { unmount } = render(<Harness />)
    const ta = screen.getByTestId("chat-input") as HTMLTextAreaElement

    act(() => {
      fireEvent.change(ta, { target: { value: "/" } })
    })
    expect(screen.getByText("Comandos")).toBeTruthy()

    act(() => {
      fireEvent.keyDown(ta, { key: "Escape" })
    })
    expect(screen.queryByText("Comandos")).toBeNull()

    // Boy Scout: ensure rerender doesn't violate rules-of-hooks
    expect(() => unmount()).not.toThrow()
  })
})
