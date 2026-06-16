"use client"

import { useMemo } from "react"
import { useTranslations } from "next-intl"
import {
  CANONICAL_CATEGORY_KEYS,
  defaultCategoryLabelsPtBR,
  type CategoryLabelMap,
} from "./rejection-categories"

/**
 * Builds the i18n-driven label map consumed by `renderSubStatusOptions`.
 *
 * Reads from `kanban.rejectionCategories.*` keys (added by task #983 follow-up
 * to task #939). Falls back to the canonical PT-BR defaults if a key is
 * missing, so a missing translation never crashes the dropdown.
 *
 * Lives in its own file so the pure helper (`rejection-categories.tsx`)
 * stays free of next-intl / hook dependencies — keeping unit tests trivial.
 */
export function useRejectionCategoryLabels(): CategoryLabelMap {
  const t = useTranslations("kanban.rejectionCategories")

  return useMemo<CategoryLabelMap>(() => {
    const safe = (key: string, fallback: string): string => {
      try {
        const value = t(key)
        // next-intl returns the key itself when the message is missing in dev;
        // detect that and fall back to the canonical default.
        return value && value !== key ? value : fallback
      } catch {
        return fallback
      }
    }

    const map: CategoryLabelMap = { ...defaultCategoryLabelsPtBR }
    for (const key of CANONICAL_CATEGORY_KEYS) {
      map[key] = safe(key, defaultCategoryLabelsPtBR[key])
    }
    map.__other__ = safe("other", defaultCategoryLabelsPtBR.__other__)
    return map
  }, [t])
}
