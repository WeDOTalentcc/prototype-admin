/**
 * Tests — CandidateSkillsList canonical building block.
 * Covers: empty state null, maxVisible truncation, overflow button + callback.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { CandidateSkillsList } from "../CandidateSkillsList"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

describe("CandidateSkillsList", () => {
  it("returns null when skills empty", () => {
    const { container } = render(<CandidateSkillsList skills={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it("returns null when skills undefined", () => {
    // @ts-expect-error — testing runtime safety
    const { container } = render(<CandidateSkillsList skills={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it("renders all skills when count <= maxVisible", () => {
    render(<CandidateSkillsList skills={["React", "TypeScript", "Node"]} />)
    expect(screen.getByText("React")).toBeInTheDocument()
    expect(screen.getByText("TypeScript")).toBeInTheDocument()
    expect(screen.getByText("Node")).toBeInTheDocument()
  })

  it("truncates to maxVisible default 5", () => {
    render(<CandidateSkillsList skills={["a", "b", "c", "d", "e", "f", "g"]} />)
    expect(screen.getByText("a")).toBeInTheDocument()
    expect(screen.getByText("e")).toBeInTheDocument()
    expect(screen.queryByText("f")).toBeNull()
    expect(screen.getByText("+2")).toBeInTheDocument()
  })

  it("custom maxVisible respected", () => {
    render(<CandidateSkillsList skills={["a", "b", "c"]} maxVisible={1} />)
    expect(screen.getByText("a")).toBeInTheDocument()
    expect(screen.queryByText("b")).toBeNull()
    expect(screen.getByText("+2")).toBeInTheDocument()
  })

  it("onOverflowClick fires when overflow button clicked", () => {
    const onOverflowClick = vi.fn()
    render(<CandidateSkillsList skills={["a", "b", "c", "d", "e", "f"]} onOverflowClick={onOverflowClick} />)
    fireEvent.click(screen.getByText("+1"))
    expect(onOverflowClick).toHaveBeenCalled()
  })
})
