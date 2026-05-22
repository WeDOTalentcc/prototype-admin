"use client"

import React, { useState } from"react"
import { useTranslations } from "next-intl"
import { Phone, PhoneCall, Loader2, CheckCircle, MessageSquare } from"lucide-react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from"@/components/ui/dialog"
import {
  textStyles, badgeStyles, buttonStyles
} from"@/lib/design-tokens"

interface VoiceScreeningButtonProps {
  talentPoolId: string
  candidateId: string | number
  candidateName: string
  onScreeningComplete?: () => void
  size?: "sm" | "md"
}

export default function VoiceScreeningButton({
  talentPoolId, candidateId, candidateName, onScreeningComplete, size ="sm",
}: VoiceScreeningButtonProps) {
  const t = useTranslations('agents.voiceScreening')
  const [showDialog, setShowDialog] = useState(false)
  const [channel, setChannel] = useState<"web" |"whatsapp" |"phone">("web")
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
        method:"POST",
        headers: {"Content-Type":"application/json" },
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
        method:"POST",
        headers: {"Content-Type":"application/json" },
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

  const buttonIcon = size ==="sm" ? <Phone className="w-3.5 h-3.5" /> : <Phone className="w-4 h-4 mr-1" />

  return (
    <>
      <button
        onClick={() => setShowDialog(true)}
        className={size ==="sm"
          ?"p-1.5 rounded hover:bg-lia-bg-tertiary text-lia-text-tertiary hover:text-lia-text-secondary transition-colors"
          : `${buttonStyles.outline} text-sm`
        }
        title={t('startVoiceScreening')}
      >
        {buttonIcon}
        {size ==="md" && t('voiceScreeningShort')}
      </button>

      {showDialog && (
        <Dialog open onOpenChange={() => !sessionId && setShowDialog(false)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className={textStyles.h3}>
                {t('voiceScreeningTitle')} — {candidateName}
              </DialogTitle>
            </DialogHeader>

            {!sessionId ? (
              <div className="space-y-4 py-4">
                <p className={textStyles.body}>
                  {t('chooseChannel')}
                </p>
                <div className="space-y-2">
                  {[
                    { id:"web" as const, labelKey:"channelWeb", icon: MessageSquare, descKey:"channelWebDesc" },
                    { id:"whatsapp" as const, labelKey:"channelWhatsapp", icon: Phone, descKey:"channelWhatsappDesc" },
                    { id:"phone" as const, labelKey:"channelPhone", icon: PhoneCall, descKey:"channelPhoneDesc" },
                  ].map(opt => (
                    <label
                      key={opt.id}
                      className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                        channel === opt.id ?"border-lia-text-primary bg-lia-bg-secondary" :"border-lia-border-subtle hover:bg-lia-bg-secondary"
                      }`}
                    >
                      <input
                        type="radio"
                        name="channel"
                        checked={channel === opt.id}
                        onChange={() => setChannel(opt.id)}
                        className="rounded-full border-lia-border-default"
                      />
                      <opt.icon className="w-4 h-4 text-lia-text-tertiary" />
                      <div>
                        <p className={textStyles.body}>{t(opt.labelKey)}</p>
                        <p className={textStyles.caption}>{t(opt.descKey)}</p>
                      </div>
                    </label>
                  ))}
                </div>

                <DialogFooter>
                  <Button className={buttonStyles.secondary} onClick={() => setShowDialog(false)}>
                    {t('cancel')}
                  </Button>
                  <Button className={buttonStyles.primary} onClick={startSession} disabled={isStarting}>
                    {isStarting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Phone className="w-4 h-4 mr-1" />}
                    {isStarting ? t('starting') : t('startScreening')}
                  </Button>
                </DialogFooter>
              </div>
            ) : isDone ? (
              <div className="flex flex-col items-center py-6">
                <CheckCircle className="w-12 h-12 text-green-500 mb-3" />
                <p className={textStyles.h4}>{t('screeningComplete')}</p>
                <p className={`${textStyles.body} mt-1`}>
                  {t('score')}: <strong>{score}/100</strong>
                </p>
                <p className={textStyles.caption}>
                  {t('candidateMovedToScreened')}
                </p>
                <Button className={`${buttonStyles.primary} mt-4`} onClick={() => setShowDialog(false)}>
                  {t('close')}
                </Button>
              </div>
            ) : (
              <div className="space-y-4 py-4">
                <div className="flex items-center gap-2">
                  <Chip variant="neutral" muted className={badgeStyles.warning}>{sessionState}</Chip>
                  <span className={textStyles.caption}>
                    {t('questionProgress', { current: Math.min((progress * 5) + 1, 5).toFixed(0), total: 5 })}
                  </span>
                </div>

                <div className="w-full bg-lia-interactive-active rounded-full h-1.5">
                  <div
                    className="bg-lia-bg-inverse h-1.5 rounded-full transition-colors"
                    style={{ width: `${progress * 100}%` }}
                  />
                </div>

                <div className="bg-lia-bg-secondary rounded-lg p-3">
                  <p className={textStyles.body}>{agentText}</p>
                </div>

                {channel ==="web" && (
                  <TextResponseInput onSubmit={submitTextResponse} />
                )}

                {channel !=="web" && (
                  <p className={textStyles.caption}>
                    {t('awaitingResponse', { channel: channel ==="whatsapp" ?"WhatsApp" : t('phoneLabel') })}
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
  const t = useTranslations('agents.voiceScreening')
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
        placeholder={t('candidateResponsePlaceholder')}
        className="flex-1 border border-lia-border-default rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
        onKeyDown={e => e.key ==="Enter" && handleSubmit()}
      />
      <Button className={buttonStyles.primary} onClick={handleSubmit} disabled={isSending || !text.trim()}>
        {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : t('send')}
      </Button>
    </div>
  )
}
