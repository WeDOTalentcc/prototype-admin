import { z } from 'zod'

export const jobStatusSchema = z.object({
  status: z.enum(['open', 'closed', 'paused', 'draft']).optional(),
  reason: z.string().optional(),
  notes: z.string().optional(),
}).passthrough()

export const jobCreateSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  department: z.string().optional(),
  location: z.string().optional(),
  employment_type: z.string().optional(),
  seniority: z.string().optional(),
  salary_min: z.number().optional(),
  salary_max: z.number().optional(),
  currency: z.string().optional(),
  skills: z.array(z.string()).optional(),
  languages: z.array(z.string()).optional(),
  remote: z.boolean().optional(),
}).passthrough()
