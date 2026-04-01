import { describe, it, expect } from "vitest"
import { safeData } from "./safe-data"

describe("safeData", () => {
  const data = {
    name: "Alice",
    age: 30,
    active: true,
    tags: ["frontend", "react"],
    meta: { version: 1 },
    nullField: null,
    undefinedField: undefined,
  }

  const sd = safeData(data as Record<string, unknown>)

  describe("str()", () => {
    it("returns string value for string key", () => {
      expect(sd.str("name")).toBe("Alice")
    })

    it("returns fallback for missing key", () => {
      expect(sd.str("missing", "default")).toBe("default")
    })

    it("returns fallback for null value", () => {
      expect(sd.str("nullField", "fallback")).toBe("fallback")
    })

    it("converts number to string", () => {
      expect(sd.str("age")).toBe("30")
    })
  })

  describe("num()", () => {
    it("returns numeric value", () => {
      expect(sd.num("age")).toBe(30)
    })

    it("returns fallback for missing key", () => {
      expect(sd.num("missing", 99)).toBe(99)
    })

    it("returns 0 as default fallback", () => {
      expect(sd.num("nullField")).toBe(0)
    })
  })

  describe("bool()", () => {
    it("returns boolean value", () => {
      expect(sd.bool("active")).toBe(true)
    })

    it("returns false as default fallback", () => {
      expect(sd.bool("missing")).toBe(false)
    })

    it("returns false for non-boolean value", () => {
      expect(sd.bool("name")).toBe(false)
    })
  })

  describe("arr()", () => {
    it("returns array value", () => {
      expect(sd.arr("tags")).toEqual(["frontend", "react"])
    })

    it("returns empty array for missing key", () => {
      expect(sd.arr("missing")).toEqual([])
    })

    it("returns empty array for non-array value", () => {
      expect(sd.arr("name")).toEqual([])
    })
  })

  describe("rec()", () => {
    it("returns object value", () => {
      expect(sd.rec("meta")).toEqual({ version: 1 })
    })

    it("returns empty object for missing key", () => {
      expect(sd.rec("missing")).toEqual({})
    })

    it("returns empty object for array value", () => {
      expect(sd.rec("tags")).toEqual({})
    })
  })

  describe("raw()", () => {
    it("returns raw value", () => {
      expect(sd.raw("name")).toBe("Alice")
    })

    it("returns undefined for missing key", () => {
      expect(sd.raw("missing")).toBeUndefined()
    })
  })
})
