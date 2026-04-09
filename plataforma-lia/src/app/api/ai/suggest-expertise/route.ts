export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { callLLMBackend } from '@/lib/api/llm-backend'

const _bodySchema = z.record(z.string(), z.unknown())


export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const query = bodyResult.data.query as unknown
    const existing = bodyResult.data.existing as string[] | undefined
    const findSimilar = bodyResult.data.findSimilar as unknown

    if (!query || typeof query !== 'string') {
      return NextResponse.json(
        { error: "Query is required" },
        { status: 400 }
      )
    }

    const existingList = (existing ?? []).length > 0 
      ? `\n\nAlready selected (DO NOT include these): ${(existing ?? []).join(', ')}`
      : ''

    const prompt = findSimilar
      ? `Based on these areas of expertise: "${query}", suggest 6 related or complementary expertise areas that would commonly appear together on LinkedIn profiles.${existingList}

Return ONLY a JSON array of strings with the expertise names. Example: ["Machine Learning", "Deep Learning", "NLP"]

Focus on professional expertise areas like:
- Technical domains (Machine Learning, Cloud Architecture, Data Engineering)
- Business functions (Product Management, Growth Marketing, Sales Strategy)
- Industry specializations (FinTech, HealthTech, SaaS)
- Methodologies (Agile, DevOps, Lean Startup)`
      : `Suggest 5 professional expertise areas related to "${query}" that would typically appear on LinkedIn profiles.${existingList}

Return ONLY a JSON array of strings with the expertise names. Example: ["Machine Learning", "Deep Learning", "NLP"]

Focus on professional expertise areas like:
- Technical domains (Machine Learning, Cloud Architecture, Data Engineering)
- Business functions (Product Management, Growth Marketing, Sales Strategy)
- Industry specializations (FinTech, HealthTech, SaaS)
- Methodologies (Agile, DevOps, Lean Startup)`

    const text = await callLLMBackend({ prompt, maxTokens: 256 })
    const trimmed = text.trim()
    const jsonMatch = trimmed.match(/\[[\s\S]*\]/)
    
    if (jsonMatch) {
      try {
        const suggestions = JSON.parse(jsonMatch[0])
        if (Array.isArray(suggestions)) {
          const filtered = suggestions
            .filter((s: unknown): s is string => 
              typeof s === 'string' && 
              s.length > 0 && 
              !(existing ?? []).map((e: string) => e.toLowerCase()).includes(s.toLowerCase())
            )
            .slice(0, findSimilar ? 6 : 5)
          
          return NextResponse.json({ suggestions: filtered })
        }
      } catch {
      }
    }

    return NextResponse.json({ suggestions: [] })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to get suggestions" },
      { status: 500 }
    )
  }
}
