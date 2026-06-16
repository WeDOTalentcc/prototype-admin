import { describe, it, expect } from "vitest"
import { bulkDeleteSchema } from "@/lib/schemas/candidate.schema"

/**
 * Contract tests for bulk delete Zod schema — pins N1/N2 fixes.
 * RED tests (TDD): bulkDeleteSchema currently lacks permanent/hard_delete fields.
 *
 * Fix: extend bulkDeleteSchema to include:
 *   - permanent: z.boolean().default(false)
 *   - hard_delete: z.boolean().optional().transform() → sets permanent
 */
describe("bulkDeleteSchema — N1/N2 contract", () => {
  it("passes permanent field through to BE", () => {
    const result = bulkDeleteSchema.parse({
      candidate_ids: ["abc"],
      permanent: true,
    })
    expect(result).toHaveProperty("permanent", true)
  })

  it("transforms hard_delete to permanent for BE compatibility", () => {
    const result = bulkDeleteSchema.parse({
      candidate_ids: ["abc"],
      hard_delete: true,
    })
    expect(result).toHaveProperty("permanent", true)
  })

  it("defaults permanent to false when neither field provided", () => {
    const result = bulkDeleteSchema.parse({
      candidate_ids: ["abc"],
    })
    expect(result).toHaveProperty("permanent", false)
  })

  it("rejects empty candidate_ids", () => {
    expect(() => bulkDeleteSchema.parse({ candidate_ids: [] })).toThrow()
  })
})
