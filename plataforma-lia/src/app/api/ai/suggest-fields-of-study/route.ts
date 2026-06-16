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
    const query = bodyResult.data.query as string | undefined
    const existingFields = bodyResult.data.existingFields as string[] | undefined
    
    if (!query || typeof query !== 'string' || query.trim().length < 2) {
      return NextResponse.json(
        { error: 'Query must be at least 2 characters' },
        { status: 400 }
      )
    }

    const existingList = existingFields?.join(', ') || 'none'

    const prompt = `Given this search query for fields of study/majors: "${query}"

Generate 6-10 related academic fields of study that a recruiter might use to find candidates who studied specific subjects.

Consider:
1. Direct matches - fields that match the query directly
2. Related disciplines - adjacent or complementary fields
3. Parent/child fields - broader or more specific versions
4. Cross-functional fields - fields that often share career paths

Common academic fields by category:
- STEM: Computer Science, Data Science, Software Engineering, Electrical Engineering, Mechanical Engineering, Civil Engineering, Chemical Engineering, Biomedical Engineering, Mathematics, Physics, Chemistry, Biology
- Business: Business Administration, Finance, Accounting, Marketing, Economics, Management, Entrepreneurship, International Business, Supply Chain Management
- Health: Medicine, Nursing, Pharmacy, Public Health, Biomedical Sciences, Nutrition, Physical Therapy
- Social Sciences: Psychology, Sociology, Political Science, Anthropology, International Relations, Economics
- Arts & Humanities: English, History, Philosophy, Art History, Communications, Journalism, Creative Writing
- Law & Policy: Law, Public Policy, Criminal Justice, Public Administration

Existing fields to EXCLUDE: ${existingList}

Return ONLY a JSON array of field of study strings.
Example format: ["Computer Science", "Data Science", "Software Engineering", "Information Technology"]

Focus on recognized academic field names that universities commonly use.`

    const text = await callLLMBackend({ prompt, maxTokens: 500 })

    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0])
        const existingLower = (existingFields || []).map((f: string) => f.toLowerCase())
        
        const filteredSuggestions = suggestions
          .filter((s: string) => 
            typeof s === 'string' && 
            !existingLower.includes(s.toLowerCase())
          )
          .slice(0, 10)
        
        return NextResponse.json({ suggestions: filteredSuggestions })
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
