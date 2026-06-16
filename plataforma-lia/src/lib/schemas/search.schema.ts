import { z } from 'zod'

export const searchQuerySchema = z.object({
  query: z.string().min(1).max(500),
  filters: z.record(z.string(), z.unknown()).optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).optional(),
})

export const semanticSearchSchema = z.object({
  query: z.string().min(1).max(1000),
  jobId: z.string().optional(),
  filters: z.record(z.string(), z.unknown()).optional(),
  limit: z.coerce.number().int().min(1).max(50).default(10),
})
