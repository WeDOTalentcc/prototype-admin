// src/stores/__tests__/lia-panel-store.test.ts
vi.mock('../auth-store', () => ({
  registerStoreReset: vi.fn(),
}))

import { useLiaPanelStore } from '../lia-panel-store'
import { act } from '@testing-library/react'

const { getState, setState } = useLiaPanelStore

beforeEach(() => {
  act(() =>
    setState({
      focusedToolCallId: null,
      _panelOpenBySession: {},
    })
  )
})

describe('lia-panel-store', () => {
  it('starts with null focusedToolCallId and empty session map', () => {
    const s = getState()
    expect(s.focusedToolCallId).toBeNull()
    expect(s._panelOpenBySession).toEqual({})
  })

  it('openForToolCall sets focusedToolCallId and marks session open', () => {
    act(() => getState().openForToolCall('tc-abc', 'session-1'))
    const s = getState()
    expect(s.focusedToolCallId).toBe('tc-abc')
    expect(s._panelOpenBySession['session-1']).toBe(true)
  })

  it('closePanel marks session closed but preserves focusedToolCallId', () => {
    act(() => getState().openForToolCall('tc-abc', 'session-1'))
    act(() => getState().closePanel('session-1'))
    const s = getState()
    expect(s._panelOpenBySession['session-1']).toBe(false)
    expect(s.focusedToolCallId).toBe('tc-abc')
  })

  it('isPanelOpenForSession returns correct boolean', () => {
    act(() => getState().openForToolCall('tc-1', 'sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(true)
    expect(getState().isPanelOpenForSession('sess-B')).toBe(false)
    act(() => getState().closePanel('sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(false)
  })

  it('multiple sessions are independent', () => {
    act(() => getState().openForToolCall('tc-1', 'sess-A'))
    act(() => getState().openForToolCall('tc-2', 'sess-B'))
    act(() => getState().closePanel('sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(false)
    expect(getState().isPanelOpenForSession('sess-B')).toBe(true)
    expect(getState().focusedToolCallId).toBe('tc-2')
  })
})
