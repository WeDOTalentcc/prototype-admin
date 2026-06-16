vi.mock('../auth-store', () => ({
  registerStoreReset: vi.fn(),
}))

import { useChatStateStore } from '../chat-state-store'
import { act } from '@testing-library/react'

const { getState, setState } = useChatStateStore

beforeEach(() => {
  act(() =>
    setState({
      conversationIds: {},
      contextSnapshots: { wizard: null, general: null },
      wizardDraftId: null,
      wizardDraft: null,
      userCommands: [],
      liaTemplates: [],
    })
  )
})

describe('chat-state-store', () => {
  it('starts with empty state', () => {
    const s = getState()
    expect(s.conversationIds).toEqual({})
    expect(s.contextSnapshots.wizard).toBeNull()
    expect(s.wizardDraftId).toBeNull()
    expect(s.userCommands).toEqual([])
  })

  it('setConversationId stores by key', () => {
    act(() => getState().setConversationId('wizard', 'conv-123'))
    expect(getState().conversationIds['wizard']).toBe('conv-123')
  })

  it('getConversationId returns stored id or null', () => {
    act(() => getState().setConversationId('chat', 'c-1'))
    expect(getState().getConversationId('chat')).toBe('c-1')
    expect(getState().getConversationId('nonexistent')).toBeNull()
  })

  it('removeConversationId deletes the key', () => {
    act(() => getState().setConversationId('wizard', 'conv-1'))
    act(() => getState().removeConversationId('wizard'))
    expect(getState().getConversationId('wizard')).toBeNull()
  })

  it('setContextSnapshots stores wizard and general', () => {
    const snapshots = {
      wizard: {
        stage: 'competencies',
        basicInfoFields: {},
        technicalSkills: [],
        behavioralCompetencies: [],
        salaryInfo: {},
        wsiQuestions: [],
        detectedCriteria: {},
        generatedJobDescription: '',
        fastTrackSourceJobId: null,
        timestamp: Date.now(),
      },
      general: null,
    }
    act(() => getState().setContextSnapshots(snapshots as never))
    expect(getState().contextSnapshots.wizard?.stage).toBe('competencies')
  })

  it('clearContextSnapshots resets both to null', () => {
    act(() =>
      getState().setContextSnapshots({
        wizard: { stage: 'salary' } as never,
        general: null,
      })
    )
    act(() => getState().clearContextSnapshots())
    expect(getState().contextSnapshots.wizard).toBeNull()
    expect(getState().contextSnapshots.general).toBeNull()
  })

  it('setWizardDraft stores draft object', () => {
    const draft = { title: 'Dev Python', salary: '10k' }
    act(() => getState().setWizardDraft(draft))
    expect(getState().wizardDraft).toEqual(draft)
  })

  it('setUserCommands stores command array', () => {
    const cmds = [
      {
        id: '1',
        title: 'Buscar',
        command: '/search',
        description: 'Search',
        category: 'search',
        examples: [],
        tags: [],
        createdAt: new Date().toISOString(),
        usageCount: 0,
        rating: 5,
        author: 'user',
      },
    ]
    act(() => getState().setUserCommands(cmds))
    expect(getState().userCommands).toHaveLength(1)
    expect(getState().userCommands[0].command).toBe('/search')
  })

  it('resetStore clears everything', () => {
    act(() => {
      getState().setConversationId('a', 'b')
      getState().setWizardDraftId('draft-1')
      getState().setWizardDraft({ title: 'Test' })
    })
    act(() => getState().resetStore())
    expect(getState().conversationIds).toEqual({})
    expect(getState().wizardDraftId).toBeNull()
    expect(getState().wizardDraft).toBeNull()
  })
})
