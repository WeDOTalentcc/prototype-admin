"use client"

import React, { useState } from "react"
import { useLocale } from "next-intl"
import { ChatContainer } from "@/components/triagem/ChatContainer"
import { WelcomeCard } from "@/components/triagem/WelcomeCard"
import { PhoneConfirmModal } from "@/components/triagem/PhoneConfirmModal"
import type { TriagemConfig } from "@/components/triagem/types"

const PREVIEW_CONFIG_PT: TriagemConfig = {
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

const PREVIEW_CONFIG_EN: TriagemConfig = {
  companyName: "Lumina Tech",
  companyLogoUrl: null,
  jobTitle: "Mid-Level Customer Success Analyst",
  candidateName: "Mary",
  estimatedMinutes: 7,
  privacyPolicyUrl: "/privacy",
  audioEnabled: true,
  feedbackEnabled: true,
  welcomeMessage:
    "I'll guide you through a quick conversation about your experience with customers, retention and success metrics. Your answers will be analysed fairly and objectively.",
  voiceMode: false,
  jobDescription:
    "Owning the relationship with our corporate customer portfolio, driving product adoption, contract renewals and revenue expansion. Working closely with the Sales, Product and Support teams.",
  location: "Remote (US)",
  workModel: "remoto",
  salaryRange: { min: 70000, max: 95000, currency: "USD" },
  benefits: [
    "Health insurance",
    "Dental plan",
    "Home office stipend",
    "Wellness allowance",
    "Annual learning budget",
  ],
  showSalary: true,
  showBenefits: true,
  chatWebEnabled: true,
  whatsappEnabled: true,
  phoneEnabled: true,
  voiceWebEnabled: true,
  candidatePhone: "+55 11 91234-5678",
}

const FOOTER_COPY = {
  pt: "Política de Privacidade",
  en: "Privacy Policy",
}

export default function TriagemPreviewWelcome() {
  const locale = useLocale()
  const isEn = locale === "en"
  const config = isEn ? PREVIEW_CONFIG_EN : PREVIEW_CONFIG_PT

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
          config={config}
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
        initialPhone={config.candidatePhone ?? null}
      />
      <PhoneConfirmModal
        mode="whatsapp"
        open={whatsappModalOpen}
        onClose={() => setWhatsappModalOpen(false)}
        onConfirm={async () => setWhatsappModalOpen(false)}
        initialPhone={config.candidatePhone ?? null}
      />

      <div className="py-3 px-4 text-center">
        <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
          Powered by WeDoTalent · {isEn ? FOOTER_COPY.en : FOOTER_COPY.pt}
        </p>
      </div>
    </ChatContainer>
  )
}
