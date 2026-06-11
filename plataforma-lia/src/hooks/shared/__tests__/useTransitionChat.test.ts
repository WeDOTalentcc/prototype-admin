/**
 * F-B TDD: useTransitionChat — unified REST/SSE transition chat hook.
 *
 * Tests:
 * 1. REST path (SSE_ENABLED=false): delegates to useInterpretContext
 * 2. SSE path (SSE_ENABLED=true): uses useChatTransport.sendMessageViaSSE
 * 3. SSE message accumulation: token events → ChatMessage
 * 4. SSE HITL: approval_required → hitlPending; sendApproval → cleared
 * 5. Context fields correctly passed to sendMessageViaSSE
 * 6. sseReset clears all state
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

// ─── Mocks ─────────────────────────────────────────────────────────────────

const mockSendMessageViaSSE = vi.fn()
const mockUseChatTransportOnEvent = vi.fn()

vi.mock('@/hooks/chat/useChatTransport', () => ({
  useChatTransport: vi.fn((sessionId: string, _opts: unknown, onEvent: (e: unknown) => void) => {
    mockUseChatTransportOnEvent.mockImplementation(onEvent)
    return { sendMessageViaSSE: mockSendMessageViaSSE }
  }),
}))

const mockRestSendMessage = vi.fn()
const mockRestReset = vi.fn()

vi.mock('../use-interpret-context', () => ({
  useInterpretContext: vi.fn(() => ({
    sendMessage: mockRestSendMessage,
    messages: [],
    result: null,
    isLoading: false,
    reset: mockRestReset,
    conversationId: undefined,
  })),
}))

// ─── Helper: fire SSE event ─────────────────────────────────────────────────

function fireEvent(event: Record<string, unknown>) {
  act(() => {
    mockUseChatTransportOnEvent(event)
  })
}

// ─── Tests ─────────────────────────────────────────────────────────────────

describe('useTransitionChat — REST path (SSE_ENABLED=false)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_LIA_TRANSITION_VIA_SSE', 'false')
    vi.resetModules()
  })

  it('delegates sendMessage to useInterpretContext.sendMessage', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())
    const params = {
      candidate_id: 'cand-1',
      from_stage: 'triagem',
      to_stage: 'entrevista',
      action_behavior: 'passive',
    }
    act(() => {
      result.current.sendMessage('olá', params)
    })
    expect(mockRestSendMessage).toHaveBeenCalledWith('olá', params)
  })

  it('hitlPending is null (REST has no per-session HITL)', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())
    expect(result.current.hitlPending).toBeNull()
  })
})

describe('useTransitionChat — SSE path (SSE_ENABLED=true)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_LIA_TRANSITION_VIA_SSE', 'true')
    vi.resetModules()
    mockSendMessageViaSSE.mockClear()
    mockUseChatTransportOnEvent.mockClear()
  })

  it('sends via sendMessageViaSSE with domain=pipeline_transition', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())
    const params = {
      candidate_id: 'cand-42',
      candidate_name: 'Maria Silva',
      job_id: 'job-7',
      job_title: 'Eng. Software',
      from_stage: 'triagem',
      to_stage: 'entrevista',
      action_behavior: 'active',
      company_id: 'comp-99',
    }
    act(() => {
      result.current.sendMessage('mover candidata', params)
    })
    expect(mockSendMessageViaSSE).toHaveBeenCalledWith(
      expect.any(String),          // sessionId
      'mover candidata',
      'pipeline_transition',
      expect.objectContaining({
        candidate_id: 'cand-42',
        candidate_name: 'Maria Silva',
        from_stage: 'triagem',
        to_stage: 'entrevista',
        action_behavior: 'active',
        company_id: 'comp-99',
      }),
      null,
    )
  })

  it('accumulates tokens into ChatMessage on "message" event', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    // seed a user message first
    act(() => {
      result.current.sendMessage('mover', { candidate_id: 'c1', from_stage: 'a', to_stage: 'b', action_behavior: 'passive' })
    })
    // simulate tokens
    fireEvent({ type: 'thinking' })
    fireEvent({ type: 'token', content: 'Can' })
    fireEvent({ type: 'token', content: 'didato' })
    fireEvent({ type: 'message', content: 'Candidato movido com sucesso.', confidence: 0.9 })

    const msgs = result.current.messages
    const liaMsg = msgs.find(m => m.role === 'lia')
    expect(liaMsg).toBeDefined()
    expect(liaMsg!.content).toBe('Candidato movido com sucesso.')
    expect(liaMsg!.metadata?.confidence).toBe(0.9)
  })

  it('sets hitlPending on approval_required event', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    expect(result.current.hitlPending).toBeNull()
    fireEvent({
      type: 'approval_required',
      pending_id: 'pending-abc',
      action: 'pipeline_transition',
      description: 'Mover Maria de triagem para entrevista',
    })

    expect(result.current.hitlPending).toEqual({
      pending_id: 'pending-abc',
      action: 'pipeline_transition',
      description: 'Mover Maria de triagem para entrevista',
    })
  })

  it('sendApproval(true) clears hitlPending and sends HITL_APPROVED via SSE', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    const params = { candidate_id: 'c1', from_stage: 'a', to_stage: 'b', action_behavior: 'active' }
    act(() => { result.current.sendMessage('mover', params) })
    mockSendMessageViaSSE.mockClear()

    fireEvent({
      type: 'approval_required',
      pending_id: 'pid-42',
      action: 'pipeline_transition',
      description: 'desc',
    })
    expect(result.current.hitlPending).not.toBeNull()

    act(() => { result.current.sendApproval(true) })

    expect(result.current.hitlPending).toBeNull()
    expect(mockSendMessageViaSSE).toHaveBeenCalledWith(
      expect.any(String),
      '[HITL_APPROVED]',
      'pipeline_transition',
      expect.objectContaining({
        approve_pending_id: 'pid-42',
        hitl_approved: true,
      }),
      null,
    )
  })

  it('sendApproval(false) clears hitlPending without sending SSE', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    act(() => { result.current.sendMessage('mover', { candidate_id: 'c1', from_stage: 'a', to_stage: 'b', action_behavior: 'active' }) })
    mockSendMessageViaSSE.mockClear()
    fireEvent({ type: 'approval_required', pending_id: 'pid-99', action: 'x', description: 'y' })

    act(() => { result.current.sendApproval(false) })
    expect(result.current.hitlPending).toBeNull()
    expect(mockSendMessageViaSSE).not.toHaveBeenCalled()
  })

  it('sseReset clears messages, loading and hitlPending', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    act(() => { result.current.sendMessage('test', { candidate_id: 'c1', from_stage: 'a', to_stage: 'b', action_behavior: 'passive' }) })
    fireEvent({ type: 'approval_required', pending_id: 'p1', action: 'a', description: 'd' })
    expect(result.current.messages.length).toBeGreaterThan(0)
    expect(result.current.hitlPending).not.toBeNull()

    act(() => { result.current.reset() })
    expect(result.current.messages).toHaveLength(0)
    expect(result.current.hitlPending).toBeNull()
    expect(result.current.isLoading).toBe(false)
  })
})
