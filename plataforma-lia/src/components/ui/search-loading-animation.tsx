'use client'

import React, { useEffect, useRef, useState } from "react"
import { Check } from 'lucide-react'

interface SearchLoadingAnimationProps {
  isActive: boolean
}

interface Step {
  label: string
  activeLabel: string
  doneLabel: string
  subtitleActive: string
}

const STEPS: Step[] = [
  {
    label:         "Interpretando",
    activeLabel:   "Interpretando...",
    doneLabel:     "Interpretado",
    subtitleActive: "Analisando critérios e intenção...",
  },
  {
    label:         "Buscando",
    activeLabel:   "Buscando...",
    doneLabel:     "Buscado",
    subtitleActive: "Consultando base de talentos...",
  },
  {
    label:         "Rankeando",
    activeLabel:   "Rankeando...",
    doneLabel:     "Rankeado",
    subtitleActive: "Calculando compatibilidade...",
  },
]

const STEP_DURATION = 1600 // ms por step

type StepState = "done" | "active" | "pending"

function getState(i: number, active: number): StepState {
  if (i < active) return "done"
  if (i === active) return "active"
  return "pending"
}

export const SearchLoadingAnimation = React.memo(function SearchLoadingAnimation({ isActive }: SearchLoadingAnimationProps) {
  const [activeStep, setActiveStep] = useState(0)
  const cycleRef = useRef(0)

  // Reseta quando fica inativo
  useEffect(() => {
    if (!isActive) {
      setActiveStep(0)
    }
  }, [isActive])

  // Avança steps em loop enquanto ativo
  useEffect(() => {
    if (!isActive) return
    const t = setTimeout(() => {
      setActiveStep(s => {
        if (s < STEPS.length - 1) return s + 1
        cycleRef.current++
        return 0
      })
    }, STEP_DURATION)
    return () => clearTimeout(t)
  }, [isActive, activeStep, cycleRef.current]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!isActive) return null

  const activeStepData = STEPS[activeStep]

  return (
    <div className="mb-6 rounded-xl max-w-md w-full overflow-hidden" style={{
      background: "linear-gradient(135deg, color-mix(in srgb, var(--wedo-cyan, #60BED1) 8%, white), color-mix(in srgb, var(--wedo-purple, #9860D1) 5%, white))",
      border: "1.5px solid color-mix(in srgb, var(--wedo-cyan, #60BED1) 30%, transparent)",
      boxShadow: "0 2px 16px color-mix(in srgb, var(--wedo-cyan, #60BED1) 10%, transparent), 0 1px 4px rgba(0,0,0,0.04)",
    }}>
      <style>{`
        @keyframes sla-spin    { from{transform:rotate(0)} to{transform:rotate(360deg)} }
        @keyframes sla-glow    { 0%,100%{box-shadow:0 0 0 0 color-mix(in srgb, var(--wedo-cyan,#60BED1) 40%, transparent)} 50%{box-shadow:0 0 0 10px transparent} }
        @keyframes sla-ring    { from{transform:rotate(0)} to{transform:rotate(360deg)} }
        @keyframes sla-shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
        @keyframes sla-dot     { 0%,100%{transform:translateY(0);opacity:.4} 50%{transform:translateY(-3px);opacity:1} }
        @keyframes sla-appear  { from{opacity:0;transform:translateX(-4px)} to{opacity:1;transform:translateX(0)} }
      `}</style>

      <div className="p-4">
        {/* Header row */}
        <div className="flex items-center gap-3 mb-4">
          {/* Ícone de busca com anel girando */}
          <div className="relative w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0" style={{
            background: "linear-gradient(135deg, color-mix(in srgb, var(--wedo-cyan,#60BED1) 15%, white), color-mix(in srgb, var(--wedo-purple,#9860D1) 10%, white))",
            border: "1px solid color-mix(in srgb, var(--wedo-cyan,#60BED1) 25%, transparent)",
          }}>
            {/* Anel externo */}
            <div className="absolute inset-0 rounded-xl" style={{
              border: "2px solid transparent",
              borderTopColor: "var(--wedo-cyan, #60BED1)",
              borderRightColor: "color-mix(in srgb, var(--wedo-cyan,#60BED1) 30%, transparent)",
              animation: "sla-ring 1.1s linear infinite",
            }} />
            {/* Search icon */}
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="var(--wedo-cyan, #60BED1)" className="w-5 h-5 relative z-10">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35" strokeLinecap="round"/>
            </svg>
          </div>

          <div className="min-w-0">
            <p className="text-sm font-semibold text-lia-text-primary">
              Processando busca
              <span style={{
                background: "linear-gradient(90deg, var(--wedo-cyan,#60BED1) 0%, var(--wedo-purple,#9860D1) 50%, var(--wedo-cyan,#60BED1) 100%)",
                backgroundSize: "200% 100%",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                animation: "sla-shimmer 2s linear infinite",
                marginLeft: "2px",
              }}>...</span>
            </p>
            <p className="text-xs text-lia-text-secondary truncate" style={{ animation: "sla-appear .3s ease" }} key={activeStep}>
              {activeStepData.subtitleActive}
            </p>
          </div>
        </div>

        {/* Steps */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {STEPS.map((step, i) => {
            const state = getState(i, activeStep)
            return (
              <React.Fragment key={step.label}>
                {i > 0 && <div className="w-4 h-px flex-shrink-0" style={{ background: "color-mix(in srgb, var(--wedo-cyan,#60BED1) 30%, transparent)" }} />}

                <div className="flex items-center gap-1.5" style={state === "active" ? { animation: "sla-appear .25s ease" } : undefined}>
                  {/* Ícone */}
                  {state === "done" && (
                    <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{
                      background: "linear-gradient(135deg, var(--wedo-green,#5DA47A), var(--wedo-cyan,#60BED1))",
                    }}>
                      <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                    </div>
                  )}
                  {state === "active" && (
                    <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{
                      background: "linear-gradient(135deg, var(--wedo-cyan,#60BED1), var(--wedo-purple,#9860D1))",
                      animation: "sla-glow 1.2s ease-in-out infinite",
                    }}>
                      {i < 2 ? (
                        // Spinner para Interpretando e Buscando
                        <div className="w-2.5 h-2.5 rounded-full border-2 border-white border-t-transparent" style={{ animation: "sla-spin .8s linear infinite" }} />
                      ) : (
                        // Dots quicando para Rankeando
                        <div className="flex items-center gap-px">
                          {[0, 1, 2].map(d => (
                            <div key={d} className="w-1 h-1 rounded-full bg-white" style={{
                              animation: "sla-dot .9s ease-in-out infinite",
                              animationDelay: `${d * 0.18}s`,
                            }} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {state === "pending" && (
                    <div className="w-5 h-5 rounded-full flex-shrink-0" style={{
                      background: "color-mix(in srgb, var(--wedo-cyan,#60BED1) 8%, white)",
                      border: "1.5px dashed color-mix(in srgb, var(--wedo-cyan,#60BED1) 35%, transparent)",
                    }} />
                  )}

                  {/* Label */}
                  <span className={`text-xs font-medium transition-colors duration-300 ${
                    state === "done"   ? "text-wedo-green" :
                    state === "active" ? "text-wedo-cyan font-semibold" :
                    "text-lia-text-secondary opacity-40"
                  }`}>
                    {state === "done"   ? step.doneLabel   :
                     state === "active" ? step.activeLabel :
                     step.label}
                  </span>
                </div>
              </React.Fragment>
            )
          })}
        </div>
      </div>
    </div>
  )
})
SearchLoadingAnimation.displayName = 'SearchLoadingAnimation'
