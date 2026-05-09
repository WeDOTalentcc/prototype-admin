// R-020 P0-B: restored empty constants file with required exports

export interface CandidateStatusConfig {
  label: string
  bg: string
  text: string
  border: string
}

export const CANDIDATE_STATUS_CONFIG: Record<string, CandidateStatusConfig> = {
  active: {
    label: 'Ativo',
    bg: 'bg-status-success/10',
    text: 'text-status-success',
    border: 'border-status-success/30',
  },
  inactive: {
    label: 'Inativo',
    bg: 'bg-lia-bg-tertiary',
    text: 'text-lia-text-secondary',
    border: 'border-lia-border-subtle',
  },
  blacklisted: {
    label: 'LCNU',
    bg: 'bg-status-error/10',
    text: 'text-status-error',
    border: 'border-status-error/30',
  },
  hidden: {
    label: 'Oculto',
    bg: 'bg-lia-bg-tertiary',
    text: 'text-lia-text-tertiary',
    border: 'border-lia-border-subtle',
  },
}
