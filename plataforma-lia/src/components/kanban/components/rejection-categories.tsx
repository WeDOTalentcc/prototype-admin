"use client"

import { SelectGroup, SelectItem, SelectLabel } from '@/components/ui/select'

export interface SubStatusOptionWithCategory {
  code: string
  display_name: string
  category?: string
}

/**
 * Canonical ordered list of rejection categories. Mirrors the API contract
 * (substatus-options endpoint) and drives the heading order in the dropdown.
 * Exported so tests can sentinel-check the contract and so callers wishing to
 * build their own label maps know the canonical key set.
 */
export const CANONICAL_CATEGORY_KEYS = [
  'business_decision',
  'qualification',
  'cultural',
  'logistics',
  'compensation',
  'process',
] as const

export type CanonicalCategoryKey = (typeof CANONICAL_CATEGORY_KEYS)[number]

/**
 * Synthetic bucket key for options whose `category` is missing or unknown.
 * Kept as a constant so callers / tests don't repeat the magic string.
 */
export const OTHER_CATEGORY_KEY = '__other__'

/**
 * Map of canonical keys → label. Includes the `__other__` synthetic bucket.
 *
 * Default labels are PT-BR fallbacks — used when the caller doesn't pass an
 * i18n-driven map. Callers in the app should always pass `categoryLabels`
 * derived from `useTranslations` (see UniversalTransitionModal +
 * TransitionActionSection callsites). The fallback exists so the helper
 * remains pure (no React/i18n dependency) and so unit tests can run without
 * a NextIntlClientProvider.
 *
 * Migration of these labels to the i18n catalog is task #983.
 */
export type CategoryLabelMap = Record<CanonicalCategoryKey | typeof OTHER_CATEGORY_KEY, string>

export const defaultCategoryLabelsPtBR: CategoryLabelMap = {
  business_decision: 'Decisão de negócio',
  qualification: 'Qualificação',
  cultural: 'Fit cultural',
  logistics: 'Logística',
  compensation: 'Remuneração',
  process: 'Processo',
  __other__: 'Outros',
}

function isCanonicalKey(key: string): key is CanonicalCategoryKey {
  return (CANONICAL_CATEGORY_KEYS as readonly string[]).includes(key)
}

export function groupOptionsByCategory(
  options: SubStatusOptionWithCategory[],
  labels: CategoryLabelMap = defaultCategoryLabelsPtBR,
): Array<{ key: string; label: string; items: SubStatusOptionWithCategory[] }> {
  const buckets = new Map<string, SubStatusOptionWithCategory[]>()
  for (const opt of options) {
    const key = opt.category && isCanonicalKey(opt.category) ? opt.category : OTHER_CATEGORY_KEY
    const arr = buckets.get(key) ?? []
    arr.push(opt)
    buckets.set(key, arr)
  }

  const groups: Array<{ key: string; label: string; items: SubStatusOptionWithCategory[] }> = []
  for (const key of CANONICAL_CATEGORY_KEYS) {
    const items = buckets.get(key)
    if (items && items.length > 0) {
      groups.push({ key, label: labels[key], items })
    }
  }
  // Append the __other__ bucket last when non-empty.
  const otherItems = buckets.get(OTHER_CATEGORY_KEY)
  if (otherItems && otherItems.length > 0) {
    groups.push({ key: OTHER_CATEGORY_KEY, label: labels.__other__, items: otherItems })
  }
  return groups
}

/**
 * Returns true when at least one option carries a recognized canonical
 * category — the signal that the dropdown should render with category
 * headings (used for the `rejected` stage). When no option has a recognized
 * category (e.g. `offer_declined`, or only unknown categories present), the
 * caller renders a flat list as before — preserving legacy behavior.
 */
export function shouldGroupByCategory(options: SubStatusOptionWithCategory[]): boolean {
  return options.some((o) => !!o.category && isCanonicalKey(o.category))
}

/**
 * Renders SelectItems for the rejection dropdown. When any option has a
 * known category, items are wrapped in <SelectGroup> with localized
 * <SelectLabel> headings; otherwise renders a plain flat list.
 *
 * `itemClassName` is forwarded to each <SelectItem> so callers can keep
 * their existing typography (e.g. text-xs).
 *
 * `categoryLabels` lets the caller supply i18n-driven heading labels.
 * Defaults to `defaultCategoryLabelsPtBR` for backward compatibility and
 * to keep the helper pure (no hook dependency in tests).
 */
export function renderSubStatusOptions(
  options: SubStatusOptionWithCategory[],
  itemClassName?: string,
  categoryLabels: CategoryLabelMap = defaultCategoryLabelsPtBR,
) {
  if (!shouldGroupByCategory(options)) {
    return options.map((opt) => (
      <SelectItem key={opt.code} value={opt.code} className={itemClassName}>
        {opt.display_name}
      </SelectItem>
    ))
  }

  const groups = groupOptionsByCategory(options, categoryLabels)
  return groups.map((group) => (
    <SelectGroup key={group.key}>
      <SelectLabel className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider">
        {group.label}
      </SelectLabel>
      {group.items.map((opt) => (
        <SelectItem key={opt.code} value={opt.code} className={itemClassName}>
          {opt.display_name}
        </SelectItem>
      ))}
    </SelectGroup>
  ))
}
