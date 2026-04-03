export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import Anthropic from '@anthropic-ai/sdk'
import { z } from 'zod'

const anthropic = new Anthropic({
  apiKey: process.env.AI_INTEGRATIONS_ANTHROPIC_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_ANTHROPIC_BASE_URL
})

const _bodySchema = z.record(z.string(), z.unknown())

const _bodySchema = z.object({
  titles: z.unknown(),
})

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const { titles } = bodyResult.data
    
    if (!titles || !Array.isArray(titles) || titles.length === 0) {
      return NextResponse.json(
        { error: 'Titles array is required' },
        { status: 400 }
      )
    }

    const prompt = `Given these job titles: ${titles.join(', ')}

Generate 8-10 similar or related job titles that a recruiter might also want to search for. Include:
1. Variations with different seniority levels (Junior, Senior, Staff, Principal, Lead, Head of)
2. Related roles in the same domain
3. Alternative naming conventions (e.g., "Software Engineer" vs "Software Developer")

Return ONLY a JSON array of strings with the suggested titles, no explanations.
Example format: ["Senior Software Engineer", "Staff Engineer", "Principal Developer"]`

    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 500,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ]
    })

    const textContent = response.content.find((block: { type: string }) => block.type === 'text')
    if (!textContent || textContent.type !== 'text') {
      return NextResponse.json({ suggestions: [] })
    }

    try {
      const jsonMatch = textContent.text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0])
        const filteredSuggestions = suggestions.filter(
          (s: string) => !titles.includes(s) && typeof s === 'string'
        )
        return NextResponse.json({ suggestions: filteredSuggestions.slice(0, 10) })
      }
    } catch (parseError) {
    }

    return NextResponse.json({ suggestions: [] })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to generate suggestions' },
      { status: 500 }
    )
  }
}
