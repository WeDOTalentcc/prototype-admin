export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { callLLMBackend } from '@/lib/api/llm-backend'

const _bodySchema = z.record(z.string(), z.unknown())


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

    const text = await callLLMBackend({ prompt, maxTokens: 500 })

    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
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
