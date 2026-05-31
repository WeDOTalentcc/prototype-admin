"use client"

import { useQuery } from "@tanstack/react-query"

/**
 * Valida email/telefone dos candidatos visiveis (Peca B.2 + Peca C).
 * Email = sintaxe + MX; telefone = E.164. Permite badge "verificado / nao
 * verificado" na tabela, para nao enganar o recrutador com candidatos que
 * nunca vao receber email/WhatsApp.
 *
 * Best-effort: se o endpoint falhar, retorna mapa vazio (sem badge, sem ruido).
 */
export interface ContactValidity {
  candidate_id: string
  email_valid?: boolean | null
  email_reason?: string | null
  phone_valid?: boolean | null
  phone_e164?: string | null
}

export interface ContactToValidate {
  candidate_id: string
  email?: string | null
  phone?: string | null
}

export type ContactValidityMap = Record<string, ContactValidity>

export function useContactValidation(contacts: ContactToValidate[]): {
  validity: ContactValidityMap
  isLoading: boolean
} {
  // Chave estavel: ordena por id + inclui email/phone (revalida se o contato mudar)
  const stableKey = contacts
    .map((c) => `${c.candidate_id}:${c.email || ""}:${c.phone || ""}`)
    .sort()

  const { data, isLoading } = useQuery({
    queryKey: ["contact-validation", stableKey],
    enabled: contacts.length > 0,
    staleTime: 30 * 60 * 1000, // validade e estavel; 30min
    gcTime: 60 * 60 * 1000,
    queryFn: async (): Promise<ContactValidityMap> => {
      const res = await fetch("/api/backend-proxy/search/validate-contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contacts }),
      })
      if (!res.ok) return {}
      const json = await res.json()
      const map: ContactValidityMap = {}
      for (const r of json?.results || []) {
        if (r?.candidate_id) map[r.candidate_id] = r
      }
      return map
    },
  })

  return { validity: data || {}, isLoading }
}
