"use client"

/**
 * usePersonaName — nome white-label do assistente de IA configurado em
 * Configurações › Personalidade da IA (persona per-tenant). Default "LIA".
 *
 * Reaproveita useAiPersona (React Query, cache "company-ai-persona") — chamar em
 * vários componentes dispara 1 fetch só. Use em QUALQUER lugar-chave onde o nome
 * do assistente é exibido ao usuário, em vez de hardcodar "LIA" (white-label).
 */
import { useAiPersona } from "@/hooks/company/use-ai-persona"

export function usePersonaName(): string {
  const { persona } = useAiPersona()
  return persona?.name?.trim() || "LIA"
}

export default usePersonaName
