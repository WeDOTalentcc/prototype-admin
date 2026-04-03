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
  query: z.unknown(),
  existingIndustries: z.unknown(),
})

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const { query, existingIndustries } = bodyResult.data
    
    if (!query || typeof query !== 'string' || query.trim().length < 2) {
      return NextResponse.json(
        { error: 'Query must be at least 2 characters' },
        { status: 400 }
      )
    }

    const existingList = existingIndustries?.join(', ') || 'none'

    const prompt = `Given this search query for industries: "${query}"

Generate 6-10 related industries that a recruiter might use to find candidates who have worked in specific sectors.

Use standard LinkedIn industry categories when possible. Consider:
1. Direct matches - industries that match the query directly
2. Related sectors - adjacent or complementary industries
3. Parent/child industries - broader or more specific versions
4. Cross-functional industries - industries that often share talent

Standard industry examples:
- Technology: Computer Software, Information Technology, Internet, Computer Hardware
- Finance: Banking, Financial Services, Investment Banking, Insurance, Venture Capital
- Healthcare: Hospital & Health Care, Medical Devices, Pharmaceuticals, Biotechnology
- Manufacturing: Automotive, Consumer Electronics, Industrial Automation
- Services: Management Consulting, Professional Training, Staffing and Recruiting

Existing industries to EXCLUDE: ${existingList}

Return ONLY a JSON array of industry name strings.
Example format: ["Computer Software", "Information Technology", "Financial Services", "Banking"]

Focus on practical, recognized industry names that LinkedIn and job platforms use.`

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
        const existingLower = (existingIndustries || []).map((i: string) => i.toLowerCase())
        
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
