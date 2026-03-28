"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Clock, Shield, Mic } from "lucide-react"
import type { TriagemConfig } from "@/components/triagem/types"

interface WelcomeCardProps {
  config: TriagemConfig
  onStart: (voiceMode?: boolean) => void
  isStarting?: boolean
  className?: string
}

export function WelcomeCard({ config, onStart, isStarting = false, className }: WelcomeCardProps) {
  return (
    <div
      className={cn(
        "flex-1 flex items-center justify-center px-4 py-8",
        className
      )}
    >
      <div className="w-full max-w-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-sm p-6 space-y-6">
        <div className="flex flex-col items-center gap-4 text-center">
          {config.companyLogoUrl ? (
            <img
              src={config.companyLogoUrl}
              alt={`Logo ${config.companyName}`}
              className="h-12 object-contain"
            />
          ) : (
            <div className="h-12 px-4 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-md">
              <span className="text-sm font-semibold text-gray-600 dark:text-gray-300 font-['Open_Sans',sans-serif]">
                {config.companyName}
              </span>
            </div>
          )}

          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]">
            {config.jobTitle}
          </h1>
        </div>

        <div className="flex items-start gap-3 p-4 bg-[#60BED1]/10 rounded-md">
          <LIAIcon size="sm" className="flex-shrink-0 bg-[#60BED1]/10" />
          <div className="text-sm text-gray-700 dark:text-gray-300 font-['Open_Sans',sans-serif] leading-relaxed">
            <p className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
              Olá, {config.candidateName}! Eu sou a LIA 👋
            </p>
            <p>{config.welcomeMessage || "Vou conduzir sua triagem para esta vaga. Será uma conversa rápida e descontraída sobre sua experiência e habilidades."}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif]">
          <Clock className="w-3.5 h-3.5" />
          <span>
            Tempo estimado:{" "}
            <span className="font-['Inter',sans-serif] font-medium">~{config.estimatedMinutes}</span> minutos
          </span>
        </div>

        <div className="space-y-3">
          <button
            type="button"
            onClick={() => onStart(false)}
            disabled={isStarting}
            aria-label="Iniciar conversa de triagem por texto"
            className="w-full h-11 flex items-center justify-center rounded-md bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none font-['Open_Sans',sans-serif]"
          >
            {isStarting ? "Iniciando..." : "Iniciar Conversa"}
          </button>

          {config.voiceMode && (
            <button
              type="button"
              onClick={() => onStart(true)}
              disabled={isStarting}
              aria-label="Iniciar conversa de triagem por voz"
              className="w-full h-11 flex items-center justify-center gap-2 rounded-md border border-gray-900 dark:border-gray-50 bg-transparent text-gray-900 dark:text-gray-50 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:outline-none font-['Open_Sans',sans-serif]"
            >
              <Mic className="w-4 h-4" />
              {isStarting ? "Iniciando..." : "Iniciar Conversa por Voz"}
            </button>
          )}
        </div>

        <a
          href={config.privacyPolicyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors font-['Open_Sans',sans-serif]"
          aria-label="Política de privacidade"
        >
          <Shield className="w-3 h-3" />
          Política de Privacidade
        </a>
      </div>
    </div>
  )
}
