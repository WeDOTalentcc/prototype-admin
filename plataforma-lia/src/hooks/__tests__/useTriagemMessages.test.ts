/**
 * Testes — useTriagemMessages (Task #248)
 *
 * Camada 2 (Unitário FE — Vitest + @testing-library/react)
 *
 * Cobre o caminho REST do chat de triagem candidato:
 *  - Optimistic update: mensagem do usuário aparece imediatamente após o
 *    debounce e é substituída pelas respostas do backend (candidate_message
 *    + lia_response) no sucesso.
 *  - Falha de rede (catch): a mensagem otimista é REMOVIDA e um erro
 *    genérico de SERVER_ERROR é setado, permitindo que o usuário tente de
 *    novo sem ver duplicata.
 *  - Retry pelo usuário após falha: novo sendMessage funciona normalmente
 *    (state isSending/erro não fica preso).
 *  - Resposta HTTP de erro (4xx/5xx do backend): mensagem otimista também
 *    é removida e erro mapeado é setado.
 */
import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// fetchWithRetry é importado em useTriagemMessages a partir de
// "./triagem-chat-types" — mocamos esse módulo (re-exportando o resto).
const mockFetchWithRetry = vi.fn()
vi.mock("../chat/triagem-chat-types", async () => {
  const actual = await vi.importActual<typeof import("../chat/triagem-chat-types")>(
    "../chat/triagem-chat-types",
  )
  return {
    ...actual,
    // DEBOUNCE_MS=0 nos testes para não precisar avançar timers em cada caso.
    DEBOUNCE_MS: 0,
    fetchWithRetry: (url: string, options: RequestInit) =>
      mockFetchWithRetry(url, options),
  }
})

import { useTriagemMessages, type UseTriagemMessagesOptions } from "../chat/useTriagemMessages"
import type {
  TriagemMessage,
  TriagemError,
  TriagemPageState,
  TriagemSession,
  WSIProgress,
} from "@/components/triagem/types"

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers({ shouldAdvanceTime: true })
})
afterEach(() => {
  vi.useRealTimers()
})

function makeOptions(): {
  options: UseTriagemMessagesOptions
  state: {
    messages: TriagemMessage[]
    error: TriagemError | null
    pageState: TriagemPageState
    isSending: boolean
    progress: WSIProgress | null
    session: TriagemSession | null
    isLiaTyping: boolean
  }
  setters: {
    setMessages: ReturnType<typeof vi.fn>
    setError: ReturnType<typeof vi.fn>
    setPageState: ReturnType<typeof vi.fn>
    setIsSending: ReturnType<typeof vi.fn>
    setProgress: ReturnType<typeof vi.fn>
    setSession: ReturnType<typeof vi.fn>
    setIsLiaTyping: ReturnType<typeof vi.fn>
  }
} {
  const state = {
    messages: [] as TriagemMessage[],
    error: null as TriagemError | null,
    pageState: "chat" as TriagemPageState,
    isSending: false,
    progress: null as WSIProgress | null,
    session: { id: "sess-1" } as TriagemSession,
    isLiaTyping: false,
  }

  const setMessages = vi.fn((updater: TriagemMessage[] | ((prev: TriagemMessage[]) => TriagemMessage[])) => {
    state.messages = typeof updater === "function" ? updater(state.messages) : updater
  })
  const setError = vi.fn((updater: TriagemError | null | ((prev: TriagemError | null) => TriagemError | null)) => {
    state.error = typeof updater === "function" ? (updater as (p: TriagemError | null) => TriagemError | null)(state.error) : updater
  })
  const setPageState = vi.fn((updater: TriagemPageState | ((prev: TriagemPageState) => TriagemPageState)) => {
    state.pageState = typeof updater === "function" ? (updater as (p: TriagemPageState) => TriagemPageState)(state.pageState) : updater
  })
  const setIsSending = vi.fn((updater: boolean | ((prev: boolean) => boolean)) => {
    state.isSending = typeof updater === "function" ? (updater as (p: boolean) => boolean)(state.isSending) : updater
  })
  const setProgress = vi.fn((updater: WSIProgress | null | ((prev: WSIProgress | null) => WSIProgress | null)) => {
    state.progress = typeof updater === "function" ? (updater as (p: WSIProgress | null) => WSIProgress | null)(state.progress) : updater
  })
  const setSession = vi.fn((updater: TriagemSession | null | ((prev: TriagemSession | null) => TriagemSession | null)) => {
    state.session = typeof updater === "function" ? (updater as (p: TriagemSession | null) => TriagemSession | null)(state.session) : updater
  })
  const setIsLiaTyping = vi.fn((updater: boolean | ((prev: boolean) => boolean)) => {
    state.isLiaTyping = typeof updater === "function" ? (updater as (p: boolean) => boolean)(state.isLiaTyping) : updater
  })

  const options: UseTriagemMessagesOptions = {
    token: "tok-abc",
    pageState: state.pageState,
    setPageState,
    session: state.session,
    setSession,
    config: null,
    messages: state.messages,
    setMessages,
    progress: state.progress,
    setProgress,
    setError,
    setIsLiaTyping,
    mountedRef: { current: true },
    isSending: state.isSending,
    setIsSending,
  }

  return {
    options,
    state,
    setters: { setMessages, setError, setPageState, setIsSending, setProgress, setSession, setIsLiaTyping },
  }
}

