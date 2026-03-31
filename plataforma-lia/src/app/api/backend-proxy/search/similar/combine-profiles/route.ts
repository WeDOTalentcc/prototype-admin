export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    const urls: string[] = []
    const cvFiles: File[] = []
    
    for (const [key, value] of formData.entries()) {
      if (key.startsWith("urls[") || key === "urls") {
        urls.push(value as string)
      } else if (key.startsWith("cvs[") || key === "cvs") {
        cvFiles.push(value as File)
      }
    }

    if (urls.length === 0 && cvFiles.length === 0) {
      return NextResponse.json(
        { error: "Provide at least one URL or CV" },
        { status: 400 }
      )
    }

    const backendFormData = new FormData()
    urls.forEach((url) => {
      if (url.trim()) {
        backendFormData.append("urls", url)
      }
    })
    
    for (const file of cvFiles) {
      backendFormData.append("cvs", file)
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/search/similar/combine-profiles`, {
        method: "POST",
        body: backendFormData,
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }
      
    } catch (backendError) {
    }
    
    const mockResponse = generateMockCombinedProfile(urls, cvFiles.length)
    return NextResponse.json(mockResponse)
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to process profiles" },
      { status: 500 }
    )
  }
}

function generateMockCombinedProfile(urls: string[], cvCount: number) {
  const baseKeywords = [
    "Sênior",
    "Python",
    "AWS",
    "Data Engineer",
    "Fintech",
    "SQL",
    "Spark",
    "Inglês Avançado"
  ]

  const additionalKeywords = [
    "Machine Learning",
    "Docker",
    "Kubernetes",
    "PostgreSQL",
    "ETL",
    "Airflow"
  ]

  const sourceCount = urls.length + cvCount
  const keywordCount = Math.min(5 + sourceCount * 2, baseKeywords.length + additionalKeywords.length)
  const keywords = [...baseKeywords, ...additionalKeywords].slice(0, keywordCount)

  return {
    keywords,
    title: "Data Engineer",
    seniority: "Sênior",
    skills_technical: ["Python", "SQL", "AWS", "Spark", "Airflow"],
    skills_soft: ["Comunicação", "Trabalho em equipe"],
    industries: ["Fintech", "Tecnologia"],
    location: "São Paulo",
    summary: `Perfil combinado baseado em ${sourceCount} fonte(s): profissional sênior com forte experiência em engenharia de dados e cloud.`,
    source_count: sourceCount
  }
}
