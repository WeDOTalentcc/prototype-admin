"use client"

import { SelectGroup, SelectItem, SelectLabel } from '@/components/ui/select'

export interface SubStatusOptionWithCategory {
  code: string
  display_name: string
  category?: string
}

const CATEGORY_LABELS: Record<string, string> = {
  business_decision: 'Decisão de negócio',
  qualification: 'Qualificação',
  cultural: 'Fit cultural',
  logistics: 'Logística',
  compensation: 'Remuneração',
  process: 'Processo',
}

const CATEGORY_ORDER: string[] = [
  'business_decision',
  'qualification',
  'cultural',
  'logistics',
  'compensation',
  'process',
]

const OTHER_LABEL = 'Outros'

export function groupOptionsByCategory(
  options: SubStatusOptionWithCategory[]
): Array<{ key: string; label: string; items: SubStatusOptionWithCategory[] }> {
  const buckets = new Map<string, SubStatusOptionWithCategory[]>()
  for (const opt of options) {
    const key = opt.category && CATEGORY_LABELS[opt.category] ? opt.category : '__other__'
    const arr = buckets.get(key) ?? []
    arr.push(opt)
    buckets.set(key, arr)
  }

  const groups: Array<{ key: string; label: string; items: SubStatusOptionWithCategory[] }> = []
  for (const key of CATEGORY_ORDER) {
    const items = buckets.get(key)
    if (items && items.length > 0) {
      groups.push({ key, label: CATEGORY_LABELS[key], items })
    }
  }
  // Append unrecognized/other categories last (only if non-empty).
  for (const [key, items] of buckets.entries()) {
    if (CATEGORY_ORDER.includes(key)) continue
    if (!items || items.length === 0) continue
    const label = key === '__other__' ? OTHER_LABEL : (CATEGORY_LABELS[key] ?? key)
    groups.push({ key, label, items })
  }
  return groups
}

/**
 * Returns true when at least one option carries a recognized category — the
 * signal that the dropdown should render with category headings (used for the
 * `rejected` stage). When no option has a category (e.g. `offer_declined`),
 * the caller renders a flat list as before.
 */
export function shouldGroupByCategory(options: SubStatusOptionWithCategory[]): boolean {
  return options.some((o) => !!o.category && !!CATEGORY_LABELS[o.category])
}

/**
 * Renders SelectItems for the rejection dropdown. When any option has a
 * known category, items are wrapped in <SelectGroup> with localized
 * <SelectLabel> headings; otherwise renders a plain flat list.
 *
 * `itemClassName` is forwarded to each <SelectItem> so callers can keep
 * their existing typography (e.g. text-xs).
 */
export function renderSubStatusOptions(
  options: SubStatusOptionWithCategory[],
  itemClassName?: string,
) {
  if (!shouldGroupByCategory(options)) {
    return options.map((opt) => (
      <SelectItem key={opt.code} value={opt.code} className={itemClassName}>
        {opt.display_name}
      </SelectItem>
    ))
  }

  const groups = groupOptionsByCategory(options)
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
