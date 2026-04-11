import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLiaChatConnection } from '../use-lia-chat-connection'

const mockSendMessage = vi.fn()
const mockSendRaw = vi.fn()
const mockConnect = vi.fn()
const mockDisconnect = vi.fn()
const mockClearTokens = vi.fn()
let mockIsConnected = false
let mockIsStreaming = false
let mockTokens = ''

let capturedOnEvent: ((event: Record<string, unknown>) => void) | undefined

const mockSendMessageViaSSE = vi.fn()

vi.mock('../useChatTransport', () => ({
  useChatTransport: (
    _sessionId: string,
    _options: unknown,
    onEvent: (event: Record<string, unknown>) => void,
  ) => {
    capturedOnEvent = onEvent
    return {
      tokens: mockTokens,
      isStreaming: mockIsStreaming,
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

describe('useLiaChatConnection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsConnected = false
    mockIsStreaming = false
    mockTokens = ''
    capturedOnEvent = undefined
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
  })

  it('returns initial state correctly', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    expect(result.current.conversationId).toBeNull()
    expect(result.current.isConnected).toBe(false)
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.isCreating).toBe(false)
    expect(result.current.isFetchingHistory).toBe(false)
    expect(result.current.hitlPending).toBeNull()
    expect(result.current.fairnessWarnings).toEqual([])
    expect(result.current.backgroundTasks).toEqual([])
    expect(result.current.thinkingSteps).toEqual([])
    expect(result.current.isThinking).toBe(false)
  })

  it('handles approval_required event', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-1',
        thread_id: 't-1',
        action: 'create_job',
        description: 'Create a new job posting',
        data: { title: 'Dev Sr' },
      })
    })

    expect(result.current.hitlPending).toEqual({
      pendingId: 'p-1',
      threadId: 't-1',
      action: 'create_job',
      description: 'Create a new job posting',
      data: { title: 'Dev Sr' },
    })
  })

  it('sendApproval sends approval_response via sendRaw and clears hitl on reject', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-2',
        thread_id: 't-2',
        action: 'delete_candidate',
        description: 'Delete candidate',
        data: {},
      })
    })

    expect(result.current.hitlPending).not.toBeNull()

    act(() => {
      result.current.sendApproval(false)
    })

    expect(mockSendRaw).toHaveBeenCalledWith({
      type: 'approval_response',
      approved: false,
      thread_id: 't-2',
      pending_id: 'p-2',
    })
    expect(result.current.hitlPending).toBeNull()
  })

  it('sendApproval with true sends approved but keeps hitlPending until message', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'approval_required',
        pending_id: 'p-3',
        thread_id: 't-3',
        action: 'send_email',
        description: 'Send email',
        data: {},
      })
    })

    act(() => {
      result.current.sendApproval(true)
    })

    expect(mockSendRaw).toHaveBeenCalledWith({
      type: 'approval_response',
      approved: true,
      thread_id: 't-3',
      pending_id: 'p-3',
    })
  })

  it('sendApproval without pending is a no-op', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      result.current.sendApproval(true)
    })

    expect(mockSendRaw).not.toHaveBeenCalled()
  })

  it('handles message event with onComplete callback', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useLiaChatConnection({
        sessionId: 'test-session',
        onMessageComplete: onComplete,
      })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'message',
        content: 'Hello from LIA',
      })
    })

    expect(onComplete).toHaveBeenCalledWith('Hello from LIA', undefined)
    expect(result.current.hitlPending).toBeNull()
  })

  it('handles message event with fairness warnings', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'message',
        content: 'Result with warnings',
        fairness_warnings: ['Gender bias detected'],
      })
    })

    expect(result.current.fairnessWarnings).toEqual(['Gender bias detected'])
  })

  it('dismissFairnessWarnings clears the warnings', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'message',
        content: 'Result',
        fairness_warnings: ['Bias warning'],
      })
    })

    expect(result.current.fairnessWarnings).toHaveLength(1)

    act(() => {
      result.current.dismissFairnessWarnings()
    })

    expect(result.current.fairnessWarnings).toEqual([])
  })

  it('handles thinking event', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'thinking',
        content: 'Analyzing request...',
      })
    })

    expect(result.current.isThinking).toBe(true)
    expect(result.current.thinkingSteps).toEqual(['Analyzing request...'])
  })

  it('handles background_task_update event', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-1',
        task_type: 'sourcing',
        label: 'Sourcing candidates',
        status: 'running',
        progress: 50,
      })
    })

    expect(result.current.backgroundTasks).toHaveLength(1)
    expect(result.current.backgroundTasks[0]).toEqual({
      task_id: 'bg-1',
      task_type: 'sourcing',
      label: 'Sourcing candidates',
      status: 'running',
      progress: 50,
      message: undefined,
      result: undefined,
    })
  })

  it('clearBackgroundTask removes a specific task', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-1',
        task_type: 'sourcing',
        label: 'Sourcing',
        status: 'completed',
      })
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-2',
        task_type: 'screening',
        label: 'Screening',
        status: 'running',
      })
    })

    expect(result.current.backgroundTasks).toHaveLength(2)

    act(() => {
      result.current.clearBackgroundTask('bg-1')
    })

    expect(result.current.backgroundTasks).toHaveLength(1)
    expect(result.current.backgroundTasks[0].task_id).toBe('bg-2')
  })

  it('handles panel_update event', () => {
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
        panel_type: 'candidate_review',
        panel_data: { candidateId: '123' },
        panel_title: 'Review',
        action: 'open',
      })
    })

    expect(onPanelUpdate).toHaveBeenCalledWith({
      panel_type: 'candidate_review',
      panel_data: { candidateId: '123' },
      panel_title: 'Review',
      action: 'open',
    })
  })

  it('handles plan_progress events', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'plan_progress',
        event: 'plan_started',
        plan_id: 'plan-1',
      })
    })

    expect(result.current.activePlanId).toBe('plan-1')

    act(() => {
      capturedOnEvent?.({
        type: 'plan_progress',
        event: 'step_running',
        task_id: 'task-1',
        action_id: 'a-1',
        domain_id: 'd-1',
      })
    })

    expect(result.current.planProgressSteps).toHaveLength(1)
    expect(result.current.planProgressSteps[0].status).toBe('running')

    act(() => {
      capturedOnEvent?.({
        type: 'plan_progress',
        event: 'step_completed',
        task_id: 'task-1',
        action_id: 'a-1',
        domain_id: 'd-1',
        status: 'completed',
      })
    })

    expect(result.current.planProgressSteps[0].status).toBe('completed')

    act(() => {
      capturedOnEvent?.({
        type: 'plan_progress',
        event: 'plan_completed',
        plan_id: 'plan-1',
      })
    })

    expect(result.current.activePlanId).toBeNull()
  })

  it('sendMessage uses WebSocket when connected', async () => {
    mockIsConnected = true

    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    await act(async () => {
      await result.current.sendMessage('Hello LIA', 'general', 'kanban')
    })

    expect(mockClearTokens).toHaveBeenCalled()
    expect(mockSendMessage).toHaveBeenCalledWith('Hello LIA', { scope: 'kanban' }, 'general')
    expect(mockFetch).not.toHaveBeenCalledWith(
      '/api/backend-proxy/chat/message',
      expect.anything()
    )
  })

  it('sendMessage falls back to fetch when not connected', async () => {
    mockIsConnected = false
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ content: 'LIA response' }),
    })

    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useLiaChatConnection({
        sessionId: 'test-session',
        onMessageComplete: onComplete,
      })
    )

    await act(async () => {
      await result.current.sendMessage('Hello via REST')
    })

    expect(mockSendMessage).not.toHaveBeenCalled()
    expect(onComplete).toHaveBeenCalledWith('LIA response')
  })

  it('initConversation creates a conversation and sets conversationId', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 'conv-123' }),
    })

    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    let convId: string | null = null
    await act(async () => {
      convId = await result.current.initConversation('First message', 'general')
    })

    expect(convId).toBe('conv-123')
    expect(result.current.conversationId).toBe('conv-123')
  })

  it('initConversation returns null on failure', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
    mockFetch.mockResolvedValueOnce({ ok: false })

    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    let convId: string | null = null
    await act(async () => {
      convId = await result.current.initConversation('Hello')
    })

    expect(convId).toBeNull()
    expect(result.current.conversationId).toBeNull()
  })

  it('loadHistory fetches messages and maps them to LiaChatMessage', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          messages: [
            { id: 'm1', role: 'user', content: 'Hello', created_at: '2026-01-01T10:00:00Z' },
            { id: 'm2', role: 'assistant', content: 'Hi!', created_at: '2026-01-01T10:01:00Z' },
          ],
        }),
    })

    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    let history: unknown[] = []
    await act(async () => {
      history = await result.current.loadHistory('conv-123')
    })

    expect(history).toHaveLength(2)
    expect((history[0] as Record<string, unknown>).sender).toBe('user')
    expect((history[1] as Record<string, unknown>).sender).toBe('lia')
  })

  it('loadHistory returns empty array on error', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) })
    mockFetch.mockResolvedValueOnce({ ok: false })

    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    let history: unknown[] = []
    await act(async () => {
      history = await result.current.loadHistory('conv-404')
    })

    expect(history).toEqual([])
  })

  it('resetBackgroundTasks clears all tasks', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-1',
        task_type: 'sourcing',
        label: 'Test',
        status: 'running',
      })
    })

    expect(result.current.backgroundTasks).toHaveLength(1)

    act(() => {
      result.current.resetBackgroundTasks()
    })

    expect(result.current.backgroundTasks).toEqual([])
  })

  it('setConversationId updates the conversation id', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      result.current.setConversationId('new-conv')
    })

    expect(result.current.conversationId).toBe('new-conv')
  })

  it('background task update replaces existing task with same id', () => {
    const { result } = renderHook(() =>
      useLiaChatConnection({ sessionId: 'test-session' })
    )

    act(() => {
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-1',
        task_type: 'sourcing',
        label: 'Sourcing',
        status: 'running',
        progress: 30,
      })
    })

    act(() => {
      capturedOnEvent?.({
        type: 'background_task_update',
        task_id: 'bg-1',
        task_type: 'sourcing',
        label: 'Sourcing',
        status: 'completed',
        progress: 100,
      })
    })

    expect(result.current.backgroundTasks).toHaveLength(1)
    expect(result.current.backgroundTasks[0].status).toBe('completed')
    expect(result.current.backgroundTasks[0].progress).toBe(100)
  })
})
