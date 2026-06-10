import { describe, it, expect } from 'vitest'
import { getCandidateBadges, SUB_STATUS_DISPLAY_MAP } from '../badge-utils'

describe('badge-utils — hired sub-status (G4)', () => {
  it('SUB_STATUS_DISPLAY_MAP has hired with label Contratado and green color', () => {
    const hired = SUB_STATUS_DISPLAY_MAP['hired']
    expect(hired).toBeDefined()
    expect(hired.label).toBe('Contratado')
    expect(hired.color).toBe('green')
    expect(hired.icon).toBe('check-circle')
  })

  it('getCandidateBadges returns Contratado badge for subStatus=hired', () => {
    const badges = getCandidateBadges({ subStatus: 'hired' })
    expect(badges).toHaveLength(1)
    expect(badges[0].label).toBe('Contratado')
    expect(badges[0].color).toBe('green')
    expect(badges[0].type).toBe('sub_status')
  })

  it('hired badge does not interfere with offer_accepted badge', () => {
    const offerBadges = getCandidateBadges({ subStatus: 'offer_accepted' })
    expect(offerBadges[0].label).toBe('Proposta Aceita')

    const hiredBadges = getCandidateBadges({ subStatus: 'hired' })
    expect(hiredBadges[0].label).toBe('Contratado')
  })
})
