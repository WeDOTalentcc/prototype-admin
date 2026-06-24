/**
 * Centralized toast error messages — GAP-11-020
 * Single source of truth for user-facing error strings in toasts.
 * Use instead of inline string literals so messages stay consistent
 * across surfaces that handle the same operation.
 */

export const TOAST_MESSAGES = {
  SAVE_CANDIDATE: {
    VALIDATION: "Dados do candidato inválidos",
    NETWORK: "Conexão perdida ao salvar candidato",
    PERMISSION: "Você não tem permissão para editar este candidato",
    UNKNOWN: "Erro ao salvar candidato",
  },
  SEARCH_CANDIDATES: {
    VALIDATION: "Critério de busca inválido",
    NETWORK: "Erro ao conectar com servidor",
    TIMEOUT: "Busca demorou muito, tente filtros mais específicos",
    UNKNOWN: "Erro ao buscar candidatos",
  },
  UPLOAD_FILE: {
    SIZE: "Arquivo muito grande (máx 10MB)",
    FORMAT: "Formato de arquivo não suportado",
    NETWORK: "Falha ao fazer upload do arquivo",
    UNKNOWN: "Erro ao fazer upload",
  },
  SEND_EMAIL: {
    INVALID: "Email inválido",
    NETWORK: "Falha ao enviar email",
    PERMISSION: "Você não tem permissão para enviar emails",
    UNKNOWN: "Erro ao enviar email",
  },
  CREATE_JOB: {
    VALIDATION: "Dados da vaga incompletos",
    PERMISSION: "Você não tem permissão para criar vagas",
    NETWORK: "Erro ao conectar ao servidor",
    UNKNOWN: "Erro ao criar vaga",
  },
  CREATE_CANDIDATE: {
    VALIDATION: "Dados do candidato incompletos",
    DUPLICATE: "Candidato com este email já existe",
    PERMISSION: "Você não tem permissão para criar candidatos",
    UNKNOWN: "Erro ao criar candidato",
  },
  DELETE: {
    PERMISSION: "Você não tem permissão para deletar",
    NETWORK: "Erro ao conectar com servidor",
    NOT_FOUND: "Item não encontrado",
    UNKNOWN: "Erro ao deletar",
  },
  SCREENING_CONFIG: {
    SAVE_ERROR: "Erro ao salvar configurações",
    UPDATE_SCHEDULING_ERROR: "Erro ao atualizar agendamento",
    UPDATE_SETTINGS_ERROR: "Erro ao atualizar configurações",
    UPDATE_CHANNELS_ERROR: "Erro ao atualizar canais de comunicação",
  },
} as const

export type ToastCategory = keyof typeof TOAST_MESSAGES

/**
 * Returns a specific message with UNKNOWN fallback.
 */
export function getToastMessage(
  category: ToastCategory,
  type: string = "UNKNOWN",
): string {
  const messages = TOAST_MESSAGES[category]
  if (type in messages) {
    return messages[type as keyof typeof messages]
  }
  return (messages as Record<string, string>).UNKNOWN ?? "Algo deu errado"
}
