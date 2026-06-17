const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export interface LLMCallOptions {
  prompt: string
  system?: string
  maxTokens?: number
}

export async function callLLMBackend(options: LLMCallOptions): Promise<string> {
  const { prompt, system, maxTokens = 1024 } = options

  const response = await fetch(`${BACKEND_URL}/api/v1/internal/llm/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, system, max_tokens: maxTokens }),
  })

  if (!response.ok) {
    throw new Error(`LLM backend error: ${response.status}`)
  }

  const data = await response.json()
  return data.text as string
}
