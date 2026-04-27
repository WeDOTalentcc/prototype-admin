"use client"

import React from "react"
import { ChatContainer } from "@/components/triagem/ChatContainer"
import { ProgressBar } from "@/components/triagem/ProgressBar"
import { MessageBubble } from "@/components/triagem/MessageBubble"
import { TypingIndicator } from "@/components/triagem/TypingIndicator"
import { InputBar } from "@/components/triagem/InputBar"
import type { TriagemMessage, WSIProgress } from "@/components/triagem/types"

const SESSION_ID = "preview-session"
const CANDIDATE_NAME = "Mariana Souza"

const PROGRESS: WSIProgress = {
  currentBlock: 2,
  totalBlocks: 4,
  currentBlockName: "Orientação para resultados",
  questionsAnswered: 9,
  totalQuestions: 20,
  estimatedMinutesRemaining: 4,
}

const NOW = new Date("2026-04-27T14:32:00.000Z")
const ts = (offsetMinutes: number) =>
  new Date(NOW.getTime() - offsetMinutes * 60_000).toISOString()

const MESSAGES: TriagemMessage[] = [
  {
    id: "m1",
    sessionId: SESSION_ID,
    role: "lia",
    type: "text",
    content:
      "Oi, Mariana! Tudo bem? Antes de começarmos, queria entender um pouco do seu contexto atual. **Como tem sido sua atuação no time de Customer Success nos últimos meses?**",
    options: null,
    selectedOption: null,
    likertValue: null,
    likertLabels: null,
    timestamp: ts(8),
    blockIndex: 1,
    blockName: "Contexto profissional",
    audioUrl: null,
  },
  {
    id: "m2",
    sessionId: SESSION_ID,
    role: "candidate",
    type: "text",
    content:
      "Oi, tudo bem! Hoje atendo uma carteira de 32 clientes corporativos no segmento de serviços financeiros. Meu foco tem sido reduzir churn e ampliar a adoção de módulos novos.",
    options: null,
    selectedOption: null,
    likertValue: null,
    likertLabels: null,
    timestamp: ts(7),
    blockIndex: 1,
    blockName: "Contexto profissional",
    audioUrl: null,
  },
  {
    id: "m3",
    sessionId: SESSION_ID,
    role: "lia",
    type: "text",
    content:
      "Ótimo contexto. Pode me contar um caso recente em que você **identificou risco de churn** e o que fez para reverter a situação? Estou interessada nas ações concretas e no resultado.",
    options: null,
    selectedOption: null,
    likertValue: null,
    likertLabels: null,
    timestamp: ts(6),
    blockIndex: 2,
    blockName: "Orientação para resultados",
    audioUrl: null,
  },
  {
    id: "m4",
    sessionId: SESSION_ID,
    role: "candidate",
    type: "text",
    content:
      "Tinha um cliente com queda de 40% no uso semanal. Marquei uma reunião de diagnóstico, descobri que dois usuários-chave tinham saído e desenhei um plano de re-onboarding em 30 dias. No fim do trimestre o uso voltou ao patamar anterior e fechamos a renovação com upsell de um módulo extra.",
    options: null,
    selectedOption: null,
    likertValue: null,
    likertLabels: null,
    timestamp: ts(4),
    blockIndex: 2,
    blockName: "Orientação para resultados",
    audioUrl: null,
  },
  {
    id: "m5",
    sessionId: SESSION_ID,
    role: "lia",
    type: "text",
    content:
      "Bem detalhado, obrigada! Agora me ajude a entender **como você mede sucesso na sua rotina** — quais indicadores você acompanha de perto e com que frequência?",
    options: null,
    selectedOption: null,
    likertValue: null,
    likertLabels: null,
    timestamp: ts(2),
    blockIndex: 2,
    blockName: "Orientação para resultados",
    audioUrl: null,
  },
]

export default function TriagemPreviewChat() {
  const noop = () => {
    // eslint-disable-next-line no-console
    console.log("[triagem preview] chat input acionado")
  }

  return (
    <ChatContainer>
      <ProgressBar progress={PROGRESS} />

      <div
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-label="Mensagens da triagem"
      >
        {MESSAGES.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            candidateName={CANDIDATE_NAME}
          />
        ))}
        <TypingIndicator />
      </div>

      <InputBar
        onSend={noop}
        isSending={false}
        disabled={false}
        audioEnabled={true}
        autoPlayVoice={false}
        onToggleAutoPlayVoice={noop}
      />

      <div className="py-3 px-4 text-center">
        <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
          Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent · Política de Privacidade
        </p>
      </div>
    </ChatContainer>
  )
}