describe("useTriagemMessages — sendMessage REST + optimistic update", () => {
  it("sucesso: optimistic message é substituída pelas mensagens do backend", async () => {
    mockFetchWithRetry.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          candidate_message: { id: "m-cand-1", sender: "candidate", content: "Olá" },
          lia_response: { id: "m-lia-1", sender: "lia", content: "Bem-vindo" },
        }),
    })

    const { options, state, setters } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "text", content: "Olá" })
    })

    // Houve pelo menos um setMessages com a optimistic, depois com a real
    expect(setters.setMessages).toHaveBeenCalled()
    expect(state.messages.map((m) => m.id)).toEqual(["m-cand-1", "m-lia-1"])
    // Optimistic id (`temp_…`) não permanece no estado final
    expect(state.messages.some((m) => m.id.startsWith("temp_"))).toBe(false)
    // Erro permanece null
    expect(state.error).toBeNull()
    // Liga e desliga "LIA digitando"
    expect(setters.setIsLiaTyping).toHaveBeenCalledWith(true)
    expect(setters.setIsLiaTyping).toHaveBeenCalledWith(false)
    // isSending reseta
    expect(setters.setIsSending).toHaveBeenLastCalledWith(false)
  })

  it("falha de rede: optimistic é removida e SERVER_ERROR é setado", async () => {
    mockFetchWithRetry.mockRejectedValueOnce(new Error("network down"))

    const { options, state, setters } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "text", content: "Falha" })
    })

    // Houve uma adição (optimistic) e uma remoção depois
    expect(setters.setMessages).toHaveBeenCalledTimes(2)
    expect(state.messages.some((m) => m.id.startsWith("temp_"))).toBe(false)
    expect(state.messages).toHaveLength(0)
    expect(state.error).toEqual({
      code: "SERVER_ERROR",
      message: expect.stringMatching(/Erro ao enviar/i),
    })
    expect(setters.setIsSending).toHaveBeenLastCalledWith(false)
  })

  it("retry pelo usuário após falha: novo send funciona", async () => {
    mockFetchWithRetry.mockRejectedValueOnce(new Error("blip"))
    mockFetchWithRetry.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          candidate_message: { id: "m-cand-2", sender: "candidate", content: "retry" },
          lia_response: { id: "m-lia-2", sender: "lia", content: "ok" },
        }),
    })

    const { options, state } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "text", content: "primeiro" })
    })
    expect(state.error).not.toBeNull()
    expect(state.messages).toHaveLength(0)

    // Segundo envio (retry pelo usuário)
    await act(async () => {
      await result.current.sendMessage({ type: "text", content: "retry" })
    })

    expect(mockFetchWithRetry).toHaveBeenCalledTimes(2)
    expect(state.messages.map((m) => m.id)).toEqual(["m-cand-2", "m-lia-2"])
    // Erro foi limpo no início do segundo envio
    expect(state.error).toBeNull()
  })

  it("audio: lia_response com audio_base64 → mensagem mapeada com audioUrl (blob URL)", async () => {
    // jsdom não implementa URL.createObjectURL — definimos um stub primeiro
    // (vi.spyOn falharia se a propriedade não existisse) e depois espionamos.
    if (typeof URL.createObjectURL !== "function") {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        writable: true,
        value: () => "",
      })
    }
    const createObjectURLSpy = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:mock-audio-url")
    const atobSpy = vi.spyOn(globalThis, "atob")

    // base64 de "hi" = "aGk="
    mockFetchWithRetry.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          candidate_message: {
            id: "m-cand-audio",
            sender: "candidate",
            content: "[áudio]",
            message_type: "audio",
          },
          lia_response: {
            id: "m-lia-audio",
            sender: "lia",
            content: "Resposta em áudio",
            message_type: "audio",
            audio_base64: "aGk=",
          },
        }),
    })

    const { options, state } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "audio", content: "[áudio]", voiceMode: true })
    })

    // Backend foi chamado com message_type=audio e voice_mode=true
    const [, init] = mockFetchWithRetry.mock.calls[0]
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body.message_type).toBe("audio")
    expect(body.voice_mode).toBe(true)

    // Decoder rodou e blob URL foi criado
    expect(atobSpy).toHaveBeenCalledWith("aGk=")
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1)
    const blobArg = createObjectURLSpy.mock.calls[0][0] as Blob
    expect(blobArg).toBeInstanceOf(Blob)
    expect(blobArg.type).toBe("audio/mp3")
    expect(blobArg.size).toBe(2) // "hi" = 2 bytes

    // Estado final: optimistic removido, mensagens reais com áudio
    const liaMsg = state.messages.find((m) => m.id === "m-lia-audio")
    expect(liaMsg?.type).toBe("audio")
    expect(liaMsg?.audioUrl).toBe("blob:mock-audio-url")
    // Mensagem do candidato (sem audio_base64) não deve ter audioUrl
    const candMsg = state.messages.find((m) => m.id === "m-cand-audio")
    expect(candMsg?.audioUrl).toBeNull()

    createObjectURLSpy.mockRestore()
    atobSpy.mockRestore()
  })

  it("audio: base64 inválido → erro de decode é silenciado e audioUrl fica null", async () => {
    if (typeof URL.createObjectURL !== "function") {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        writable: true,
        value: () => "",
      })
    }
    const createObjectURLSpy = vi.spyOn(URL, "createObjectURL")
    // Força atob a falhar (simula payload corrompido).
    const atobSpy = vi.spyOn(globalThis, "atob").mockImplementation(() => {
      throw new Error("InvalidCharacterError")
    })

    mockFetchWithRetry.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          lia_response: {
            id: "m-lia-bad",
            sender: "lia",
            content: "x",
            message_type: "audio",
            audio_base64: "@@@not-base64@@@",
          },
        }),
    })

    const { options, state } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "audio", content: "[áudio]" })
    })

    const liaMsg = state.messages.find((m) => m.id === "m-lia-bad")
    expect(liaMsg).toBeDefined()
    expect(liaMsg?.audioUrl).toBeNull()
    expect(createObjectURLSpy).not.toHaveBeenCalled()

    atobSpy.mockRestore()
    createObjectURLSpy.mockRestore()
  })

  it("response.ok=false (HTTP 4xx) → optimistic removida, erro mapeado", async () => {
    mockFetchWithRetry.mockResolvedValueOnce({
      ok: false,
      status: 410,
      json: () => Promise.resolve({ detail: "expired" }),
    })

    const { options, state } = makeOptions()
    const { result } = renderHook(() => useTriagemMessages(options))

    await act(async () => {
      await result.current.sendMessage({ type: "text", content: "x" })
    })

    expect(state.messages).toHaveLength(0)
    expect(state.error?.code).toBe("TOKEN_EXPIRED")
  })
})
