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
import { render, screen } from '@testing-library/react'
import { ProfileInfoCards } from '../ProfileInfoCards'
import { CandidateEditProvider } from '@/components/candidate-profile/CandidateEditContext'

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock('@/hooks/company/use-current-company', () => ({
  useCurrentCompany: () => ({ companyId: 'company-test' }),
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

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

describe('ProfileInfoCards — F10 caveats (self_introduction + certifications)', () => {
  function renderEditable(candidate: Record<string, unknown>, editable: boolean = true) {
    const updateField = vi.fn().mockResolvedValue({ success: true })
    return {
      result: render(
        <CandidateEditProvider
          editable={editable}
          candidateId="cand_xyz"
          updateField={updateField}
          isSaving={() => false}
        >
          <ProfileInfoCards
            candidate={candidate}
            formatCurrency={(v) => (v == null ? '' : String(v))}
            languagesData={[]}
            hasSalaryData={() => false}
            hasAddressData={() => false}
            getAddressString={() => ''}
          />
        </CandidateEditProvider>,
      ),
      updateField,
    }
  }

  it('renders ProfileNarrativeCard when editable=true even without self_introduction', () => {
    renderEditable({ certifications: [] }, true)
    expect(screen.getByTestId('profile-narrative-card')).toBeInTheDocument()
  })

  it('hides ProfileNarrativeCard when editable=false AND self_introduction empty', () => {
    renderEditable({ certifications: [], self_introduction: '' }, false)
    expect(screen.queryByTestId('profile-narrative-card')).not.toBeInTheDocument()
  })

  it('renders ProfileNarrativeCard read-only when editable=false BUT self_introduction present', () => {
    renderEditable({ certifications: [], self_introduction: 'Engenheiro senior...' }, false)
    expect(screen.getByTestId('profile-narrative-card')).toBeInTheDocument()
    expect(screen.getByText('Engenheiro senior...')).toBeInTheDocument()
  })

  it('renders ProfileCertificationsCard with add button when editable=true', () => {
    renderEditable({ certifications: [] }, true)
    expect(screen.getByTestId('profile-certifications-card')).toBeInTheDocument()
    expect(screen.getByTestId('cert-add-btn')).toBeInTheDocument()
  })

  it('hides cert add button when editable=false (drawer/kanban read-only)', () => {
    renderEditable({ certifications: ['AWS SAA'] }, false)
    expect(screen.queryByTestId('cert-add-btn')).not.toBeInTheDocument()
  })

  it('normalizes object certs to strings for display', () => {
    renderEditable(
      {
        certifications: [
          { name: 'PMP', issuer: 'PMI', date: '2020' },
          'AWS SAA',
        ],
      },
      false,
    )
    expect(screen.getByText('PMP')).toBeInTheDocument()
    expect(screen.getByText('PMI')).toBeInTheDocument()
    expect(screen.getByText('AWS SAA')).toBeInTheDocument()
  })

  it('renders per-cert edit + remove buttons when editable=true (data-testid pattern)', () => {
    renderEditable({ certifications: ['Cert A', 'Cert B'] }, true)
    expect(screen.getByTestId('cert-edit-btn-0')).toBeInTheDocument()
    expect(screen.getByTestId('cert-remove-btn-0')).toBeInTheDocument()
    expect(screen.getByTestId('cert-edit-btn-1')).toBeInTheDocument()
    expect(screen.getByTestId('cert-remove-btn-1')).toBeInTheDocument()
  })
})
