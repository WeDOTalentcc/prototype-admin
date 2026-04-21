import { describe, it, expect } from 'vitest'
import { mergeCompanyBenefits } from '../benefits-merge'
import { INITIAL_BENEFITS } from '../constants'
import type { CompanyBenefit, JobBenefit } from '@/types/benefits'

const cb = (
  overrides: Partial<CompanyBenefit> & { id: string; name: string }
): CompanyBenefit => ({
  description: '',
  category: 'other',
  value_type: 'informative',
  seniority_levels: ['all'],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  ...overrides,
})

describe('mergeCompanyBenefits — Task #765 wizard hydration', () => {
  it('replaces the placeholder INITIAL_BENEFITS list on a fresh wizard', () => {
    const company = [
      cb({ id: 'c1', name: 'VR Premium', is_highlighted: true }),
      cb({ id: 'c2', name: 'Plano Top', is_mandatory: true }),
      cb({ id: 'c3', name: 'Gympass' }),
    ]
    const merged = mergeCompanyBenefits(INITIAL_BENEFITS, company)
    expect(merged.map(b => b.name)).toEqual(['VR Premium', 'Plano Top', 'Gympass'])
    expect(merged[0].enabled).toBe(true)  // highlighted → enabled
    expect(merged[1].enabled).toBe(true)  // mandatory → enabled
    expect(merged[2].enabled).toBe(false) // neither → disabled
  })

  it('preserves user selections when a draft is already loaded', () => {
    const userDraft: JobBenefit[] = [
      { ...cb({ id: 'u1', name: 'VR Premium' }), enabled: true },
      { ...cb({ id: 'u2', name: 'Custom Benefit' }), enabled: true },
    ]
    const company = [
      cb({ id: 'c1', name: 'VR Premium', is_highlighted: true }),
      cb({ id: 'c2', name: 'Plano Top', is_mandatory: true }),
    ]
    const merged = mergeCompanyBenefits(userDraft, company)

    // Existing entries kept verbatim
    const vr = merged.find(b => b.name === 'VR Premium')!
    expect(vr.enabled).toBe(true)
    expect(vr.id).toBe('u1') // user's id, not company's

    const custom = merged.find(b => b.name === 'Custom Benefit')!
    expect(custom.enabled).toBe(true)

    // Missing company benefit appended as disabled
    const top = merged.find(b => b.name === 'Plano Top')!
    expect(top).toBeDefined()
    expect(top.enabled).toBe(false)
  })

  it('matches existing entries case-insensitively (no duplicates)', () => {
    const userDraft: JobBenefit[] = [
      { ...cb({ id: 'u1', name: 'vale refeição' }), enabled: true },
    ]
    const company = [
      cb({ id: 'c1', name: 'Vale Refeição', is_highlighted: true }),
    ]
    const merged = mergeCompanyBenefits(userDraft, company)
    expect(merged).toHaveLength(1)
    expect(merged[0].id).toBe('u1') // existing wins
  })

  it('returns the same reference when nothing needs to be added', () => {
    const userDraft: JobBenefit[] = [
      { ...cb({ id: 'u1', name: 'VR' }), enabled: true },
    ]
    const company = [cb({ id: 'c1', name: 'VR' })]
    const merged = mergeCompanyBenefits(userDraft, company)
    expect(merged).toBe(userDraft) // ref equality → no needless re-render
  })

  it('handles an empty existing list (no-placeholder, no-user case)', () => {
    const company = [cb({ id: 'c1', name: 'VR', is_highlighted: true })]
    const merged = mergeCompanyBenefits([], company)
    // Empty existing is NOT the placeholder; treated as loaded-empty,
    // so company benefits are appended disabled.
    expect(merged).toHaveLength(1)
    expect(merged[0].enabled).toBe(false)
  })
})
