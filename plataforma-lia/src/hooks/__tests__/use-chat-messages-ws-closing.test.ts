/**
 * Task #379 — Garantir que mensagens nunca somem quando o WebSocket está fechando.
 *
 * Cenário coberto:
 *   - O hook acredita estar em modo WS (`isConnected=true`, `transportMode="ws"`),
 *     mas no exato momento do envio o socket entrou em CLOSING/CLOSED. Nesse caso,
 *     `useChatTransport.sendMessage` devolve `false` e o hook precisa reenviar
 *     automaticamente pelo caminho REST — sem deixar o usuário com o spinner
 *     "LIA digitando" preso ou com a mensagem perdida.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useRef } from 'react'

import { useChatMessages } from '../chat/useChatMessages'
import type { HITLPending } from '../chat/lia-chat-connection-types'

type FetchMock = ReturnType<typeof vi.fn>

const ORIGINAL_FETCH = global.fetch

function makeJsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

describe('useChatMessages — WS fechando entre mensagens (Task #379)', () => {
  let fetchMock: FetchMock

  beforeEach(() => {
    fetchMock = vi.fn()
    // Isola do Secret NEXT_PUBLIC_CHAT_TRANSPORT=sse do Replit (Fase C SSE-e2e):
    // sem isso o early-return SSE de useChatMessages pularia o fallback REST
    // (wsSend=false → REST) que este arquivo testa.
    vi.stubEnv('NEXT_PUBLIC_CHAT_TRANSPORT', '')
    global.fetch = fetchMock as unknown as typeof fetch
  })

  afterEach(() => {
    global.fetch = ORIGINAL_FETCH
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
  })

  function renderChatMessages(opts: {
    wsSend: (content: string, ctx: Record<string, unknown>, domain: string) => boolean
    setIsThinking?: React.Dispatch<React.SetStateAction<boolean>>
    onMessageComplete?: (content: string) => void
  }) {
    return renderHook(() => {
      const hitlRef = useRef<HITLPending | null>(null)
      const wsEventTickRef = useRef(0)
      return useChatMessages({
        sessionId: 'sess-379',
        isConnected: true,
        transportMode: 'ws',
        wsSend: opts.wsSend,
        sendRaw: vi.fn(),
        clearTokens: vi.fn(),
        sendMessageViaSSE: vi.fn(),
        wsEventTickRef,
        hitlRef,
        setHitlPending: vi.fn(),
        onMessageComplete: opts.onMessageComplete,
        conversationIdFromWs: null,
        setIsThinking: opts.setIsThinking,
      })
    })
  }

  it('quando wsSend devolve false (socket em CLOSING), cai no REST e entrega a resposta', async () => {
    fetchMock.mockResolvedValueOnce(
      makeJsonResponse({ content: 'Resposta pelo REST', conversation_id: 'conv-1' }),
    )

    const onMessageComplete = vi.fn()
    const wsSend = vi.fn().mockReturnValue(false)

    const { result } = renderChatMessages({ wsSend, onMessageComplete })

    await act(async () => {
      await result.current.sendMessage('oi LIA', 'recruiter_assistant')
    })

    // O caminho WS foi tentado primeiro...
    expect(wsSend).toHaveBeenCalledTimes(1)
    // ...mas como devolveu false, o REST foi acionado em seguida.
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/backend-proxy/chat/message')
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body.message).toBe('oi LIA')
    expect(body.session_id).toBe('sess-379')

    // E a resposta do REST foi entregue ao consumidor — mensagem não some.
    await waitFor(() => {
      expect(onMessageComplete).toHaveBeenCalled()
    })
    // Contrato canonical (PR-D): (content, executionPlan?, extras?). O conteúdo
    // entregue ao consumidor é o 1º argumento — metadata opcional pode seguir.
    expect(onMessageComplete.mock.calls[0][0]).toBe('Resposta pelo REST')
  })

  it('libera o indicador "LIA digitando" mesmo após o fallback REST', async () => {
    fetchMock.mockResolvedValueOnce(
      makeJsonResponse({ content: 'pronto', conversation_id: 'conv-2' }),
    )

    const thinkingHistory: boolean[] = []
    const setIsThinking = vi.fn((v: boolean) => {
      thinkingHistory.push(v)
    })
    const wsSend = vi.fn().mockReturnValue(false)

    const { result } = renderChatMessages({ wsSend, setIsThinking })

    await act(async () => {
      await result.current.sendMessage('teste', 'recruiter_assistant')
    })

    // Acendeu o spinner ao iniciar o envio e apagou ao final do REST —
    // sem isso o "LIA digitando" ficaria preso para sempre.
    expect(thinkingHistory[0]).toBe(true)
    expect(thinkingHistory[thinkingHistory.length - 1]).toBe(false)
  })

  it('mostra mensagem amigável quando o REST de fallback também falha', async () => {
    fetchMock.mockRejectedValueOnce(new Error('network down'))

    const onMessageComplete = vi.fn()
    const wsSend = vi.fn().mockReturnValue(false)
    const setIsThinking = vi.fn()

    const { result } = renderChatMessages({ wsSend, onMessageComplete, setIsThinking })

    await act(async () => {
      await result.current.sendMessage('alguém aí?', 'recruiter_assistant')
    })

    expect(wsSend).toHaveBeenCalledTimes(1)
    await waitFor(() => {
      expect(onMessageComplete).toHaveBeenCalledWith(
        expect.stringContaining('Erro ao conectar'),
      )
    })
    // Spinner sempre desliga, mesmo no cenário de erro.
    expect(setIsThinking).toHaveBeenLastCalledWith(false)
  })
})
