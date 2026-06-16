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
    const { skills } = bodyResult.data
    
    if (!skills || !Array.isArray(skills) || skills.length === 0) {
      return NextResponse.json(
        { error: 'Skills array is required' },
        { status: 400 }
      )
    }

    const prompt = `Given these technical skills/competencies: ${skills.join(', ')}

Generate 8-10 similar or related technical skills that a recruiter might also want to search for when looking for candidates. Include:
1. Related technologies in the same ecosystem (e.g., if React, suggest Next.js, Redux, etc.)
2. Complementary skills commonly found together
3. Alternative or competing technologies (e.g., if React, suggest Vue.js, Angular)
4. Higher/lower level abstractions of the same skill

Focus on practical, job-market relevant skills. Return ONLY a JSON array of strings with the suggested skills, no explanations.
Example format: ["Docker", "Kubernetes", "CI/CD", "Jenkins", "GitHub Actions"]`

    const text = await callLLMBackend({ prompt, maxTokens: 500 })

    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0])
        const filteredSuggestions = suggestions.filter(
          (s: string) => !skills.includes(s) && typeof s === 'string'
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
