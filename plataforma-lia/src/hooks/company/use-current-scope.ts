/**
 * useCurrentScope — Deriva o PromptScope automaticamente a partir da URL.
 *
 * Mapeia a rota atual para um dos 4 escopos de acesso a ferramentas do backend:
 *   - TALENT_FUNNEL: páginas de candidatos/funil (/funil, /funil-de-talentos)
 *   - JOB_TABLE:     listagem de vagas sem ID específico (/jobs)
 *   - IN_JOB:        dentro de uma vaga específica (/jobs/[id]/...)
 *   - GLOBAL:        qualquer outra rota
 *
 * Compatível com Vue/Nuxt: lógica de mapeamento em função pura exportada
 * separadamente para facilitar migração para composable useCurrentScope().
 *
 * @example
 *   const { scope, scopeName } = useCurrentScope()
 *   // Em handleSend: wsSend(text, { scope }, domain)
 */

"use client"

import { usePathname } from "next/navigation"
import { useMemo } from "react"

/** Valores de escopo espelhando o backend PromptScope enum. */
export type PromptScope = "talent_funnel" | "job_table" | "in_job" | "global"

export interface CurrentScope {
  /** Valor canônico a enviar ao backend (context.scope) */
  scope: PromptScope
  /** Label PT-BR para exibição/debug */
  scopeName: string
}

/**
 * Mapeia um pathname para o PromptScope correspondente.
 * Função pura — facilita testes unitários e migração Vue.
 */
export function resolveScopeFromPathname(pathname: string): PromptScope {
  if (!pathname) return "global"

  // Funil de talentos / candidatos
  if (pathname.startsWith("/funil-de-talentos")) {
    return "talent_funnel"
  }

  // Dentro de uma vaga específica (/jobs/[id] ou /jobs/[id]/...)
  const inJobMatch = /^\/jobs\/[^/]+/.test(pathname)
  if (inJobMatch) {
    return "in_job"
  }

  // Listagem de vagas (apenas /jobs ou /jobs/)
  if (pathname === "/jobs" || pathname === "/jobs/") {
    return "job_table"
  }

  return "global"
}

const SCOPE_LABELS: Record<PromptScope, string> = {
  talent_funnel: "Funil de Talentos",
  job_table: "Vagas",
  in_job: "Vaga Específica",
  global: "Global",
}

/**
 * Hook: retorna o escopo atual derivado da URL.
 * Recalcula apenas quando o pathname muda (useMemo).
 */
export function useCurrentScope(): CurrentScope {
  const pathname = usePathname()

  return useMemo(() => {
    const scope = resolveScopeFromPathname(pathname ?? "")
    return {
      scope,
      scopeName: SCOPE_LABELS[scope],
    }
  }, [pathname])
}
