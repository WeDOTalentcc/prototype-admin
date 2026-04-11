import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import React from 'react'

let capturedOnEvent: ((event: Record<string, unknown>) => void) | undefined
let capturedOnComplete: ((content: string, plan?: Record<string, unknown>) => void) | undefined
let capturedSessionId: string | undefined

const mockConnect = vi.fn()
const mockDisconnect = vi.fn()
const mockSendMessage = vi.fn()
const mockSendRaw = vi.fn()
const mockClearTokens = vi.fn()
let mockIsConnected = true

const mockSendMessageViaSSE = vi.fn()

vi.mock('../useChatTransport', () => ({
  useChatTransport: (
    sessionId: string,
    _options: unknown,
    onEvent: (event: Record<string, unknown>) => void,
  ) => {
    capturedSessionId = sessionId
    capturedOnEvent = onEvent
    return {
      tokens: '',
      isStreaming: false,
      isConnected: mockIsConnected,
      isReconnecting: false,
      reconnectAttempt: 0,
      error: null,
      transportMode: mockIsConnected ? 'ws' : 'disconnected',
      connect: mockConnect,
      disconnect: mockDisconnect,
      sendMessage: mockSendMessage,
      sendRaw: mockSendRaw,
      clearTokens: mockClearTokens,
      sendMessageViaSSE: mockSendMessageViaSSE,
    }
  },
}))

vi.mock('../use-agent-streaming', async () => {
  const actual = await vi.importActual('../use-agent-streaming')
  return actual
})

