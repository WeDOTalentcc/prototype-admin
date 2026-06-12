// src/lib/surface-config.ts
// REGRA: toda tool que pode retornar dados estruturados para o chat
// DEVE ter uma entrada neste arquivo. Tools desconhecidas renderizam
// como texto puro (fallback seguro mas sem UX rica).
// INVARIANT: hitl:true → default_surface:'inline' (sensor em surface-config.test.ts).

export type SurfaceConfig = {
  default_surface: 'inline' | 'panel'
  fallback_surface: 'inline-card' | 'inline-notification' | 'inline-hitl'
  can_show_both: boolean
  hitl: boolean
  density_threshold?: number  // itens acima deste número → panel; abaixo → inline
}

export const SURFACE_CONFIG: Record<string, SurfaceConfig> = {
  // ── Dados densos → painel ──────────────────────────────────────────────
  search_candidates: {
    default_surface: 'panel',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
    density_threshold: 3,
  },
  get_candidate_profile: {
    default_surface: 'panel',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
  },
  get_job_details: {
    default_surface: 'panel',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
  },
  get_wsi_questions: {
    default_surface: 'panel',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
  },
  get_calibration: {
    default_surface: 'panel',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
  },
  list_jobs: {
    default_surface: 'inline',
    fallback_surface: 'inline-card',
    can_show_both: true,
    hitl: false,
    density_threshold: 5,
  },

  // ── HITL → inline obrigatório (aprovações nunca ficam no painel) ───────
  send_email: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  send_whatsapp: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  reject_candidate: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  bulk_update_stage: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  approve_job: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  close_job: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },
  publish_job: {
    default_surface: 'inline',
    fallback_surface: 'inline-hitl',
    can_show_both: false,
    hitl: true,
  },

  // ── Ações instantâneas → inline-notification ──────────────────────────
  navigate_page: {
    default_surface: 'inline',
    fallback_surface: 'inline-notification',
    can_show_both: false,
    hitl: false,
  },
  open_ui: {
    default_surface: 'inline',
    fallback_surface: 'inline-notification',
    can_show_both: false,
    hitl: false,
  },
} as const
