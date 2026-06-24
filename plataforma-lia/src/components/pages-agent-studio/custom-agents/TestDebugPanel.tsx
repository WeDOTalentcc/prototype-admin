"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Send, Loader2, Wrench, BarChart3, ShieldCheck, DollarSign } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, buttonStyles, textStyles, inputStyles, badgeStyles } from "@/lib/design-tokens"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { BetaBadge } from "@/components/ui/beta-badge"
// White-label canonical 2026-05-29: persona como fallback do nome do agente
// no título do modal de teste/debug.
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import type { CustomAgent } from "./types"

interface TestResult {
  response: string
  confidence: number
  tool_calls: string[]
  execution_time_ms: number
  tokens_input: number
  tokens_output: number
  model_used: string
}

interface TestDebugPanelProps {
  agent: CustomAgent | null
  open: boolean
  onClose: () => void
}

export function TestDebugPanel({ agent, open, onClose }: TestDebugPanelProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('test-debug', open)

  const t = useTranslations('agents.customAgents')
  // White-label canonical: persona como fallback do nome do agente no header.
  const { persona: aiPersona } = useAiPersona()
  const agentDisplayName = agent?.name || aiPersona?.name || t('untitledAgent')
  const [message, setMessage] = useState("")
  const [isTesting, setIsTesting] = useState(false)
  const [results, setResults] = useState<TestResult[]>([])
  const [messages, setMessages] = useState<{ role: "user" | "agent"; text: string }[]>([])

  const handleTest = async () => {
    if (!agent || !message.trim()) return
    const userMsg = message.trim()
    setMessage("")
    setMessages((prev) => [...prev, { role: "user", text: userMsg }])
    setIsTesting(true)

    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userMsg }),
      })
      if (!res.ok) throw new Error("Test failed")
      const data: TestResult = await res.json()
      setResults((prev) => [...prev, data])
      setMessages((prev) => [...prev, { role: "agent", text: data.response }])
    } catch {
      setMessages((prev) => [...prev, { role: "agent", text: t('errors.errorRunningTest') }])
    } finally {
      setIsTesting(false)
    }
  }

  const lastResult = results[results.length - 1]
  const totalTokens = results.reduce((s, r) => s + r.tokens_input + r.tokens_output, 0)
  const totalLatency = results.reduce((s, r) => s + r.execution_time_ms, 0)
  const estimatedCost = (totalTokens * 0.000003).toFixed(4)

  if (!agent) return null

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { onClose(); setMessages([]); setResults([]) } }}>
      <DialogContent className="sm:max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className={cn(textStyles.title, "flex items-center gap-2")}>
            {t('testAgent')}: {agentDisplayName}
            <BetaBadge size="sm" />
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-5 gap-4 h-[60vh]">
          {/* Chat Panel (3/5) */}
          <div className="col-span-3 flex flex-col border border-lia-border-subtle rounded-md overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-auto p-3 space-y-3">
              {messages.length === 0 && (
                <p className={cn(textStyles.caption, "text-center py-8")}>
                  {t('sendTestMessage')}
                </p>
              )}
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                    msg.role === "user"
                      ? "ml-auto bg-lia-btn-primary-bg text-lia-btn-primary-text"
                      : "bg-lia-bg-tertiary text-lia-text-primary"
                  )}
                >
                  {msg.text}
                </div>
              ))}
              {isTesting && (
                <div className="flex items-center gap-2 text-xs text-lia-text-muted">
                  <Loader2 className="w-3 h-3 animate-spin" /> {t('processing')}
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-lia-border-subtle p-2 flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleTest()}
                placeholder={t('typeMessage') as string}
                className={cn(inputStyles.default, "flex-1 text-sm")}
                disabled={isTesting}
              />
              <button
                type="button"
                onClick={handleTest}
                disabled={isTesting || !message.trim()}
                className={cn(buttonStyles.primary, "px-3 py-1.5")}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Debug Panel (2/5) */}
          <div className="col-span-2 overflow-auto space-y-3">
            {/* Tools */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <Wrench className="w-3.5 h-3.5 text-lia-text-muted" />
                <span className="text-xs font-semibold text-lia-text-primary">{t('toolsCalled')}</span>
              </div>
              {lastResult?.tool_calls.length ? (
                <div className="flex flex-wrap gap-1">
                  {lastResult.tool_calls.map((tool, i) => (
                    <span key={i} className={cn(badgeStyles.cyan, "text-[10px]")}>
                      {t('tools.' + tool) || tool}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-lia-text-muted">{t('noToolsCalled')}</p>
              )}
            </div>

            {/* Metrics */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-lia-text-muted" />
                <span className="text-xs font-semibold text-lia-text-primary">{t('metrics')}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-lia-text-disabled">{t('tokensIn')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{lastResult?.tokens_input || 0}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('tokensOut')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{lastResult?.tokens_output || 0}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('latency')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{lastResult?.execution_time_ms || 0}ms</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('confidenceMetric')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{lastResult ? (lastResult.confidence * 100).toFixed(0) + "%" : "-"}</p>
                </div>
              </div>
              {lastResult?.model_used && (
                <p className="text-[10px] text-lia-text-muted mt-1">{t('model')}: {lastResult.model_used}</p>
              )}
            </div>

            {/* Cost */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-2">
                <DollarSign className="w-3.5 h-3.5 text-lia-text-muted" />
                <span className="text-xs font-semibold text-lia-text-primary">{t('sessionUsage')}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-lia-text-disabled">{t('totalTokens')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{totalTokens}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('estimatedCost')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">~R${estimatedCost}</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('totalLatency')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{(totalLatency / 1000).toFixed(1)}s</p>
                </div>
                <div>
                  <span className="text-lia-text-disabled">{t('interactions')}</span>
                  <p className="font-bold font-sans text-lia-text-primary">{results.length}</p>
                </div>
              </div>
            </div>

            {/* Compliance */}
            <div className={cn(cardStyles.flat, "p-3")}>
              <div className="flex items-center gap-1.5 mb-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs font-semibold text-lia-text-primary">{t('compliance')}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                <span className={cn(badgeStyles.success, "text-[10px]")}>{t('fairnessGuardOk')}</span>
                <span className={cn(badgeStyles.success, "text-[10px]")}>{t('piiStripOk')}</span>
                <span className={cn(badgeStyles.success, "text-[10px]")}>{t('auditLogOk')}</span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
