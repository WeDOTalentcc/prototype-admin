import Anthropic from "@anthropic-ai/sdk"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const client = new Anthropic()

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const { query, existing = [], findSimilar = false } = await request.json()

    if (!query || typeof query !== 'string') {
      return NextResponse.json(
        { error: "Query is required" },
        { status: 400 }
      )
    }

    const existingList = existing.length > 0 
      ? `\n\nAlready selected (DO NOT include these): ${existing.join(', ')}`
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

    const response = await client.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 256,
      messages: [{ role: "user", content: prompt }]
    })

    const content = response.content[0]
    if (content.type !== 'text') {
      return NextResponse.json({ suggestions: [] })
    }

    const text = content.text.trim()
    const jsonMatch = text.match(/\[[\s\S]*\]/)
    
    if (jsonMatch) {
      try {
        const suggestions = JSON.parse(jsonMatch[0])
        if (Array.isArray(suggestions)) {
          const filtered = suggestions
            .filter((s: unknown): s is string => 
              typeof s === 'string' && 
              s.length > 0 && 
              !existing.map((e: string) => e.toLowerCase()).includes(s.toLowerCase())
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
