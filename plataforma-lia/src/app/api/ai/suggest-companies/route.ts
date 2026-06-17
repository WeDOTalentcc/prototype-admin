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
    const companies = bodyResult.data.companies as string[] | undefined
    const query = bodyResult.data.query as string | undefined
    
    if ((!companies || !Array.isArray(companies) || companies.length === 0) && !query) {
      return NextResponse.json(
        { error: 'Companies array or query is required' },
        { status: 400 }
      )
    }

    let prompt: string
    
    if (query) {
      prompt = `Given this search query for companies: "${query}"

The query could be:
1. A company name - return competitors and similar companies in the same industry
2. A description like "energy companies in New York" or "fintech startups in Brazil" - return matching companies
3. A LinkedIn URL - extract the company name and return similar companies

Generate 8-12 relevant company suggestions. For each company, include:
- The company name
- The company's domain (website) if known
- The company's LinkedIn URL if you can construct it

Return ONLY a JSON array with objects containing: name, domain (optional), linkedinUrl (optional).
Example format: [{"name": "Stripe", "domain": "stripe.com", "linkedinUrl": "linkedin.com/company/stripe"}, {"name": "Square", "domain": "squareup.com"}]

Focus on well-known companies that recruiters would search for. Include both global and Brazilian companies when relevant.`
    } else {
      const companyNames = (companies ?? []).map((c: { name: string } | string) => 
        typeof c === 'string' ? c : c.name
      )
      
      prompt = `Given these companies: ${companyNames.join(', ')}

Generate 8-12 similar or related companies that a recruiter might also want to search for. Consider:
1. Direct competitors in the same industry
2. Companies of similar size and stage
3. Companies in adjacent markets
4. Companies known for similar culture or talent

For each company, include:
- The company name
- The company's domain (website) if known

Return ONLY a JSON array with objects containing: name, domain (optional).
Example format: [{"name": "Stripe", "domain": "stripe.com"}, {"name": "Square", "domain": "squareup.com"}]

Focus on well-known companies. Include both global and Brazilian companies when relevant.`
    }

    const text = await callLLMBackend({ prompt, maxTokens: 800 })

    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0])
        const existingNames = companies?.map((c: { name: string } | string) => 
          (typeof c === 'string' ? c : c.name).toLowerCase()
        ) || []
        
        const filteredSuggestions = suggestions.filter(
          (s: { name: string }) => !existingNames.includes(s.name.toLowerCase())
        )
        return NextResponse.json({ suggestions: filteredSuggestions.slice(0, 12) })
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
