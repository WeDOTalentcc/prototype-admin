"use client"

import { useMemo } from "react"

// ─────────────────────────────────────────────────────────────────────────────
// Hook: useWizardStageConstants
// Centralises the stage display-name map and the set of "initial" stages that
// do not represent meaningful draft progress. These values were previously
// inlined as useMemo calls inside useExpandedChatModalCore.
// ─────────────────────────────────────────────────────────────────────────────

export function useWizardStageConstants() {
  // Unified stage name mapping used by draft-detection and effects
  const STAGE_DISPLAY_NAMES: Record<string, string> = useMemo(() => ({
    'assessment': 'Avaliação',
    'input-evaluation': 'Avaliação',
    'jd-enrichment': 'Enriquecimento',
    'salary': 'Remuneração',
    'competencies': 'Competências',
    'wsi-questions': 'Triagem WSI',
    'review': 'Revisão',
    'review-publish': 'Revisão',
    'search': 'Busca',
    'search-calibration': 'Busca',
  }), [])

  // Initial stages that don't count as meaningful draft progress
  const INITIAL_STAGES = useMemo(() => ['assessment', 'input-evaluation'], [])

  return { STAGE_DISPLAY_NAMES, INITIAL_STAGES }
}
