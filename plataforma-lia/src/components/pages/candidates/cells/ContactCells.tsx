import React from "react"
import { Mail, Phone, Linkedin, Github, Globe } from "lucide-react"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "@/components/pages/candidates/types"

type RevealedContacts = Record<string, { email?: string; phone?: string }>
type OnRevealContact = (candidate: Candidate, type: "email" | "phone") => void
type TranslateFn = (key: string, values?: Record<string, unknown>) => string

export function renderEmailCell(
  candidate: Candidate,
  revealedContacts: RevealedContacts,
  onRevealContact: OnRevealContact,
  t?: TranslateFn
): React.ReactNode {
  const candidateEmail = revealedContacts[candidate.id]?.email || candidate.email
  const canRevealEmail =
    isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) &&
    candidate.has_email !== false

  if (candidateEmail) {
    return <span className="text-xs text-lia-text-primary truncate">{candidateEmail}</span>
  }

  if (canRevealEmail) {
    return (
      <button
        data-testid={`reveal-email-btn-${candidate.id}`}
        onClick={(e) => {
          e.stopPropagation()
          onRevealContact(candidate, "email")
        }}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 text-micro font-medium rounded-full bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active dark:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
        title={t ? t('revealEmailTitle') : "Clique para revelar email (2 créditos)"}
      >
        <Mail className="w-3 h-3" />
        <span>{t ? t('reveal') : "Revelar"}</span>
        <span className="opacity-60">{t ? t('emailCredits') : "(2 cr)"}</span>
      </button>
    )
  }

  return <span className="text-xs text-lia-text-primary">-</span>
}

export function renderPhoneCell(
  candidate: Candidate,
  revealedContacts: RevealedContacts,
  onRevealContact: OnRevealContact,
  fieldKey: "phone" | "mobile_phone" = "phone",
  t?: TranslateFn
): React.ReactNode {
  const candidatePhone =
    revealedContacts[candidate.id]?.phone ||
    (fieldKey === "mobile_phone"
      ? candidate.mobile_phone || candidate.phone
      : candidate.phone)
  const canRevealPhone =
    isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) &&
    candidate.has_phone !== false

  if (candidatePhone) {
    return <span className="text-xs text-lia-text-primary">{candidatePhone}</span>
  }

  if (canRevealPhone) {
    const titleText = t
      ? (fieldKey === "mobile_phone" ? t('revealMobileTitle') : t('revealPhoneTitle'))
      : (fieldKey === "mobile_phone"
        ? "Clique para revelar celular (14 créditos)"
        : "Clique para revelar telefone (14 créditos)")
    return (
      <button
        data-testid={`reveal-phone-btn-${candidate.id}`}
        onClick={(e) => {
          e.stopPropagation()
          onRevealContact(candidate, "phone")
        }}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 text-micro font-medium rounded-full bg-status-success/10 text-status-success hover:bg-status-success/15 transition-colors motion-reduce:transition-none"
        title={titleText}
      >
        <Phone className="w-3 h-3" />
        <span>{t ? t('reveal') : "Revelar"}</span>
        <span className="opacity-60">{t ? t('phoneCredits') : "(14 cr)"}</span>
      </button>
    )
  }

  return <span className="text-xs text-lia-text-primary">-</span>
}

export function renderLinkedinCell(candidate: Candidate, t?: TranslateFn): React.ReactNode {
  return candidate.linkedin_url ? (
    <a
      href={candidate.linkedin_url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center w-6 h-6 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      title={t ? t('viewLinkedIn') : "Ver perfil no LinkedIn"}
    >
      <Linkedin className="w-4 h-4 text-lia-text-secondary" />
    </a>
  ) : (
    <span
      className="inline-flex items-center justify-center w-6 h-6"
      title={t ? t('linkedinNotProvided') : "LinkedIn não informado"}
    >
      <Linkedin className="w-4 h-4 text-lia-text-tertiary" />
    </span>
  )
}

export function renderGithubCell(candidate: Candidate, t?: TranslateFn): React.ReactNode {
  return candidate.github_url ? (
    <a
      href={candidate.github_url}
      target="_blank"
      rel="noopener"
      className="text-lia-text-primary hover:underline text-xs flex items-center gap-1"
    >
      <Github className="w-3 h-3" /> GitHub
    </a>
  ) : (
    <span className="text-xs text-lia-text-primary">{t ? t('na') : "N/A"}</span>
  )
}

export function renderPortfolioCell(candidate: Candidate, t?: TranslateFn): React.ReactNode {
  return candidate.portfolio_url ? (
    <a
      href={candidate.portfolio_url}
      target="_blank"
      rel="noopener"
      className="text-wedo-purple hover:underline text-xs flex items-center gap-1"
    >
      <Globe className="w-3 h-3" /> {t ? t('portfolio') : "Portfólio"}
    </a>
  ) : (
    <span className="text-xs text-lia-text-primary">{t ? t('na') : "N/A"}</span>
  )
}
