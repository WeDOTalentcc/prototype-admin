import { describe, it, expect, vi, beforeEach } from 'vitest'
import { bulkExport } from '../bulk-api'

// Mock getAuthHeaders
vi.mock('../base', () => ({
  getAuthHeaders: () => ({ 'Content-Type': 'application/json', Authorization: 'Bearer test' }),
}))

function makeResponse(opts: {
  ok?: boolean
  contentType?: string
  formatFallback?: string
  body?: string | Blob
}) {
  const headers = new Headers()
  if (opts.contentType) headers.set('content-type', opts.contentType)
  if (opts.formatFallback) headers.set('X-Format-Fallback', opts.formatFallback)

  return {
    ok: opts.ok ?? true,
    headers,
    blob: vi.fn().mockResolvedValue(new Blob(['csv,data'], { type: opts.contentType ?? 'text/csv' })),
    json: vi.fn().mockResolvedValue({ total: 0, successful: 0, failed: 0, errors: [], processed_ids: [] }),
    statusText: 'OK',
  } as unknown as Response
}

describe('bulkExport — X-Format-Fallback detection', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('returns formatFallback=false when no X-Format-Fallback header', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      makeResponse({ contentType: 'text/csv' })
    ))
    const result = await bulkExport({ candidate_ids: ['a'], format: 'xlsx' })
    expect('blob' in result).toBe(true)
    if ('blob' in result) {
      expect(result.formatFallback).toBe(false)
    }
  })

  it('returns formatFallback=true when X-Format-Fallback: xlsx-unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      makeResponse({ contentType: 'text/csv', formatFallback: 'xlsx-unavailable' })
    ))
    const result = await bulkExport({ candidate_ids: ['a'], format: 'xlsx' })
    expect('blob' in result).toBe(true)
    if ('blob' in result) {
      expect(result.formatFallback).toBe(true)
      expect(result.blob).toBeInstanceOf(Blob)
    }
  })

  it('returns formatFallback=false for other X-Format-Fallback values', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      makeResponse({ contentType: 'text/csv', formatFallback: 'some-other-value' })
    ))
    const result = await bulkExport({ candidate_ids: ['a'], format: 'csv' })
    expect('blob' in result).toBe(true)
    if ('blob' in result) {
      expect(result.formatFallback).toBe(false)
    }
  })

  it('returns BulkOperationResult (JSON) when response is not a file', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      makeResponse({ contentType: 'application/json' })
    ))
    const result = await bulkExport({ candidate_ids: ['a'], format: 'csv' })
    expect('blob' in result).toBe(false)
    expect('successful' in result).toBe(true)
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      headers: new Headers(),
      json: vi.fn().mockResolvedValue({ detail: 'No valid candidates' }),
      statusText: 'Not Found',
    } as unknown as Response))
    await expect(bulkExport({ candidate_ids: [], format: 'xlsx' })).rejects.toThrow('No valid candidates')
  })
})
