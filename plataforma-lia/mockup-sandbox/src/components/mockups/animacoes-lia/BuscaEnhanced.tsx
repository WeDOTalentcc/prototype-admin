/**
 * BuscaEnhanced — Estado de busca com animações aprimoradas.
 *
 * Melhorias:
 * - Brain icon com anel de pulso ciano suave
 * - Steps progridem sequencialmente com delay real
 * - "Rankeando" tem animação de dots pulsantes quando ativo
 * - Card com borda ciano gradiente e glow sutil
 * - Textos de cada etapa trocam para refletir progresso
 */
import { useEffect, useState } from "react"

type StepState = "done" | "active" | "pending"

interface Step {
  label: string
  activeLabel: string
  doneLabel: string
}

const STEPS: Step[] = [
  { label: "Interpretando",  activeLabel: "Interpretando...",  doneLabel: "Interpretado ✓" },
  { label: "Buscando",       activeLabel: "Buscando...",        doneLabel: "Buscado ✓"      },
  { label: "Rankeando",      activeLabel: "Rankeando...",       doneLabel: "Pronto ✓"       },
]

function getStepState(step: number, active: number): StepState {
  if (step < active) return "done"
  if (step === active) return "active"
  return "pending"
}

export function BuscaEnhanced() {
  const [activeStep, setActiveStep] = useState(0)
  const [loop, setLoop] = useState(0)

  // Avança o step a cada ~1.8s, reinicia depois do último
  useEffect(() => {
    const t = setTimeout(() => {
      if (activeStep < STEPS.length - 1) {
        setActiveStep(s => s + 1)
      } else {
        setTimeout(() => {
          setActiveStep(0)
          setLoop(l => l + 1)
        }, 1800)
      }
    }, 1800)
    return () => clearTimeout(t)
  }, [activeStep, loop])

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-6 px-8 font-sans">
      <style>{`
        @keyframes spin-e { from{transform:rotate(0)} to{transform:rotate(360deg)} }
        @keyframes glow-pulse {
          0%,100% { box-shadow: 0 0 0 0 rgba(96,190,209,0.4); }
          50%      { box-shadow: 0 0 0 12px rgba(96,190,209,0); }
        }
        @keyframes brain-rotate {
          0%,100% { transform: scale(1) rotate(0deg); }
          25%     { transform: scale(1.08) rotate(-4deg); }
          75%     { transform: scale(1.08) rotate(4deg); }
        }
        @keyframes dot-bounce {
          0%,100% { transform: translateY(0); opacity:.4 }
          50%     { transform: translateY(-4px); opacity:1 }
        }
        @keyframes step-appear {
          from { opacity:0; transform: translateX(-6px); }
          to   { opacity:1; transform: translateX(0); }
        }
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>

      <div className="text-xs font-semibold uppercase tracking-widest text-[#60BED1] mb-2">
        ✨ Enhanced — busca animada
      </div>

      {/* Header com Brain icon pulsante */}
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center bg-[#60BED1]/10"
          style={{ animation: "glow-pulse 1.8s ease-in-out infinite" }}
        >
          {/* Brain SVG com animação */}
          <svg
            viewBox="0 0 24 24" fill="none" strokeWidth="1.8"
            stroke="#60BED1" className="w-6 h-6"
            style={{ animation: "brain-rotate 3s ease-in-out infinite" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9.663 17h4.673M12 3v1m6.364 1.636-.707.707M21 12h-1M4 12H3m3.343-5.657-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-800">
          IA está buscando
          <span style={{
            background: "linear-gradient(90deg, #60BED1 0%, #9860D1 50%, #60BED1 100%)",
            backgroundSize: "200% 100%",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            animation: "shimmer 2s linear infinite",
            marginLeft: "4px",
          }}>...</span>
        </h2>
      </div>

      {/* Card */}
      <div
        className="p-5 rounded-xl max-w-sm w-full"
        style={{
          background: "linear-gradient(135deg, #f0fbfd 0%, #faf5ff 100%)",
          border: "1.5px solid rgba(96,190,209,0.35)",
          boxShadow: "0 2px 20px rgba(96,190,209,0.12), 0 1px 4px rgba(0,0,0,0.04)",
        }}
      >
        {/* Ícone de busca animado */}
        <div className="flex items-center gap-3 mb-4">
          <div
            className="relative w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: "linear-gradient(135deg, rgba(96,190,209,0.15) 0%, rgba(152,96,209,0.1) 100%)",
              border: "1px solid rgba(96,190,209,0.25)",
            }}
          >
            {/* Anel externo girando */}
            <div
              className="absolute inset-0 rounded-xl"
              style={{
                border: "2px solid transparent",
                borderTopColor: "#60BED1",
                borderRightColor: "rgba(96,190,209,0.3)",
                animation: "spin-e 1.2s linear infinite",
              }}
            />
            {/* Ícone central */}
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="#60BED1" className="w-5 h-5 relative z-10">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35" strokeLinecap="round"/>
            </svg>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-800">Processando busca</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {activeStep === 0 && "Analisando critérios e intenção..."}
              {activeStep === 1 && "Consultando base de talentos..."}
              {activeStep === 2 && "Calculando compatibilidade..."}
            </p>
          </div>
        </div>

        {/* Steps progressivos */}
        <div className="flex items-center gap-2 flex-wrap">
          {STEPS.map((step, i) => {
            const state = getStepState(i, activeStep)
            return (
              <div key={step.label} className="flex items-center gap-1" style={{animation: state === "active" ? "step-appear .3s ease" : undefined}}>
                {/* Separador */}
                {i > 0 && (
                  <div className="w-4 h-px bg-gray-200 mx-1 flex-shrink-0" />
                )}

                {/* Ícone de status */}
                {state === "done" && (
                  <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: "linear-gradient(135deg, #5DA47A, #60BED1)" }}>
                    <svg viewBox="0 0 12 12" fill="none" stroke="white" strokeWidth="2.5" className="w-3 h-3">
                      <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                )}
                {state === "active" && (
                  <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{
                      background: "linear-gradient(135deg, #60BED1, #9860D1)",
                      animation: "glow-pulse 1s ease-in-out infinite",
                    }}>
                    {i < 2 ? (
                      <div className="w-2.5 h-2.5 rounded-full border-2 border-white border-t-transparent"
                        style={{ animation: "spin-e .8s linear infinite" }} />
                    ) : (
                      // Dots para "Rankeando"
                      <div className="flex items-center gap-0.5">
                        {[0,1,2].map(d => (
                          <div key={d} className="w-1 h-1 rounded-full bg-white"
                            style={{ animation: `dot-bounce .9s ease-in-out infinite`, animationDelay: `${d * 0.2}s` }} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {state === "pending" && (
                  <div className="w-5 h-5 rounded-full flex-shrink-0"
                    style={{ background: "rgba(96,190,209,0.1)", border: "1.5px dashed rgba(96,190,209,0.4)" }} />
                )}

                {/* Label */}
                <span className={`text-xs font-medium transition-colors duration-300 ${
                  state === "done"    ? "text-[#5DA47A]" :
                  state === "active"  ? "text-[#60BED1] font-semibold" :
                  "text-gray-300"
                }`}>
                  {state === "done"   ? step.doneLabel   :
                   state === "active" ? step.activeLabel  :
                   step.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

    </div>
  )
}
