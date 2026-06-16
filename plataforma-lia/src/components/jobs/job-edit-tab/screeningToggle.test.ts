import { describe, it, expect } from "vitest"

import { screeningToggleState } from "./screeningToggle"

describe("screeningToggleState", () => {
  it("active → toggle checked", () => {
    expect(screeningToggleState("active")).toEqual({ mode: "toggle", checked: true })
  })
  it("paused → toggle unchecked", () => {
    expect(screeningToggleState("paused")).toEqual({ mode: "toggle", checked: false })
  })
  it("not_started → toggle unchecked", () => {
    expect(screeningToggleState("not_started")).toEqual({ mode: "toggle", checked: false })
  })
  it("completed → readonly", () => {
    expect(screeningToggleState("completed").mode).toBe("readonly")
  })
  it("not_configured → configure", () => {
    expect(screeningToggleState("not_configured").mode).toBe("configure")
  })
  it("undefined/null → configure", () => {
    expect(screeningToggleState(undefined).mode).toBe("configure")
    expect(screeningToggleState(null).mode).toBe("configure")
  })
})
