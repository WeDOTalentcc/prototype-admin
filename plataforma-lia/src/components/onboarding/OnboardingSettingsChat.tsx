"use client"

import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"

interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

interface UIAction {
  type: string
  actionId?: string
  section?: string
}

interface ChatResponse {
  message: string
  is_complete: boolean
  progress_percent: number
  ui_action?: UIAction | null
}

interface Props {
  userId: number
}

export function OnboardingSettingsChat({ userId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: text }])
    setLoading(true)

    try {
      const resp = await fetch(`/api/backend-proxy/onboarding/${userId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: text }),
      })

      if (!resp.ok) throw new Error("chat_request_failed")

      const data: ChatResponse = await resp.json()
      setMessages((prev) => [...prev, { role: "assistant", content: data.message }])

      if (data.ui_action?.type === "settings_saved" && data.ui_action.actionId) {
        window.dispatchEvent(
          new CustomEvent("lia:settings-success", {
            detail: { actionId: data.ui_action.actionId },
          }),
        )
      }

      if (data.ui_action?.type === "settings_complete") {
        window.dispatchEvent(
          new CustomEvent("lia:settings-success", { detail: { actionId: "complete" } }),
        )
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Algo deu errado. Por favor, tente novamente." },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="flex flex-col h-full bg-lia-bg-primary">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center pt-12">
            <p className="text-sm text-lia-text-secondary">
              Olá! Vou ajudar você a configurar sua empresa via chat.
            </p>
            <p className="text-xs text-lia-text-muted mt-1">
              Responda as perguntas e as informações serão salvas automaticamente.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-gray-900 text-white"
                  : "bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-lia-bg-secondary border border-lia-border-subtle px-3 py-2.5 rounded-xl">
              <span className="text-xs text-lia-text-secondary animate-pulse motion-reduce:animate-none" aria-hidden="true">Pensando…</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="flex-shrink-0 p-3 border-t border-lia-border-subtle bg-lia-bg-secondary">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            placeholder="Digite sua resposta..."
            disabled={loading}
            className="flex-1 px-3 py-2 text-sm bg-lia-bg-primary rounded-lg border border-lia-border-subtle placeholder:text-lia-text-disabled focus:outline-none focus:border-wedo-cyan transition-colors"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="p-2 bg-gray-900 text-white rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors"
            aria-label="Enviar mensagem"
          >
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
