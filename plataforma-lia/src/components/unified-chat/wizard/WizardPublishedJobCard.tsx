"use client"

import React from "react"
import Link from "next/link"
import { CheckCircle2, ExternalLink, Hash } from "lucide-react"
import type { WizardPublishedJobCardData } from "./wizard-plan-card"

interface Props {
  data: WizardPublishedJobCardData
}

/**
 * WizardPublishedJobCard — non-persisted closing card injected into the
 * chat feed when the "Criar nova vaga" wizard reaches `done`/`handoff`.
 *
 * Shows the recruiter the canonical handoff trio — title, ID and an
 * internal link to the job page — so the wizard's silent unmount is
 * replaced by an explicit "Vaga publicada" confirmation.
 *
 * Tokens follow DS LIA v4.2.1 (no hex colors, no ad-hoc grays). Dark mode
 * inherits from the same CSS variables, so contrast stays WCAG AA.
 */
export function WizardPublishedJobCard({ data }: Props) {
  const { jobId, title, url, shareLink } = data
  const headline = title ?? "Vaga publicada"

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="wizard-published-card"
      className="mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary p-3"
    >
      <div className="flex items-start gap-2.5">
        <div
          className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-status-success/10"
          aria-hidden="true"
        >
          <CheckCircle2 className="h-4 w-4 text-status-success" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium uppercase tracking-wide text-status-success">
            Vaga publicada
          </p>
          <p className="mt-0.5 break-words text-sm font-semibold text-lia-text-primary">
            {headline}
          </p>
          {jobId !== null && (
            <p className="mt-1 inline-flex items-center gap-1 text-[11px] text-lia-text-secondary">
              <Hash className="h-3 w-3" aria-hidden="true" />
              <span>ID {jobId}</span>
            </p>
          )}
        </div>
      </div>

      {(url || shareLink) && (
        <div className="mt-3 flex flex-col gap-1.5">
          {url && (
            <Link
              href={url}
              data-testid="wizard-published-job-link"
              className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-wedo-cyan/10 px-3 py-1.5 text-xs font-medium text-wedo-cyan transition-colors hover:bg-wedo-cyan/20 motion-reduce:transition-none"
            >
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
              Abrir página da vaga
            </Link>
          )}
          {shareLink && (
            <a
              href={shareLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-lia-border-subtle px-3 py-1.5 text-xs text-lia-text-primary transition-colors hover:bg-lia-interactive-hover motion-reduce:transition-none"
            >
              <ExternalLink className="h-3.5 w-3.5 text-lia-text-secondary" aria-hidden="true" />
              Link de compartilhamento
            </a>
          )}
        </div>
      )}
    </div>
  )
}
