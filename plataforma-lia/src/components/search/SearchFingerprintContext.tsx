"use client"

import { createContext, useContext } from "react"

/**
 * Fase 2 — fingerprint da busca corrente (hash dos criterios: query + filtros).
 *
 * Ancora o feedback (like/dislike) ao CONJUNTO DE CRITERIOS da busca, nao a uma
 * vaga nem ao recrutador. O SearchFeedbackButtons (renderizado em multiplos
 * caminhos) consome via useSearchFingerprint() e envia no POST, evitando
 * prop-drilling por varias camadas. Provider fica na view de resultados.
 */
const SearchFingerprintContext = createContext<string | undefined>(undefined)

export function SearchFingerprintProvider({
  value,
  children,
}: {
  value: string | undefined
  children: React.ReactNode
}) {
  return (
    <SearchFingerprintContext.Provider value={value}>
      {children}
    </SearchFingerprintContext.Provider>
  )
}

export function useSearchFingerprint(): string | undefined {
  return useContext(SearchFingerprintContext)
}
