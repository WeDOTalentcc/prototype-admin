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
    const description = bodyResult.data.description as string | undefined
    
    if (!description || description.length < 10) {
      return NextResponse.json(
        { error: 'Descrição muito curta' },
        { status: 400 }
      )
    }

    const prompt = `Analise a seguinte descrição de perfil profissional e extraia as informações estruturadas para criar um arquétipo de busca de candidatos.

Descrição: "${description}"

Retorne APENAS um JSON válido (sem markdown, sem código) com os seguintes campos:
{
  "name": "Nome curto e descritivo do arquétipo (ex: 'Tech Lead Python', 'PM Sênior Fintech')",
  "query": "Query de busca otimizada baseada na descrição (ex: 'Desenvolvedor Python Sênior AWS Machine Learning')",
  "emoji": "Um emoji apropriado para o cargo (ex: 💻, 📊, 🚀)",
  "skills": ["lista", "de", "skills", "técnicas", "principais"],
  "tags": ["tags", "categorias", "relevantes"],
  "seniority": "junior|pleno|senior|lead|staff|principal|manager|director (apenas um)",
  "industry": "technology|fintech|healthcare|education|ecommerce|logistics|consulting|manufacturing|agritech|other (apenas um)",
  "experience_years_min": número mínimo de anos de experiência sugerido (número inteiro ou null)
}

Extraia informações reais da descrição. Se algum campo não puder ser inferido, use valores vazios ou null.`

    const responseText = await callLLMBackend({ prompt, maxTokens: 1024 })

    let cleanedText = responseText.trim()
    if (cleanedText.startsWith('```json')) {
      cleanedText = cleanedText.slice(7)
    } else if (cleanedText.startsWith('```')) {
      cleanedText = cleanedText.slice(3)
    }
    if (cleanedText.endsWith('```')) {
      cleanedText = cleanedText.slice(0, -3)
    }
    cleanedText = cleanedText.trim()

    const extractedData = JSON.parse(cleanedText)

    return NextResponse.json({
      name: extractedData.name || "Novo Arquétipo",
      query: extractedData.query || description,
      emoji: extractedData.emoji || "🎯",
      skills: Array.isArray(extractedData.skills) ? extractedData.skills.slice(0, 10) : [],
      tags: Array.isArray(extractedData.tags) ? extractedData.tags.slice(0, 5) : [],
      seniority: extractedData.seniority || "",
      industry: extractedData.industry || "",
      experience_years_min: typeof extractedData.experience_years_min === 'number' ? extractedData.experience_years_min : null
    })

  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao extrair informações', details: String(error) },
      { status: 500 }
    )
  }
}
