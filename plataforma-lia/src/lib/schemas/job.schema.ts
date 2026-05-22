import { z } from 'zod'

export const jobStatusSchema = z.object({
  status: z.enum(['open', 'closed', 'paused', 'draft']).optional(),
  reason: z.string().optional(),
  notes: z.string().optional(),
}).passthrough()

const senioritySchema = z
  .enum(['junior', 'pleno', 'senior', 'lead', 'executive', 'specialist'])
  .or(z.string().regex(/^(junior|pleno|senior|lead|executive|specialist)$/i, 'Invalid seniority'))
  .optional()

export const jobCreateSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  department: z.string().optional(),
  location: z.string().optional(),
  employment_type: z.string().optional(),
  work_model: z.string().optional(),
  manager: z.string().optional(),
  manager_email: z.string().email('Invalid manager email').optional().or(z.literal('')),
  seniority: senioritySchema,
  status: z.string().optional(),
  priority: z.string().optional(),
  salary_min: z.number().nonnegative('Salary must be non-negative').optional(),
  salary_max: z.number().nonnegative('Salary must be non-negative').optional(),
  currency: z.string().regex(/^[A-Za-z]{3}$/, 'Currency must be a 3-letter code').transform(v => v.toUpperCase()).optional(),
  skills: z.array(z.string()).optional(),
  languages: z.array(z.string()).optional(),
  remote: z.boolean().optional(),
  enriched_jd: z.record(z.string(), z.unknown()).nullable().optional(),
}).passthrough().refine(
  (data) => {
    if (data.salary_min != null && data.salary_max != null) {
      return data.salary_min <= data.salary_max
    }
    return true
  },
  { message: 'salary_min must be <= salary_max', path: ['salary_min'] },
)
