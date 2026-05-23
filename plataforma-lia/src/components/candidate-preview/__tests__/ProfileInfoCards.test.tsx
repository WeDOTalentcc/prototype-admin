/**
 * Tests — ProfileInfoCards component
 *
 * Sensor canonical contra regressão "cn is not defined" descoberta em
 * 2026-05-23 (commit 24a70336a introduziu cn() em 4 chips condicionais
 * sem adicionar `import { cn } from '@/lib/utils'`, quebrando
 * `/pt/funil-de-talentos` ao abrir candidate preview).
 *
 * Render smoke test que exercita os 3 chips condicionais com cn():
 *  - is_remote (linha 224)
 *  - willing_to_relocate (linha 232)
 *  - mobility (linha 242)
 * Plus chip Idioma proficiency (linha 113).
 *
 * Se cn() voltar a ser referenciado sem import, este teste joga
 * ReferenceError no render e falha — pega o defeito no PR, antes de
 * chegar em produção.
 */
import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { ProfileInfoCards } from '../ProfileInfoCards'

const baseCandidate = {
  formation: [],
  certifications: [],
  expected_salary: null,
  current_salary: null,
  is_remote: false,
  willing_to_relocate: false,
  mobility: false,
  consent_given: false,
}

const defaultProps = {
  candidate: baseCandidate as Record<string, unknown>,
  formatCurrency: (v: number | string | null | undefined) =>
    v == null ? '' : String(v),
  languagesData: [
    { language: 'Português', proficiency: 'Nativo' },
  ],
  hasSalaryData: () => false,
  hasAddressData: () => false,
  getAddressString: () => '',
}

describe('ProfileInfoCards — cn import canonical contract', () => {
  it('renders without throwing ReferenceError (cn import present)', () => {
    expect(() => render(<ProfileInfoCards {...defaultProps} />)).not.toThrow()
  })

  it('renders chips condicionais (is_remote / willing_to_relocate / mobility) sem cn ReferenceError', () => {
    const props = {
      ...defaultProps,
      candidate: {
        ...baseCandidate,
        is_remote: true,
        willing_to_relocate: true,
        mobility: true,
      } as Record<string, unknown>,
    }
    expect(() => render(<ProfileInfoCards {...props} />)).not.toThrow()
  })

  it('renders chip Idioma proficiency (linha 113 cn-call) sem ReferenceError', () => {
    const props = {
      ...defaultProps,
      languagesData: [
        { language: 'Inglês', proficiency: 'Fluente' },
        { language: 'Espanhol', proficiency: 'Intermediário' },
      ],
    }
    expect(() => render(<ProfileInfoCards {...props} />)).not.toThrow()
  })
})