vi.mock('@/stores/recent-items-store', () => ({
  useRecentItemsStore: () => ({
    addItem: vi.fn(),
  }),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

vi.mock('@/hooks/use-navigation-intent', () => ({
  useNavigationIntent: () => ({ detect: vi.fn(), result: null, clear: vi.fn() }),
}))

import { useLiaChatConnection, formatMessageTime, type LiaChatMessage } from '../use-lia-chat-connection'

describe('Unified LIA Chat — Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsConnected = true
    capturedOnEvent = undefined
    capturedOnComplete = undefined
    capturedSessionId = undefined
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
  })

  describe('Cross-component conversation_id persistence', () => {
    it('REST fallback persists conversation_id from response', async () => {
      mockIsConnected = false
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            content: 'Hello',
            conversation_id: 'conv-from-rest',
          }),
        })

      const onComplete = vi.fn()
      const { result } = renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onMessageComplete: onComplete,
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hi')
      })

      expect(result.current.conversationId).toBe('conv-from-rest')
    })

    it('setConversationId + sendMessage preserves threading', async () => {
      mockIsConnected = true

      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      act(() => {
        result.current.setConversationId('conv-A')
      })

      expect(result.current.conversationId).toBe('conv-A')

      act(() => {
        result.current.setConversationId('conv-B')
      })

      expect(result.current.conversationId).toBe('conv-B')
    })

    it('initConversation → message flow creates and uses conversation_id', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: 'new-conv-123' }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      let convId: string | null = null
      await act(async () => {
        convId = await result.current.initConversation('Hello')
      })

      expect(convId).toBe('new-conv-123')
      expect(result.current.conversationId).toBe('new-conv-123')

      await act(async () => {
        await result.current.sendMessage('Follow up')
      })

      expect(mockSendMessage).toHaveBeenCalledWith('Follow up', { conversation_id: 'new-conv-123' }, '')
    })
  })

  describe('Message store consistency', () => {
    it('onMessageComplete fires for WS message events', () => {
      const onComplete = vi.fn()
      renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onMessageComplete: onComplete,
        })
      )

      act(() => {
        capturedOnEvent?.({
          type: 'message',
          content: 'LIA response via WS',
        })
      })

      expect(onComplete).toHaveBeenCalledWith('LIA response via WS', undefined)
    })

    it('onMessageComplete fires with executionPlan from WS', () => {
      const onComplete = vi.fn()
      renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onMessageComplete: onComplete,
        })
      )

      const plan = { steps: [{ action: 'create_job' }] }
      act(() => {
        capturedOnEvent?.({
          type: 'message',
          content: 'Plan created',
          execution_plan: plan,
        })
      })

      expect(onComplete).toHaveBeenCalledWith('Plan created', plan)
    })

    it('onMessageComplete fires for REST fallback messages', async () => {
      mockIsConnected = false
      const onComplete = vi.fn()

      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ content: 'REST response' }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onMessageComplete: onComplete,
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(onComplete).toHaveBeenCalledWith('REST response')
    })
  })

  describe('Context switching', () => {
    it('switching context preserves and restores conversation IDs', () => {
      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      act(() => {
        result.current.setConversationId('conv-kanban')
      })
      expect(result.current.conversationId).toBe('conv-kanban')

      act(() => {
        result.current.setConversationId('conv-candidates')
      })
      expect(result.current.conversationId).toBe('conv-candidates')

      act(() => {
        result.current.setConversationId('conv-kanban')
      })
      expect(result.current.conversationId).toBe('conv-kanban')
    })
  })

  describe('sendOrchestratedMessage threading', () => {
    it('uses explicit conversationId when provided', async () => {
      mockIsConnected = false
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            content: 'Response',
            conversation_id: 'conv-returned',
          }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      act(() => {
        result.current.setConversationId('conv-old')
      })

      expect(result.current.conversationId).toBe('conv-old')

      await act(async () => {
        await result.current.sendMessage('test')
      })

      expect(result.current.conversationId).toBe('conv-returned')
    })

    it('REST fallback calls onMessageComplete exactly once per message', async () => {
      mockIsConnected = false
      const onComplete = vi.fn()

      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ content: 'LIA reply', conversation_id: 'conv-1' }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onMessageComplete: onComplete,
        })
      )

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(onComplete).toHaveBeenCalledTimes(1)
      expect(onComplete).toHaveBeenCalledWith('LIA reply')
    })
  })

  describe('HITL persistence across events', () => {
    it('HITL state clears after message completion', () => {
      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      act(() => {
        capturedOnEvent?.({
          type: 'approval_required',
          pending_id: 'hitl-1',
          thread_id: 't-1',
          action: 'move_candidate',
          description: 'Move candidate to next stage',
          data: { candidate_id: 'c-1' },
        })
      })

      expect(result.current.hitlPending).not.toBeNull()

      act(() => {
        result.current.sendApproval(true)
      })

      act(() => {
        capturedOnEvent?.({
          type: 'message',
          content: 'Candidate moved successfully',
        })
      })

      expect(result.current.hitlPending).toBeNull()
    })
  })

  describe('Panel updates', () => {
    it('panel_update events forward to callback across contexts', () => {
      const onPanelUpdate = vi.fn()
      renderHook(() =>
        useLiaChatConnection({
          sessionId: 'test-session',
          onPanelUpdate,
        })
      )

      act(() => {
        capturedOnEvent?.({
          type: 'panel_update',
          panel_type: 'calibration',
          panel_data: { score: 85 },
          action: 'open',
        })
      })

      expect(onPanelUpdate).toHaveBeenCalledWith({
        panel_type: 'calibration',
        panel_data: { score: 85 },
        panel_title: undefined,
        action: 'open',
      })

      act(() => {
        capturedOnEvent?.({
          type: 'panel_update',
          panel_type: 'calibration',
          panel_data: { score: 90 },
          action: 'update',
        })
      })

      expect(onPanelUpdate).toHaveBeenCalledTimes(2)
    })
  })

  describe('loadHistory and initConversation lifecycle', () => {
    it('loadHistory maps backend messages to LiaChatMessage format', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            messages: [
              { id: 'm-1', role: 'user', content: 'Hello', created_at: '2026-01-01T12:00:00Z' },
              { id: 'm-2', role: 'assistant', content: 'Hi there', created_at: '2026-01-01T12:01:00Z' },
              { id: 'm-3', role: 'user', content: 'How are you?', created_at: '2026-01-01T12:02:00Z' },
            ],
          }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      let history: LiaChatMessage[] = []
      await act(async () => {
        history = await result.current.loadHistory('conv-abc')
      })

      expect(history).toHaveLength(3)
      expect(history[0].sender).toBe('user')
      expect(history[0].content).toBe('Hello')
      expect(history[1].sender).toBe('lia')
      expect(history[1].content).toBe('Hi there')
      expect(history[2].sender).toBe('user')
    })

    it('initConversation masks PII in title', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: 'conv-pii' }),
        })

      const { result } = renderHook(() =>
        useLiaChatConnection({ sessionId: 'test-session' })
      )

      await act(async () => {
        await result.current.initConversation('Buscar candidato email@test.com 123.456.789-00')
      })

      const body = JSON.parse(mockFetch.mock.calls[1][1].body)
      expect(body.title).toContain('[email]')
      expect(body.title).toContain('[CPF]')
      expect(body.title).not.toContain('email@test.com')
      expect(body.title).not.toContain('123.456.789-00')
    })
  })
})
