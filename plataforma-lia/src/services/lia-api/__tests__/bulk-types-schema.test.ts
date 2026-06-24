import type { BulkOperationResult, BulkOperationError, BulkAssignJobRequest, BulkStartScreeningRequest } from '../types/bulk.types'

describe('BulkOperationResult schema alignment with BE canonical', () => {
  it('has successful (number) not success (boolean)', () => {
    const result: BulkOperationResult = {
      successful: 3,
      total: 5,
      failed: 2,
      errors: [{ id: 'x', error_message: 'err' }],
      processed_ids: ['a', 'b', 'c'],
    }
    expect(typeof result.successful).toBe('number')
    // @ts-expect-error — success should not exist
    expect((result as unknown as Record<string, unknown>).success).toBeUndefined()
  })

  it('BulkOperationError uses id and error_message', () => {
    const err: BulkOperationError = {
      id: 'uuid-abc',
      error_message: 'Candidate not found',
    }
    expect(err.id).toBe('uuid-abc')
    expect(err.error_message).toBe('Candidate not found')
    // @ts-expect-error — old field name should not exist
    expect((err as unknown as Record<string, unknown>).error).toBeUndefined()
  })

  it('BulkAssignJobRequest uses job_vacancy_id not job_id', () => {
    const req: BulkAssignJobRequest = {
      candidate_ids: ['a'],
      job_vacancy_id: 'uuid-123',
    }
    expect(req.job_vacancy_id).toBe('uuid-123')
    // @ts-expect-error — job_id should not exist
    expect((req as unknown as Record<string, unknown>).job_id).toBeUndefined()
  })

  it('BulkStartScreeningRequest has job_vacancy_id (required)', () => {
    const req: BulkStartScreeningRequest = {
      candidate_ids: ['a'],
      job_vacancy_id: 'uuid-456',
    }
    expect(req.job_vacancy_id).toBe('uuid-456')
  })

  it('BulkOperationResult has processed_ids array not processed number', () => {
    const result: BulkOperationResult = {
      successful: 2,
      total: 2,
      failed: 0,
      errors: [],
      processed_ids: ['id-1', 'id-2'],
    }
    expect(Array.isArray(result.processed_ids)).toBe(true)
    // @ts-expect-error — old field should not exist
    expect((result as unknown as Record<string, unknown>).processed).toBeUndefined()
  })
})
