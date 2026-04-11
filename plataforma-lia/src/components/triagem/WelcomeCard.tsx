"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Clock, Shield, CheckSquare, Square, MapPin, Briefcase, DollarSign, Gift, Phone } from "lucide-react"
import type { TriagemConfig } from "@/components/triagem/types"

interface WelcomeCardProps {
  config: TriagemConfig
  onStart: (voiceMode?: boolean) => void
  onRequestCall?: () => void
  isStarting?: boolean
  className?: string
}

function formatSalary(range: { min?: number; max?: number; currency?: string }): string {
  const currency = range.currency || "BRL"
  const fmt = (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency, minimumFractionDigits: 0, maximumFractionDigits: 0 })
  if (range.min && range.max) return `${fmt(range.min)} - ${fmt(range.max)}`
  if (range.min) return `A partir de ${fmt(range.min)}`
  if (range.max) return `Até ${fmt(range.max)}`
  return ""
}

const WORK_MODEL_LABELS: Record<string, string> = {
  remoto: "Remoto",
  "híbrido": "Híbrido",
  presencial: "Presencial",
}

export function WelcomeCard({ config, onStart, onRequestCall, isStarting = false, className }: WelcomeCardProps) {
  const [consentChecked, setConsentChecked] = useState(false)

  const hasJobDetails = config.jobDescription || config.location || config.workModel
  const hasSalary = config.showSalary && config.salaryRange && (config.salaryRange.min || config.salaryRange.max)
  const hasBenefits = config.showBenefits && config.benefits && config.benefits.length > 0

  return (
    <div
      className={cn(
        "flex-1 flex items-center justify-center px-4 py-8",
        className
      )}
    >
      <div className="w-full max-w-md bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-6 space-y-5">
        <div className="flex flex-col items-center gap-4 text-center">
          {config.companyLogoUrl ? (
            <img
              src={config.companyLogoUrl}
              alt={`Logo ${config.companyName}`}
              className="h-12 object-contain"
            />
          ) : (
            <div className="h-12 px-4 flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg">
              <span className="text-sm font-semibold text-lia-text-secondary">
                {config.companyName}
              </span>
            </div>
          )}

          <h1 className="text-lg font-semibold text-lia-text-primary">
            {config.jobTitle}
          </h1>
        </div>

        {hasJobDetails && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-lia-text-tertiary">
            {config.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                {config.location}
              </span>
            )}
            {config.workModel && (
              <span className="flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 flex-shrink-0" />
                {WORK_MODEL_LABELS[config.workModel] || config.workModel}
              </span>
            )}
          </div>
        )}

        {config.jobDescription && (
          <p className="text-sm text-lia-text-secondary leading-relaxed line-clamp-4">
            {config.jobDescription}
          </p>
        )}

        {(hasSalary || hasBenefits) && (
          <div className="space-y-2">
            {hasSalary && config.salaryRange && (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                <DollarSign className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{formatSalary(config.salaryRange)}</span>
              </div>
            )}
            {hasBenefits && config.benefits && (
              <div className="flex items-start gap-2 text-xs text-lia-text-tertiary">
                <Gift className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{config.benefits.join(" · ")}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex items-start gap-3 p-4 bg-wedo-cyan/10 dark:bg-wedo-cyan/15 rounded-lg">
          <LIAIcon size="sm" className="flex-shrink-0 bg-wedo-cyan/10" />
          <div className="text-sm text-lia-text-secondary leading-relaxed">
            <p className="font-semibold text-lia-text-primary mb-1">
              Olá, {config.candidateName}. Eu sou a LIA.
            </p>
            <p>{config.welcomeMessage || "Vou conduzir sua triagem para esta vaga. A conversa abordará sua experiência e habilidades de forma objetiva."}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
          <Clock className="w-3.5 h-3.5" />
          <span>
            Tempo estimado:{" "}
            <span className="font-['Inter',sans-serif] font-medium">~{config.estimatedMinutes}</span> minutos
          </span>
        </div>

        <label
          className="flex items-start gap-3 cursor-pointer group"
          htmlFor="lgpd-consent"
        >
          <button
            type="button"
            id="lgpd-consent"
            role="checkbox"
            aria-checked={consentChecked}
            onClick={() => setConsentChecked(!consentChecked)}
            className="mt-0.5 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 rounded"
          >
            {consentChecked ? (
              <CheckSquare className="w-5 h-5 text-lia-btn-primary-bg" />
            ) : (
              <Square className="w-5 h-5 text-lia-text-tertiary group-hover:text-lia-text-secondary transition-colors" />
            )}
          </button>
          <span className="text-xs text-lia-text-secondary leading-relaxed select-none">
            Concordo com o tratamento dos meus dados pessoais para fins desta triagem, conforme a{" "}
            <a
              href={config.privacyPolicyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="underline text-lia-text-primary hover:text-wedo-cyan transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              Política de Privacidade
            </a>{" "}
            e a Lei Geral de Proteção de Dados (LGPD).
          </span>
        </label>

        <div className={config.phoneEnabled ? "flex gap-3" : ""}>
          <button
            type="button"
            onClick={() => onStart(false)}
            disabled={isStarting || !consentChecked}
            aria-label="Iniciar conversa de triagem"
            className={cn(
              "h-11 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text text-sm font-medium hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none",
              config.phoneEnabled ? "flex-1" : "w-full"
            )}
          >
            {isStarting ? "Iniciando..." : "Iniciar Conversa"}
          </button>

          {config.phoneEnabled && onRequestCall && (
            <button
              type="button"
              onClick={onRequestCall}
              disabled={isStarting || !consentChecked}
              aria-label="Solicitar ligação telefônica"
              className="h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-lia-border-subtle text-lia-text-primary text-sm font-medium hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
            >
              <Phone className="w-4 h-4" />
              Receber Ligação
            </button>
          )}
        </div>

        <a
          href={config.privacyPolicyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 text-xs text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
          aria-label="Política de privacidade"
        >
          <Shield className="w-3 h-3" />
          Política de Privacidade
        </a>
      </div>
    </div>
  )
}
