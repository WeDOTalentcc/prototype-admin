import { INITIAL_BENEFITS } from './constants'
import type { JobBenefit } from '@/types/benefits'
import type { CompanyBenefit } from '@/types/benefits'

/**
 * Task #765 — pure merge function used by WizardContext to hydrate the
 * salaryInfo.benefits list from the company catalogue exactly once.
 *
 *  - When the wizard is brand new (the placeholder INITIAL_BENEFITS is
 *    still in place), the catalogue replaces the placeholder so the
 *    recruiter sees every benefit the company offers, with mandatory /
 *    highlighted entries pre-enabled.
 *  - When a draft / vacancy is already loaded (or the user has toggled
 *    anything), every existing selection is preserved and missing
 *    catalogue items are appended as disabled — never clobbering the
 *    recruiter's choices.
 *
 * Returns the same array reference when there is nothing to add so the
 * setSalaryInfo updater can short-circuit re-renders.
 */
export function mergeCompanyBenefits(
  existing: JobBenefit[],
  companyBenefits: CompanyBenefit[]
): JobBenefit[] {
  const isStillInitial =
    existing.length === INITIAL_BENEFITS.length &&
    existing.every(b => INITIAL_BENEFITS.some(ib => ib.name === b.name))

  if (isStillInitial) {
    return companyBenefits.map(cb => ({
      ...cb,
      enabled: cb.is_highlighted || cb.is_mandatory || false,
    }))
  }

  const existingNames = new Set(
    existing.map(b => (b.name || '').toLowerCase()).filter(Boolean)
  )
  const additions: JobBenefit[] = companyBenefits
    .filter(cb => !existingNames.has((cb.name || '').toLowerCase()))
    .map(cb => ({ ...cb, enabled: false }))

  if (additions.length === 0) return existing
  return [...existing, ...additions]
}
