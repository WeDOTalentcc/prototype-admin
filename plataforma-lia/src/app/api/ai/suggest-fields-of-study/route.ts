export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { z } from 'zod'

const anthropic = new Anthropic({
  apiKey: process.env.AI_INTEGRATIONS_ANTHROPIC_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_ANTHROPIC_BASE_URL
})

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const { query, existingFields } = await request.json()
    
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
