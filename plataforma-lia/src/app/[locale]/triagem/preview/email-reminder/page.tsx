"use client"

import React, { useEffect, useState } from "react"
import { useLocale } from "next-intl"
import { getPreviewTemplate } from "@/data/screening-email-templates"
import { sanitizeEmailHtml } from "@/lib/sanitize"

const PREVIEW_VARS_PT: Record<string, string> = {
  candidate_name: "Mariana Souza",
  job_title: "Analista de Customer Success Pleno",
  company_name: "Lumina Tecnologia",
  screening_link: "https://app.wedotalent.com.br/pt/triagem/preview-token-mariana",
  recruiter_name: "Camila Ribeiro",
}

const PREVIEW_VARS_EN: Record<string, string> = {
  candidate_name: "Mary Smith",
  job_title: "Mid-Level Customer Success Analyst",
  company_name: "Lumina Tech",
  screening_link: "https://app.wedotalent.com/en/triagem/preview-token-mary",
  recruiter_name: "Camille Rivers",
}

type EnvelopeCopy = {
  inbox: string
  from: string
  to: string
  date: string
  loading: string
  staticPreview: (templateName: string) => string
  notFound: string
  emailFrom: string
  emailTo: string
  emailDate: string
}

const COPY: Record<"pt" | "en", EnvelopeCopy> = {
  pt: {
    inbox: "Caixa de entrada",
    from: "De:",
    to: "Para:",
    date: "Data:",
    loading: "Carregando email...",
    staticPreview: (name) =>
      `Visualização estática do template "${name}" — apenas para captura de tela.`,
    notFound: 'Template "tpl-voice-screening-reminder" não encontrado.',
    emailFrom: "Camila Ribeiro <camila.ribeiro@luminatec.com.br>",
    emailTo: "mariana.souza@email.com",
    emailDate: "28 de abril de 2026, 09:15",
  },
  en: {
    inbox: "Inbox",
    from: "From:",
    to: "To:",
    date: "Date:",
    loading: "Loading email...",
    staticPreview: (name) =>
      `Static preview of the "${name}" template — for screenshots only.`,
    notFound: 'Template "tpl-voice-screening-reminder" not found.',
    emailFrom: "Camille Rivers <camille.rivers@luminatech.com>",
    emailTo: "mary.smith@example.com",
    emailDate: "April 28, 2026, 9:15 AM",
  },
}

function fillTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{\s*([\w_]+)\s*\}\}/g, (_match, key: string) => {
    return vars[key] ?? ""
  })
}

export default function TriagemPreviewEmailReminder() {
  const locale = useLocale()
  const isEn = locale === "en"
  const copy = isEn ? COPY.en : COPY.pt
  const previewVars = isEn ? PREVIEW_VARS_EN : PREVIEW_VARS_PT

  const template = getPreviewTemplate("tpl-voice-screening-reminder", locale)

  const [safeBody, setSafeBody] = useState<string | null>(null)

  useEffect(() => {
    if (!template) return
    const filled = fillTemplate(template.body, previewVars)
    setSafeBody(sanitizeEmailHtml(filled))
  }, [template, previewVars])

  if (!template) {
    return (
      <main className="min-h-screen bg-gray-100 px-4 py-10">
        <p className="text-center text-sm text-gray-700">{copy.notFound}</p>
      </main>
    )
  }

  const subject = fillTemplate(template.subject, previewVars)

  return (
    <main className="min-h-screen bg-gray-100 px-4 py-10">
      <div className="mx-auto bg-white shadow-md rounded-lg overflow-hidden" style={{ maxWidth: 600 }}>
        <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
            {copy.inbox}
          </div>
          <h1 className="text-base font-semibold text-gray-900 leading-snug mb-3">
            {subject}
          </h1>
          <dl className="text-xs text-gray-600 space-y-1">
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">{copy.from}</dt>
              <dd>{copy.emailFrom}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">{copy.to}</dt>
              <dd>{copy.emailTo}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">{copy.date}</dt>
              <dd>{copy.emailDate}</dd>
            </div>
          </dl>
        </div>

        <div className="px-6 py-6 text-sm" suppressHydrationWarning>
          {safeBody === null ? (
            <p className="text-gray-400 text-sm">{copy.loading}</p>
          ) : (
            <div dangerouslySetInnerHTML={{ __html: safeBody }} />
          )}
        </div>
      </div>

      <p className="text-center text-xs text-gray-500 mt-6">
        {copy.staticPreview(template.name)}
      </p>
    </main>
  )
}
