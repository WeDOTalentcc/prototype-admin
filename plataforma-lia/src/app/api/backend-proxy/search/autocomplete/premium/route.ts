import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const query = searchParams.get("query") || ""
    const companyId = searchParams.get("company_id") || "demo"
    const userId = searchParams.get("user_id") || "default_user"

    if (!query || query.length < 2) {
      return NextResponse.json({ suggestions: [], query })
    }

    try {
      const response = await fetch(
        `${BACKEND_URL}/api/v1/search/autocomplete/premium?` +
          new URLSearchParams({
            query,
            company_id: companyId,
            user_id: userId,
          }),
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        }
      )

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }

    } catch (backendError) {
    }

    const fallbackSuggestions = generateFallbackSuggestions(query)
    return NextResponse.json({
      suggestions: fallbackSuggestions,
      query,
    })
  } catch (error) {
    return NextResponse.json({ suggestions: [], query: "" }, { status: 500 })
  }
}

function generateFallbackSuggestions(query: string) {
  const queryLower = query.toLowerCase()
  const suggestions: Array<{
    text: string
    category: string
    count?: number
  }> = []

  if (queryLower.includes("python") || queryLower.includes("dev")) {
    suggestions.push(
      { text: "Python Developer Sênior São Paulo", category: "popular", count: 15 },
      { text: "Python AWS Data Engineer", category: "team", count: 8 }
    )
  }

  if (queryLower.includes("data") || queryLower.includes("eng")) {
    suggestions.push(
      { text: "Data Engineer Pleno Fintech", category: "popular", count: 12 },
      { text: "Data Scientist Machine Learning", category: "recommended" }
    )
  }

  if (queryLower.includes("front") || queryLower.includes("react")) {
    suggestions.push(
      { text: "Frontend React TypeScript", category: "popular", count: 20 },
      { text: "React Developer Pleno Remoto", category: "team", count: 5 }
    )
  }

  suggestions.push({
    text: query,
    category: "recent",
  })

  return suggestions.slice(0, 8)
}
