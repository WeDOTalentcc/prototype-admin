/**
 * Wrapper unificado de toast — usa Sonner como implementação padrão.
 *
 * Contexto: O projeto possui dois sistemas de toast em uso simultâneo:
 *   1. Radix Toast via useToast() — sistema dominante, ~73 usos em componentes/modals
 *   2. Sonner (toast direto) — ~52 usos, adotado mais recentemente
 *
 * Decisão: manter Radix Toast como legado nos arquivos existentes e usar este
 * wrapper baseado em Sonner para todos os novos componentes. Migração gradual.
 *
 * TODO (BCK-25): Migrar chamadas useToast() legadas para este wrapper, arquivo a arquivo,
 * priorizando: src/components/modals/, src/components/pages/candidates/
 *
 * @see src/hooks/use-toast.ts — implementação Radix Toast (legada)
 * @see src/components/ui/toaster.tsx — provider Radix Toast
 */
import { toast as sonnerToast } from "sonner"

export const toast = {
  success: (message: string, description?: string) =>
    sonnerToast.success(message, { description }),
  error: (message: string, description?: string) =>
    sonnerToast.error(message, { description }),
  info: (message: string, description?: string) =>
    sonnerToast.info(message, { description }),
  warning: (message: string, description?: string) =>
    sonnerToast.warning(message, { description }),
  loading: (message: string) =>
    sonnerToast.loading(message),
  dismiss: (id?: string | number) =>
    sonnerToast.dismiss(id),
}

export type { ExternalToast } from "sonner"
