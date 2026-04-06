import { useWizardStore } from '../wizard-store'
import { act } from '@testing-library/react'

const { getState, setState } = useWizardStore

beforeEach(() => {
  act(() => {
    setState({ draft: null, draftId: null })
  })
})

describe('wizard-store', () => {
  it('starts with null draft and draftId', () => {
    const state = getState()
    expect(state.draft).toBeNull()
    expect(state.draftId).toBeNull()
  })

  it('setDraft stores draft data', () => {
    const draft = {
      jobDraftId: 'draft-1',
      basicInfoFields: { cargo: 'Dev Python' },
      currentStage: 'job-description',
    }
    act(() => getState().setDraft(draft))
    expect(getState().draft).toEqual(draft)
  })

  it('setDraftId stores the id', () => {
    act(() => getState().setDraftId('abc-123'))
    expect(getState().draftId).toBe('abc-123')
  })

  it('clearDraft resets both draft and draftId', () => {
    act(() => {
      getState().setDraft({ jobDraftId: 'x' })
      getState().setDraftId('x')
    })
    expect(getState().draft).not.toBeNull()

    act(() => getState().clearDraft())
    expect(getState().draft).toBeNull()
    expect(getState().draftId).toBeNull()
  })

  it('setDraft with null clears the draft', () => {
    act(() => getState().setDraft({ jobDraftId: 'a' }))
    act(() => getState().setDraft(null))
    expect(getState().draft).toBeNull()
  })

  it('preserves other state when setting draft', () => {
    act(() => {
      getState().setDraftId('keep-me')
      getState().setDraft({ jobDraftId: 'new' })
    })
    expect(getState().draftId).toBe('keep-me')
    expect(getState().draft?.jobDraftId).toBe('new')
  })
})
