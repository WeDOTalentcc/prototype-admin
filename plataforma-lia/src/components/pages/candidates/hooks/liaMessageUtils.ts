/**
 * Utility functions for classifying LIA chat messages.
 * Extracted from useCandidatesLIAHandlers to keep that file under 1000 lines.
 */

/** Returns true if the message is a conversational greeting/farewell, not a candidate search. */
export function isConversationalMessage(text: string): boolean {
  const normalizedText = text.toLowerCase().trim()

  const greetings = [
    /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite|tudo bem|tudo certo|beleza)[\s!.,?]*$/,
    /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite)\s+(lia|tudo|como)/,
    /^(obrigad[oa]|valeu|thanks|vlw|brigad[oa])[\s!.,?]*$/,
    /^(tchau|até mais|ate mais|bye|flw|falou)[\s!.,?]*$/,
  ]

  return greetings.some(pattern => pattern.test(normalizedText))
}

/** Returns true if the message is a generic question (not a candidate search query). */
export function isGenericQuestion(text: string): boolean {
  const normalizedText = text.toLowerCase().trim()

  const questionPatterns = [
    /^(o que|que tipo|qual|quais|como|por que|quando|onde|quem|quanto|quantos)\s/,
    /^(me explica|explique|pode explicar|poderia explicar)/,
    /^(me ajuda|ajuda|help|pode ajudar|poderia ajudar)/,
    /^(o que você|voce pode|você consegue|vc pode)/,
    /\?$/,
  ]

  const searchKeywords = [
    "desenvolvedor", "developer", "programador", "engenheiro", "analista",
    "gerente", "manager", "coordenador", "diretor", "especialista",
    "junior", "pleno", "sênior", "senior", "trainee", "estagiário",
    "python", "java", "javascript", "react", "node", "angular", "vue",
    "backend", "frontend", "fullstack", "devops", "data", "machine learning",
    "são paulo", "rio de janeiro", "belo horizonte", "remoto", "híbrido",
    "anos de experiência", "experiência em", "conhecimento em",
    "product manager", "product owner", "scrum master", "ux", "ui",
    "designer", "marketing", "vendas", "sales", "rh", "recursos humanos",
    "b2b", "saas", "fintech", "startup",
  ]

  const hasSearchKeywords = searchKeywords.some(keyword =>
    normalizedText.includes(keyword.toLowerCase())
  )

  const isQuestion = questionPatterns.some(pattern => pattern.test(normalizedText))

  return isQuestion && !hasSearchKeywords
}
