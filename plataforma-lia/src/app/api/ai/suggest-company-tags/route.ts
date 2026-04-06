export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: process.env.AI_INTEGRATIONS_ANTHROPIC_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_ANTHROPIC_BASE_URL
})

const _bodySchema = z.record(z.string(), z.unknown())


export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const query = bodyResult.data.query as string | undefined
    const existingTags = bodyResult.data.existingTags as string[] | undefined
    
    if (!query || typeof query !== 'string' || query.trim().length < 2) {
      return NextResponse.json(
        { error: 'Query must be at least 2 characters' },
        { status: 400 }
      )
    }

    const existingTagsList = existingTags?.join(', ') || 'none'

    const prompt = `Given this search query for company tags/specializations: "${query}"

Generate 6-10 related company tags, technologies, or industry focus areas that a recruiter might use to find candidates from companies in specific niches.

Consider:
1. Direct matches - technologies/specializations that match the query
2. Related technologies - complementary or competing technologies
3. Industry verticals - related industry focus areas (FinTech, HealthTech, EdTech, etc.)
4. Business models - SaaS, B2B, B2C, Marketplace, etc.
5. Emerging trends - AI, Blockchain, IoT, Clean Energy, etc.

Existing tags to EXCLUDE: ${existingTagsList}

Return ONLY a JSON array of objects with "name" and "highConfidence" fields.
- Set "highConfidence": true for tags that are direct matches or very closely related
- Set "highConfidence": false for broader or loosely related suggestions

Example format: [{"name": "Machine Learning", "highConfidence": true}, {"name": "Data Science", "highConfidence": true}, {"name": "AI", "highConfidence": false}]

Focus on practical, job-market relevant tags that recruiters would use to filter companies.`

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
        const existingLower = (existingTags || []).map((t: string) => t.toLowerCase())
        
        const filteredSuggestions = suggestions
          .filter((s: { name: string }) => 
            typeof s.name === 'string' && 
            !existingLower.includes(s.name.toLowerCase())
          )
          .slice(0, 10)
          .map((s: { name: string; highConfidence?: boolean }) => ({
            name: s.name,
            highConfidence: s.highConfidence === true
          }))
        
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
