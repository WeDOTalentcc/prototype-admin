import { z } from 'zod'

export const idSchema = z.object({
  id: z.string().min(1, 'ID is required'),
})

export const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
})

export const bulkIdsSchema = z.object({
  candidate_ids: z.array(z.string().min(1)).min(1, 'At least one candidate_id is required'),
})
