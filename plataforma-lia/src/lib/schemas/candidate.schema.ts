import { z } from 'zod'
import { bulkIdsSchema } from './common.schema'

const VALID_STAGES = [
  'sourcing', 'screening', 'long_list', 'short_list',
  'interview_hr', 'technical_test', 'english_test',
  'interview_technical', 'interview_manager', 'interview_manager2',
  'interview_final', 'references', 'offer', 'hired',
  'rejected', 'offer_declined', 'standby',
] as const

export const candidateStageSchema = z.object({
  stage: z.enum(VALID_STAGES),
  sub_status: z.string().optional(),
  job_vacancy_id: z.union([z.string(), z.number()]).optional(),
})

export const candidateDecisionSchema = z.object({
  decision: z.enum(['approved', 'rejected']),
  notes: z.string().optional(),
  reason: z.string().optional(),
}).passthrough()

export const candidateFeedbackSchema = z.object({
  rating: z.number().int().min(1).max(5).optional(),
  notes: z.string().optional(),
  recommendation: z.string().optional(),
}).passthrough()

export const bulkUpdateStatusSchema = bulkIdsSchema.extend({
  stage: z.enum(VALID_STAGES).optional(),
  sub_status: z.string().optional(),
  status: z.string().optional(),
})

export const bulkAssignJobSchema = bulkIdsSchema
  .extend({
    job_vacancy_id: z.union([z.string(), z.number()]).optional(),
    job_id: z.union([z.string(), z.number()]).optional(),
    notes: z.string().optional(),
    analyze_match: z.boolean().optional(),
    use_pearch: z.boolean().optional(),
    use_gemini: z.boolean().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.job_vacancy_id == null && data.job_id == null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'job_vacancy_id or job_id is required',
        path: ['job_vacancy_id'],
      })
    }
  })

export const bulkStartScreeningSchema = bulkIdsSchema
  .extend({
    job_vacancy_id: z.union([z.string(), z.number()]).optional(),
    job_id: z.union([z.string(), z.number()]).optional(),
    screening_type: z.string().optional().default('text'),
    use_pearch: z.boolean().optional(),
    use_gemini: z.boolean().optional(),
    user_instructions: z.string().optional(),
    override_saturation: z.boolean().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.job_vacancy_id == null && data.job_id == null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'job_vacancy_id is required to start screening',
        path: ['job_vacancy_id'],
      })
    }
  })

export const bulkSendEmailSchema = bulkIdsSchema.extend({
  template_id: z.union([z.string(), z.number()]),
  custom_variables: z.record(z.string(), z.unknown()).optional(),
  custom_data: z.record(z.string(), z.unknown()).optional(),
})

export const bulkDeleteSchema = bulkIdsSchema.extend({
  permanent: z.boolean().optional().default(false),
  hard_delete: z.boolean().optional(),
}).transform((data) => ({
  candidate_ids: data.candidate_ids,
  permanent: data.hard_delete ?? data.permanent ?? false,
}))

export const bulkExportSchema = bulkIdsSchema.extend({
  format: z.enum(['csv', 'xlsx']).optional().default('csv'),
}).passthrough()
