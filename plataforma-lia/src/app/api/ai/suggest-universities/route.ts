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
    const universities = bodyResult.data.universities as string[] | undefined
    const existingUniversities = bodyResult.data.existingUniversities as string[] | undefined
    
    const searchTerm = query || ''
    const basedOnUniversities = universities || []
    
    if (!searchTerm && basedOnUniversities.length === 0) {
      return NextResponse.json(
        { error: 'Either query or universities array is required' },
        { status: 400 }
      )
    }

    const existingList = existingUniversities?.join(', ') || 'none'
    
    let prompt: string
    
    if (basedOnUniversities.length > 0) {
      prompt = `Given these universities: ${basedOnUniversities.join(', ')}

Find 6-10 similar universities that a recruiter might use to find candidates with similar educational backgrounds.

Consider:
1. Universities with similar academic reputation/ranking tier
2. Universities in similar geographic regions
3. Universities with similar specializations or strengths
4. Universities that share similar recruiting pipelines

Existing universities to EXCLUDE: ${existingList}

Return ONLY a JSON array of university name strings.
Example format: ["Harvard University", "Stanford University", "MIT", "Yale University"]

Focus on well-known, recognized university names. Include the full official name.`
    } else {
      prompt = `Given this search query for universities: "${searchTerm}"

Generate 6-10 related universities that a recruiter might use to find candidates from specific educational institutions.

Consider:
1. Direct matches - universities that match the query directly
2. Related universities - universities with similar characteristics
3. Regional matches - if searching for a location, include top universities from that region
4. Specialty matches - if searching for a field, include universities known for that field

Examples of recognized universities by category:
- US Ivy League: Harvard, Yale, Princeton, Columbia, Brown, Cornell, Dartmouth, UPenn
- US Top Tech: MIT, Stanford, Caltech, Carnegie Mellon, Georgia Tech
- UK Top: Oxford, Cambridge, Imperial College London, LSE, UCL
- Brazil Top: USP, Unicamp, UFRJ, FGV, PUC-Rio, Insper, ITA
- Europe Top: ETH Zurich, EPFL, TU Munich, Sorbonne, Sciences Po
- Asia Top: Tsinghua, Peking, NUS, NTU, Tokyo, Kyoto, KAIST, Seoul National

Existing universities to EXCLUDE: ${existingList}

Return ONLY a JSON array of university name strings.
Example format: ["Harvard University", "Stanford University", "MIT", "Yale University"]

Focus on well-known, recognized university names. Include the full official name.`
    }

    const text = await callLLMBackend({ prompt, maxTokens: 500 })

    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0])
        const existingLower = (existingUniversities || []).map((u: string) => u.toLowerCase())
        
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
