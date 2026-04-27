"use client"

import React, { useState } from "react"
import { ChatContainer } from "@/components/triagem/ChatContainer"
import { WelcomeCard } from "@/components/triagem/WelcomeCard"
import { PhoneConfirmModal } from "@/components/triagem/PhoneConfirmModal"
import type { TriagemConfig } from "@/components/triagem/types"

const PREVIEW_CONFIG: TriagemConfig = {
  companyName: "Lumina Tecnologia",
  companyLogoUrl: null,
  jobTitle: "Analista de Customer Success Pleno",
  candidateName: "Mariana",
  estimatedMinutes: 7,
  privacyPolicyUrl: "/privacidade",
  audioEnabled: true,
  feedbackEnabled: true,
  welcomeMessage:
    "Vou conduzir uma conversa rápida sobre sua experiência com clientes, retenção e indicadores de sucesso. Suas respostas serão analisadas de forma justa e objetiva.",
  voiceMode: false,
  jobDescription:
    "Atuação no acompanhamento da carteira de clientes corporativos, garantindo adoção do produto, renovação de contratos e expansão de receita. Trabalho próximo aos times de Vendas, Produto e Suporte.",
  location: "São Paulo, SP",
  workModel: "híbrido",
  salaryRange: { min: 7500, max: 10500, currency: "BRL" },
  benefits: [
    "Vale-refeição",
    "Plano de saúde",
    "Plano odontológico",
    "Auxílio home office",
    "Gympass",
  ],
  showSalary: true,
  showBenefits: true,
  chatWebEnabled: true,
  whatsappEnabled: true,
  phoneEnabled: true,
  voiceWebEnabled: true,
  candidatePhone: "+55 11 91234-5678",
}

export default function TriagemPreviewWelcome() {
  const [phoneModalOpen, setPhoneModalOpen] = useState(false)
  const [whatsappModalOpen, setWhatsappModalOpen] = useState(false)

  const noop = (label: string) => () => {
    // eslint-disable-next-line no-console
    console.log(`[triagem preview] ${label}`)
  }

  return (
    <ChatContainer>
      <div className="flex-1 flex flex-col">
        <WelcomeCard
          config={PREVIEW_CONFIG}
          onStart={noop("onStart")}
          onRequestCall={() => setPhoneModalOpen(true)}
          onRequestWhatsapp={() => setWhatsappModalOpen(true)}
          isStarting={false}
        />
      </div>

      <PhoneConfirmModal
        open={phoneModalOpen}
        onClose={() => setPhoneModalOpen(false)}
        onConfirm={async () => setPhoneModalOpen(false)}
        initialPhone={PREVIEW_CONFIG.candidatePhone ?? null}
      />
      <PhoneConfirmModal
        mode="whatsapp"
        open={whatsappModalOpen}
        onClose={() => setWhatsappModalOpen(false)}
        onConfirm={async () => setWhatsappModalOpen(false)}
        initialPhone={PREVIEW_CONFIG.candidatePhone ?? null}
      />

      <div className="py-3 px-4 text-center">
        <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
          Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent · Política de Privacidade
        </p>
      </div>
    </ChatContainer>
  )
}
