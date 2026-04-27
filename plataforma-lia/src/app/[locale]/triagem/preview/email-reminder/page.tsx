"use client"

import React, { useEffect, useState } from "react"
import { screeningDefaultTemplates } from "@/data/screening-email-templates"
import { sanitizeEmailHtml } from "@/lib/sanitize"

const PREVIEW_VARS: Record<string, string> = {
  candidate_name: "Mariana Souza",
  job_title: "Analista de Customer Success Pleno",
  company_name: "Lumina Tecnologia",
  screening_link: "https://app.wedotalent.com.br/pt/triagem/preview-token-mariana",
  recruiter_name: "Camila Ribeiro",
}

function fillTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{\s*([\w_]+)\s*\}\}/g, (_match, key: string) => {
    return vars[key] ?? ""
  })
}

const EMAIL_FROM = "Camila Ribeiro <camila.ribeiro@luminatec.com.br>"
const EMAIL_TO = "mariana.souza@email.com"
const EMAIL_DATE = "28 de abril de 2026, 09:15"

export default function TriagemPreviewEmailReminder() {
  const template = screeningDefaultTemplates.find(
    (t) => t.id === "tpl-voice-screening-reminder"
  )

  const [safeBody, setSafeBody] = useState<string | null>(null)

  useEffect(() => {
    if (!template) return
    const filled = fillTemplate(template.body, PREVIEW_VARS)
    setSafeBody(sanitizeEmailHtml(filled))
  }, [template])

  if (!template) {
    return (
      <main className="min-h-screen bg-gray-100 px-4 py-10">
        <p className="text-center text-sm text-gray-700">
          Template &quot;tpl-voice-screening-reminder&quot; não encontrado.
        </p>
      </main>
    )
  }

  const subject = fillTemplate(template.subject, PREVIEW_VARS)

  return (
    <main className="min-h-screen bg-gray-100 px-4 py-10">
      <div className="mx-auto bg-white shadow-md rounded-lg overflow-hidden" style={{ maxWidth: 600 }}>
        <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
            Caixa de entrada
          </div>
          <h1 className="text-base font-semibold text-gray-900 leading-snug mb-3">
            {subject}
          </h1>
          <dl className="text-xs text-gray-600 space-y-1">
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">De:</dt>
              <dd>{EMAIL_FROM}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">Para:</dt>
              <dd>{EMAIL_TO}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-gray-700 w-16 flex-shrink-0">Data:</dt>
              <dd>{EMAIL_DATE}</dd>
            </div>
          </dl>
        </div>

        <div className="px-6 py-6 text-sm" suppressHydrationWarning>
          {safeBody === null ? (
            <p className="text-gray-400 text-sm">Carregando email...</p>
          ) : (
            <div dangerouslySetInnerHTML={{ __html: safeBody }} />
          )}
        </div>
      </div>

      <p className="text-center text-xs text-gray-500 mt-6">
        Visualização estática do template &quot;{template.name}&quot; — apenas para captura de tela.
      </p>
    </main>
  )
}
