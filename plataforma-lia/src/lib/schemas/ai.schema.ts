import { z } from 'zod'

export const aiChatSchema = z.object({
  message: z.string().min(1).max(10000),
  conversationId: z.string().optional(),
  context: z.record(z.string(), z.unknown()).optional(),
  model: z.string().optional(),
})

export const aiAnalyzeSchema = z.object({
  content: z.string().min(1),
  type: z.enum(['resume', 'job', 'candidate', 'text']).optional(),
  options: z.record(z.string(), z.unknown()).optional(),
})

export const aiGenerateSchema = z.object({
  prompt: z.string().min(1).max(5000),
  type: z.string().optional(),
  context: z.record(z.string(), z.unknown()).optional(),
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().int().min(1).max(4000).optional(),
})
