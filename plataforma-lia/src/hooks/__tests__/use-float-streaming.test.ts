/**
 * Testes unitários — useFloatStreaming (Sprint J)
 *
 * Cobre:
 * - Estado inicial: isConnected=false, isStreaming=false, hitlPending=null
 * - handleEvent: approval_required → preenche hitlPending
 * - handleEvent: approval_confirmed → sem efeito visível (aguarda message)
 * - handleEvent: message → chama onComplete + limpa hitlPending
 * - sendApproval(true) → envia approval_response via sendRaw
 * - sendApproval(false) → envia rejection + limpa hitlPending imediatamente
 * - sendApproval sem pending → no-op
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFloatStreaming } from '../use-float-streaming'

// Mock useAgentStreaming
const mockSendMessage = vi.fn()
const mockSendRaw = vi.fn()
const mockConnect = vi.fn()
const mockDisconnect = vi.fn()
const mockClearTokens = vi.fn()
let mockIsConnected = false

let capturedOnEvent: ((event: Record<string, unknown>) => void) | undefined

vi.mock('../use-agent-streaming', () => ({
  useAgentStreaming: (
    _sessionId: string,
    _options: unknown,
    onEvent: (event: Record<string, unknown>) => void,
  ) => {
    capturedOnEvent = onEvent
    return {
      tokens: '',
      isStreaming: false,
      isConnected: mockIsConnected,
      error: null,
      connect: mockConnect,
      disconnect: mockDisconnect,
      sendMessage: mockSendMessage,
      sendRaw: mockSendRaw,
      clearTokens: mockClearTokens,
    }
  },
}))

describe('useFloatStreaming', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    capturedOnEvent = undefined
    mockIsConnected = false
  })

  it('estado inicial: sem pending, sem erro', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-1', onComplete)
    )
    expect(result.current.hitlPending).toBeNull()
    expect(result.current.isConnected).toBe(false)
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('approval_required → preenche hitlPending', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-2', onComplete)
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-001',
        thread_id: 't-001',
        action: 'move_candidate',
        description: 'Mover João Silva para Entrevista',
        data: { candidate_id: 'c-1', to_stage: 'interview' },
      })
    })

    expect(result.current.hitlPending).not.toBeNull()
    expect(result.current.hitlPending?.pendingId).toBe('p-001')
    expect(result.current.hitlPending?.action).toBe('move_candidate')
    expect(result.current.hitlPending?.description).toBe('Mover João Silva para Entrevista')
  })

  it('message → chama onComplete e limpa hitlPending', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-3', onComplete)
    )

    // Primeiro simula um HITL pending
    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-002',
        thread_id: 't-002',
        action: 'schedule_interview',
        description: 'Agendar entrevista',
        data: {},
      })
    })
    expect(result.current.hitlPending).not.toBeNull()

    // Depois simula a resposta final após aprovação
    act(() => {
      capturedOnEvent?.({
        type: 'message',
        content: 'Entrevista agendada com sucesso para quinta-feira.',
      })
    })

    expect(onComplete).toHaveBeenCalledWith('Entrevista agendada com sucesso para quinta-feira.')
    expect(result.current.hitlPending).toBeNull()
  })

  it('message sem content → não chama onComplete', () => {
    const onComplete = vi.fn()
    renderHook(() => useFloatStreaming('session-4', onComplete))

    act(() => {
      capturedOnEvent?.({ type: 'message', content: '' })
    })

    expect(onComplete).not.toHaveBeenCalled()
  })

  it('sendApproval(true) → envia approval_response via sendRaw', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-5', onComplete)
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-003',
        thread_id: 't-003',
        action: 'reject_candidate',
        description: 'Rejeitar candidato',
        data: {},
      })
    })

    act(() => {
      result.current.sendApproval(true)
    })

    expect(mockSendRaw).toHaveBeenCalledWith({
      type: 'approval_response',
      approved: true,
      thread_id: 't-003',
      pending_id: 'p-003',
    })
    // hitlPending NÃO limpa imediatamente na aprovação (aguarda backend confirmar)
    expect(result.current.hitlPending).not.toBeNull()
  })

  it('sendApproval(false) → envia rejection e limpa hitlPending imediatamente', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-6', onComplete)
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-004',
        thread_id: 't-004',
        action: 'send_email',
        description: 'Enviar email',
        data: {},
      })
    })

    act(() => {
      result.current.sendApproval(false)
    })

    expect(mockSendRaw).toHaveBeenCalledWith({
      type: 'approval_response',
      approved: false,
      thread_id: 't-004',
      pending_id: 'p-004',
    })
    // Na rejeição, limpa imediatamente sem aguardar backend
    expect(result.current.hitlPending).toBeNull()
  })

  it('sendApproval(true) duplo → envia apenas uma vez (guard double-submit)', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-ds', onComplete)
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-ds',
        thread_id: 't-ds',
        action: 'move_candidate',
        description: 'Mover',
        data: {},
      })
    })

    // Dois cliques rápidos em "Aprovar"
    act(() => {
      result.current.sendApproval(true)
      result.current.sendApproval(true)
    })

    // Deve ter enviado apenas UMA vez
    expect(mockSendRaw).toHaveBeenCalledTimes(1)
    expect(mockSendRaw).toHaveBeenCalledWith({
      type: 'approval_response',
      approved: true,
      thread_id: 't-ds',
      pending_id: 'p-ds',
    })
  })

  it('sendApproval sem pending → no-op, não chama sendRaw', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-7', onComplete)
    )

    act(() => {
      result.current.sendApproval(true)
    })

    expect(mockSendRaw).not.toHaveBeenCalled()
  })

  it('sendMessage chama wsSend com domain e clearTokens', () => {
    mockIsConnected = true
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-8', onComplete)
    )

    act(() => {
      result.current.sendMessage('buscar candidatos', 'sourcing')
    })

    expect(mockClearTokens).toHaveBeenCalled()
    expect(mockSendMessage).toHaveBeenCalledWith('buscar candidatos', {}, 'sourcing')
  })

  it('approval_confirmed → não altera hitlPending (aguarda message)', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useFloatStreaming('session-9', onComplete)
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-005',
        thread_id: 't-005',
        action: 'move_candidate',
        description: 'Mover candidato',
        data: {},
      })
    })

    act(() => {
      capturedOnEvent?.({ type: 'approval_confirmed' })
    })

    // hitlPending permanece até receber o message final
    expect(result.current.hitlPending).not.toBeNull()
    expect(onComplete).not.toHaveBeenCalled()
  })
})
