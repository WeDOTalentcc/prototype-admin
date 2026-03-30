import { z } from 'zod'

export const webhookPayloadSchema = z.object({
  event: z.string().min(1),
  data: z.record(z.unknown()),
  timestamp: z.string().optional(),
})
