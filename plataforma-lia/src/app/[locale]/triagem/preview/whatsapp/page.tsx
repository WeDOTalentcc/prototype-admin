"use client"

import React, { useEffect, useState } from "react"
import { useLocale } from "next-intl"
import { getPreviewTemplate } from "@/data/screening-email-templates"
import { sanitizeEmailHtml } from "@/lib/sanitize"

const PREVIEW_VARS_PT: Record<string, string> = {
  candidate_name: "Mariana Souza",
  job_title: "Analista de Customer Success Pleno",
}

const PREVIEW_VARS_EN: Record<string, string> = {
  candidate_name: "Mary Smith",
  job_title: "Mid-Level Customer Success Analyst",
}

type WhatsAppCopy = {
  contactName: string
  candidatePhone: string
  presence: string
  loading: string
  staticPreview: (templateName: string) => string
  notFound: string
}

const COPY: Record<"pt" | "en", WhatsAppCopy> = {
  pt: {
    contactName: "IA · Lumina Tecnologia",
    candidatePhone: "+55 11 98765-4321",
    presence: "online",
    loading: "Carregando mensagem...",
    staticPreview: (name) =>
      `Visualização estática do template "${name}" — apenas para captura de tela.`,
    notFound: 'Template "tpl-screening-complete-whatsapp" não encontrado.',
  },
  en: {
    contactName: "IA · Lumina Tech",
    candidatePhone: "+1 415 555 0142",
    presence: "online",
    loading: "Loading message...",
    staticPreview: (name) =>
      `Static preview of the "${name}" template — for screenshots only.`,
    notFound: 'Template "tpl-screening-complete-whatsapp" not found.',
  },
}

const MESSAGE_TIME = "14:32"

function fillTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{\s*([\w_]+)\s*\}\}/g, (_match, key: string) => {
    return vars[key] ?? ""
  })
}

function whatsappToHtml(text: string): string {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
  const withBold = escaped.replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>")
  return withBold.replace(/\n/g, "<br/>")
}

export default function TriagemPreviewWhatsapp() {
  const locale = useLocale()
  const isEn = locale === "en"
  const copy = isEn ? COPY.en : COPY.pt
  const previewVars = isEn ? PREVIEW_VARS_EN : PREVIEW_VARS_PT

  const template = getPreviewTemplate("tpl-screening-complete-whatsapp", locale)

  const [safeBody, setSafeBody] = useState<string | null>(null)

  useEffect(() => {
    if (!template) return
    const filled = fillTemplate(template.body, previewVars)
    const asHtml = whatsappToHtml(filled)
    setSafeBody(sanitizeEmailHtml(asHtml))
  }, [template, previewVars])

  if (!template) {
    return (
      <main className="min-h-screen bg-gray-100 px-4 py-10">
        <p className="text-center text-sm text-gray-700">{copy.notFound}</p>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-100 px-4 py-10">
      <div
        className="mx-auto rounded-2xl overflow-hidden shadow-md border border-gray-200"
        style={{ maxWidth: 380 }}
      >
        <div className="bg-[#075E54] text-white px-4 py-3 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#128C7E] flex items-center justify-center text-base font-semibold flex-shrink-0">
            L
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold leading-tight truncate">
              {copy.contactName}
            </div>
            <div className="text-[11px] text-white/75 leading-tight truncate">
              {copy.candidatePhone} · {copy.presence}
            </div>
          </div>
        </div>

        <div
          className="px-3 py-4"
          style={{ backgroundColor: "#ECE5DD", minHeight: 360 }}
        >
          <div className="flex justify-start">
            <div
              className="bg-white rounded-lg rounded-tl-none px-3 py-2 text-sm text-gray-800 shadow-sm"
              style={{ maxWidth: "85%" }}
            >
              <div suppressHydrationWarning>
                {safeBody === null ? (
                  <span className="text-gray-400">{copy.loading}</span>
                ) : (
                  <div
                    className="leading-relaxed whitespace-pre-wrap break-words"
                    dangerouslySetInnerHTML={{ __html: safeBody }}
                  />
                )}
              </div>
              <div className="text-[10px] text-gray-400 text-right mt-1">
                {MESSAGE_TIME}
              </div>
            </div>
          </div>
        </div>
      </div>

      <p className="text-center text-xs text-gray-500 mt-6">
        {copy.staticPreview(template.name)}
      </p>
    </main>
  )
}
