/**
 * F-C sensor: SSE context parity for pipeline_transition_agent.
 *
 * The REST path (/interpret-context) passed these fields to the agent:
 *   candidate_id, candidate_name, job_title, from_stage, to_stage,
 *   action_behavior, company_id
 *
 * The SSE path (sendMessageViaSSE context arg) must pass the same fields.
 * This test pins that contract so a refactor of sseSendMessage can't silently
 * drop a field the agent depends on.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

const mockSendMessageViaSSE = vi.fn()
vi.mock('@/hooks/chat/useChatTransport', () => ({
  useChatTransport: vi.fn((_sid: string, _opts: unknown, _onEvent: unknown) => ({
    sendMessageViaSSE: mockSendMessageViaSSE,
  })),
}))

vi.mock('../use-interpret-context', () => ({
  useInterpretContext: vi.fn(() => ({
    sendMessage: vi.fn(),
    messages: [],
    result: null,
    isLoading: false,
    reset: vi.fn(),
    conversationId: undefined,
  })),
}))

// Required context fields the pipeline_transition_agent reads (F-A verified BE side)
const REQUIRED_CONTEXT_FIELDS = [
  'action_behavior',
  'candidate_id',
  'from_stage',
  'to_stage',
] as const

describe('F-C sensor: SSE context parity with pipeline_transition_agent', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_LIA_TRANSITION_VIA_SSE', 'true')
    vi.resetModules()
    mockSendMessageViaSSE.mockClear()
  })

  it('sendMessageViaSSE receives all required context fields', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    const fullParams = {
      candidate_id: 'cand-ctx-parity',
      candidate_name: 'Test Candidate',
      job_id: 'job-ctx-parity',
      job_title: 'Software Engineer',
      from_stage: 'triagem',
      to_stage: 'entrevista',
      action_behavior: 'active',
      company_id: 'comp-ctx-parity',
    }

    act(() => {
      result.current.sendMessage('avalie este candidato', fullParams)
    })

    expect(mockSendMessageViaSSE).toHaveBeenCalledOnce()
    const [, , domain, contextArg] = mockSendMessageViaSSE.mock.calls[0]

    // Domain must be pipeline_transition (not pipeline_context — F-A fix)
    expect(domain).toBe('pipeline_transition')

    // All required fields must be present in context
    for (const field of REQUIRED_CONTEXT_FIELDS) {
      expect(contextArg).toHaveProperty(field)
      expect(contextArg[field]).toBeTruthy()
    }
  })

  it('action_behavior value is passed verbatim', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    act(() => {
      result.current.sendMessage('msg', {
        candidate_id: 'c',
        from_stage: 'f',
        to_stage: 't',
        action_behavior: 'passive',
      })
    })

    const [, , , ctx] = mockSendMessageViaSSE.mock.calls[0]
    expect(ctx.action_behavior).toBe('passive')
  })

  it('candidate_id, from_stage, to_stage are not empty strings in context', async () => {
    const { useTransitionChat } = await import('../use-transition-chat')
    const { result } = renderHook(() => useTransitionChat())

    const params = {
      candidate_id: 'cand-007',
      from_stage: 'triagem',
      to_stage: 'proposta',
      action_behavior: 'active',
    }
    act(() => {
      result.current.sendMessage('teste', params)
    })

    const [, , , ctx] = mockSendMessageViaSSE.mock.calls[0]
    expect(ctx.candidate_id).toBe('cand-007')
    expect(ctx.from_stage).toBe('triagem')
    expect(ctx.to_stage).toBe('proposta')
  })
})
