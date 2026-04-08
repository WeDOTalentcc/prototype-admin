"use client"

import React, { useState } from "react"
import { Phone, PhoneCall, Loader2, CheckCircle, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import {
  textStyles, badgeStyles, buttonStyles
} from "@/lib/design-tokens"

/**
 * VoiceScreeningButton — initiates voice screening for a candidate in a talent pool.
 *
 * Shows in the candidate table actions column when candidate is in "contacted" stage.
 * Opens a channel selection dialog, creates a session, and tracks progress.
 *
 * Usage in TalentPoolPage candidate table:
 *   {tpc.stage === "contacted" && (
 *     <VoiceScreeningButton
 *       talentPoolId={poolId}
 *       candidateId={tpc.candidate.id}
 *       candidateName={tpc.candidate.name}
 *       onScreeningComplete={() => loadCandidates()}
 *     />
 *   )}
 */

interface VoiceScreeningButtonProps {
  talentPoolId: string
  candidateId: string | number
  candidateName: string
  onScreeningComplete?: () => void
  size?: "sm" | "md"
}

export default function VoiceScreeningButton({
  talentPoolId, candidateId, candidateName, onScreeningComplete, size = "sm",
}: VoiceScreeningButtonProps) {
  const [showDialog, setShowDialog] = useState(false)
  const [channel, setChannel] = useState<"web" | "whatsapp" | "phone">("web")
  const [isStarting, setIsStarting] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionState, setSessionState] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [agentText, setAgentText] = useState("")
  const [isDone, setIsDone] = useState(false)
  const [score, setScore] = useState<number | null>(null)

  const startSession = async () => {
    setIsStarting(true)
    try {
      const res = await fetch("/api/backend-proxy/voice-screening/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          talent_pool_id: talentPoolId,
          candidate_id: String(candidateId),
          candidate_name: candidateName,
          channel,
        }),
      })
      const data = await res.json()
      setSessionId(data.session_id)
      setSessionState(data.state)
      setProgress(data.progress)
      setAgentText(data.agent_text)
    } catch (err) {
      console.error("Failed to start voice session:", err)
    } finally {
      setIsStarting(false)
    }
  }

  const submitTextResponse = async (text: string) => {
    if (!sessionId || !text.trim()) return
    try {
      const res = await fetch(`/api/backend-proxy/voice-screening/sessions/${sessionId}/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      setSessionState(data.state)
      setProgress(data.progress)
      setAgentText(data.agent_text)
      setIsDone(data.is_done)
      setScore(data.score)

      if (data.is_done) {
        onScreeningComplete?.()
      }
    } catch (err) {
      console.error("Failed to submit response:", err)
    }
  }

  const buttonIcon = size === "sm" ? <Phone className="w-3.5 h-3.5" /> : <Phone className="w-4 h-4 mr-1" />

  return (
    <>
      <button
        onClick={() => setShowDialog(true)}
        className={size === "sm"
          ? "p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          : `${buttonStyles.outline} text-sm`
        }
        title="Iniciar triagem por voz"
      >
        {buttonIcon}
        {size === "md" && "Triagem Voz"}
      </button>

      {showDialog && (
        <Dialog open onOpenChange={() => !sessionId && setShowDialog(false)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className={textStyles.h3}>
                Triagem por Voz — {candidateName}
              </DialogTitle>
            </DialogHeader>

            {!sessionId ? (
              /* Channel selection */
              <div className="space-y-4 py-4">
                <p className={textStyles.body}>
                  Escolha o canal para a triagem por voz:
                </p>
                <div className="space-y-2">
                  {[
                    { id: "web" as const, label: "Chat Web", icon: MessageSquare, desc: "Candidato responde pelo navegador" },
                    { id: "whatsapp" as const, label: "WhatsApp", icon: Phone, desc: "LIA envia perguntas por WhatsApp" },
                    { id: "phone" as const, label: "Ligação", icon: PhoneCall, desc: "LIA liga para o candidato" },
                  ].map(opt => (
                    <label
                      key={opt.id}
                      className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                        channel === opt.id ? "border-gray-900 bg-gray-50" : "border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      <input
                        type="radio"
                        name="channel"
                        checked={channel === opt.id}
                        onChange={() => setChannel(opt.id)}
                        className="rounded-full border-gray-300"
                      />
                      <opt.icon className="w-4 h-4 text-gray-500" />
                      <div>
                        <p className={textStyles.body}>{opt.label}</p>
                        <p className={textStyles.caption}>{opt.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>

                <DialogFooter>
                  <Button className={buttonStyles.secondary} onClick={() => setShowDialog(false)}>
                    Cancelar
                  </Button>
                  <Button className={buttonStyles.primary} onClick={startSession} disabled={isStarting}>
                    {isStarting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Phone className="w-4 h-4 mr-1" />}
                    {isStarting ? "Iniciando..." : "Iniciar Triagem"}
                  </Button>
                </DialogFooter>
              </div>
            ) : isDone ? (
              /* Completion */
              <div className="flex flex-col items-center py-6">
                <CheckCircle className="w-12 h-12 text-green-500 mb-3" />
                <p className={textStyles.h4}>Triagem concluída!</p>
                <p className={`${textStyles.body} mt-1`}>
                  Score: <strong>{score}/100</strong>
                </p>
                <p className={textStyles.caption}>
                  Candidato movido para "Triado" no pool.
                </p>
                <Button className={`${buttonStyles.primary} mt-4`} onClick={() => setShowDialog(false)}>
                  Fechar
                </Button>
              </div>
            ) : (
              /* In-progress (text fallback for web channel) */
              <div className="space-y-4 py-4">
                <div className="flex items-center gap-2">
                  <Badge className={badgeStyles.warning}>{sessionState}</Badge>
                  <span className={textStyles.caption}>
                    Pergunta {Math.min((progress * 5) + 1, 5).toFixed(0)}/5
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-gray-900 h-1.5 rounded-full transition-all"
                    style={{ width: `${progress * 100}%` }}
                  />
                </div>

                {/* Agent text */}
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className={textStyles.body}>{agentText}</p>
                </div>

                {/* Text input (web channel fallback) */}
                {channel === "web" && (
                  <TextResponseInput onSubmit={submitTextResponse} />
                )}

                {/* For whatsapp/phone: just show status */}
                {channel !== "web" && (
                  <p className={textStyles.caption}>
                    Aguardando resposta do candidato via {channel === "whatsapp" ? "WhatsApp" : "telefone"}...
                  </p>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

function TextResponseInput({ onSubmit }: { onSubmit: (text: string) => void }) {
  const [text, setText] = useState("")
  const [isSending, setIsSending] = useState(false)

  const handleSubmit = async () => {
    if (!text.trim()) return
    setIsSending(true)
    await onSubmit(text.trim())
    setText("")
    setIsSending(false)
  }

  return (
    <div className="flex gap-2">
      <input
        type="text"
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Resposta do candidato..."
        className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
        onKeyDown={e => e.key === "Enter" && handleSubmit()}
      />
      <Button className={buttonStyles.primary} onClick={handleSubmit} disabled={isSending || !text.trim()}>
        {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Enviar"}
      </Button>
    </div>
  )
}
