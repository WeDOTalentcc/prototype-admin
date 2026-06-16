import { z } from 'zod'

export const pathIdSchema = z.object({
  id: z.string().min(1, 'ID is required'),
})

export const pathSlugSchema = z.object({
  slug: z.string().min(1, 'Slug is required'),
})

export const pathProfileIdSchema = z.object({
  profileId: z.string().min(1, 'Profile ID is required'),
})

export const pathCandidateIdSchema = z.object({
  candidateId: z.string().min(1, 'Candidate ID is required'),
})

export const pathJobIdSchema = z.object({
  jobId: z.string().min(1, 'Job ID is required'),
})

export const pathClientIdSchema = z.object({
  id: z.string().min(1, 'Client ID is required'),
})

export const pathInvoiceIdSchema = z.object({
  invoice_id: z.string().min(1, 'Invoice ID is required'),
})

export const pathMethodIdSchema = z.object({
  method_id: z.string().min(1, 'Method ID is required'),
})

export const pathListIdSchema = z.object({
  listId: z.string().min(1, 'List ID is required'),
})

export const pathPlanIdSchema = z.object({
  planId: z.string().min(1, 'Plan ID is required'),
})

export const pathTokenSchema = z.object({
  token: z.string().min(1, 'Token is required'),
})

export const pathSessionIdSchema = z.object({
  sessionId: z.string().min(1, 'Session ID is required'),
})

export const proxyBodySchema = z.record(z.string(), z.unknown())

export const digestPreferencesSchema = z.object({
  weekly_report_enabled: z.boolean().optional(),
  email: z.string().email().optional(),
  frequency: z.string().optional(),
}).passthrough()

export const applySectorQuerySchema = z.object({
  companyId: z.string().min(1, 'companyId is required'),
  sector: z.string().optional(),
})

export const refineSearchQuerySchema = z.object({
  thread_id: z.string().min(1, 'thread_id is required'),
  additional_query: z.string().min(1, 'additional_query is required'),
  limit: z.coerce.number().int().min(1).max(200).optional(),
})

export const vacancyApplyFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  phone: z.string().min(1, 'Phone is required'),
  lgpd_consent: z.string().min(1, 'LGPD consent is required'),
})

export const combineProfilesSchema = z.object({
  profile_ids: z.array(z.string().min(1)).min(2, 'At least 2 profile IDs are required'),
}).passthrough()

export const autocompleteQuerySchema = z.object({
  q: z.string().min(1, 'Query is required'),
  limit: z.coerce.number().int().min(1).max(50).optional(),
})
