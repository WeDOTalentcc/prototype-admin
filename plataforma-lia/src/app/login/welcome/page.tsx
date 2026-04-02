"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useJWTAuth } from "@/contexts/auth-context"
import { Brain, Loader2 } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"

type AnimationPhase = 
  | "initial"
  | "cyan-screen"
  | "iris-closing"
  | "brain-center"
  | "brain-pulse"
  | "brain-move"
  | "typewriter"
  | "fade-text"
  | "logo-zoom"
  | "logo-appear"
  | "welcome-message"
  | "complete"

export default function WelcomePage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useJWTAuth()
  const [phase, setPhase] = useState<AnimationPhase>("initial")
  const [typedText1, setTypedText1] = useState("")
  const [typedText2, setTypedText2] = useState("")
  const [typedText3, setTypedText3] = useState("")
  const [pulseCount, setPulseCount] = useState(0)
  const [dontShowAgain, setDontShowAgain] = useState(false)

  const text1 = "Prazer, eu sou a LIA."
  const text2 = "Sua agente de IA de recrutamento."
  const text3 = "A partir de agora, vamos trabalhar juntos."

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login")
      return
    }

    if (isLoading) return
    
    // Verificar se usuário já optou por não ver o onboarding
    const welcomeDismissed = localStorage.getItem('lia_welcome_dismissed')
    if (welcomeDismissed === 'true') {
      router.push("/funil")
      return
    }

    const timers: NodeJS.Timeout[] = []

    const schedule = (fn: () => void, delay: number) => {
      const timer = setTimeout(fn, delay)
      timers.push(timer)
      return timer
    }

    schedule(() => setPhase("cyan-screen"), 200)
    schedule(() => setPhase("iris-closing"), 800)
    schedule(() => setPhase("brain-center"), 1800)
    schedule(() => setPhase("brain-pulse"), 2200)

    return () => timers.forEach(clearTimeout)
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (phase !== "brain-pulse") return

    const pulseInterval = setInterval(() => {
      setPulseCount(prev => {
        if (prev >= 2) {
          clearInterval(pulseInterval)
          setTimeout(() => setPhase("brain-move"), 300)
          return prev
        }
        return prev + 1
      })
    }, 400)

    return () => clearInterval(pulseInterval)
  }, [phase])

  useEffect(() => {
    if (phase !== "brain-move") return
    setTimeout(() => setPhase("typewriter"), 600)
  }, [phase])

  useEffect(() => {
    if (phase !== "typewriter") return

    let currentLine = 1
    let charIndex = 0
    const typeSpeed = 50

    const typeInterval = setInterval(() => {
      if (currentLine === 1) {
        if (charIndex < text1.length) {
          setTypedText1(text1.slice(0, charIndex + 1))
          charIndex++
        } else {
          currentLine = 2
          charIndex = 0
          setTimeout(() => {}, 200)
        }
      } else if (currentLine === 2) {
        if (charIndex < text2.length) {
          setTypedText2(text2.slice(0, charIndex + 1))
          charIndex++
        } else {
          currentLine = 3
          charIndex = 0
        }
      } else if (currentLine === 3) {
        if (charIndex < text3.length) {
          setTypedText3(text3.slice(0, charIndex + 1))
          charIndex++
        } else {
          clearInterval(typeInterval)
          setTimeout(() => setPhase("fade-text"), 1500)
        }
      }
    }, typeSpeed)

    return () => clearInterval(typeInterval)
  }, [phase])

  useEffect(() => {
    if (phase !== "fade-text") return
    setTimeout(() => setPhase("logo-zoom"), 800)
  }, [phase])

  useEffect(() => {
    if (phase !== "logo-zoom") return
    setTimeout(() => setPhase("logo-appear"), 1200)
  }, [phase])

  useEffect(() => {
    if (phase !== "logo-appear") return
    setTimeout(() => setPhase("welcome-message"), 600)
  }, [phase])

  useEffect(() => {
    if (phase !== "welcome-message") return
    setTimeout(() => setPhase("complete"), 500)
  }, [phase])

  const handleStart = () => {
    if (dontShowAgain) {
      localStorage.setItem('lia_welcome_dismissed', 'true')
    }
    router.push("/configuracoes")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
      </div>
    )
  }

  const userName = user?.name?.split(" ")[0] || "Recrutador"

  return (
    <div className="min-h-screen bg-lia-bg-primary overflow-hidden relative font-['Open_Sans',sans-serif]">
      {/* OPT-027: CSS keyframes replacing framer-motion brain-pulse animation */}
      <style>{`
        @keyframes brain-pulse-anim {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.7; }
        }
      `}</style>
      {(phase === "cyan-screen" || phase === "iris-closing") && (
          <div
            className="fixed inset-0 bg-lia-btn-primary-bg flex items-center justify-center z-50"
            style={{
              opacity: phase === "iris-closing" ? 0 : 1,
              transform: phase === "iris-closing" ? "scale(0)" : "scale(1)",
              borderRadius: phase === "iris-closing" ? "50%" : "0%",
              transition: phase === "iris-closing" ? "opacity 0.8s ease-in-out, transform 0.8s ease-in-out, border-radius 0.8s ease-in-out" : "opacity 0.4s ease-in-out",
            }}
          >
            <Brain className="w-24 h-24 text-white" />
          </div>
        )}

      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center justify-center w-full max-w-3xl px-8">
          {(phase === "brain-center" || phase === "brain-pulse" || phase === "brain-move" || phase === "typewriter" || phase === "fade-text") && (
            <div
              className="flex items-center gap-6"
              style={{
                opacity: phase === "fade-text" ? 0 : 1,
                transform: `translateX(${(phase === "brain-move" || phase === "typewriter" || phase === "fade-text") ? -100 : 0}px) scale(${phase === "brain-center" ? 0.5 : 1})`,
                transition: phase === "brain-move" ? "opacity 0.5s ease-out, transform 0.5s ease-out" : "opacity 0.4s ease-out, transform 0.4s ease-out",
              }}
            >
              <div
                style={{
                  transform: phase === "brain-pulse" ? undefined : "scale(1)",
                  animation: phase === "brain-pulse" ? "brain-pulse-anim 0.4s ease-in-out 3" : "none",
                }}
              >
                <Brain className="w-20 h-20 text-wedo-cyan" />
              </div>

              {(phase === "typewriter" || phase === "fade-text") && (
                <div
                  className="flex flex-col gap-2"
                  style={{
                    opacity: phase === "fade-text" ? 0 : 1,
                    transform: "translateX(0)",
                    transition: "opacity 0.3s ease",
                  }}
                >
                  <p className="text-2xl text-lia-text-primary font-['Open_Sans',sans-serif] font-light">
                    {typedText1}
                    {typedText1.length < text1.length && (
                      <span className="animate-pulse motion-reduce:animate-none">|</span>
                    )}
                  </p>
                  {typedText2 && (
                    <p className="text-lg text-lia-text-secondary">
                      {typedText2}
                      {typedText2.length < text2.length && typedText1.length === text1.length && (
                        <span className="animate-pulse motion-reduce:animate-none">|</span>
                      )}
                    </p>
                  )}
                  {typedText3 && (
                    <p className="text-lg text-lia-text-secondary">
                      {typedText3}
                      {typedText3.length < text3.length && typedText2.length === text2.length && (
                        <span className="animate-pulse motion-reduce:animate-none">|</span>
                      )}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {phase === "logo-zoom" && (
            <div
              className="fixed inset-0 flex items-center justify-center z-40 animate-in fade-in duration-300"
            >
              <div
                className="animate-in zoom-in-50 duration-1000"
              >
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WeDo Talent"
                  width={300}
                  height={100}
                  priority
                  style={{width: 'auto', height: 'auto'}}
                />
              </div>
            </div>
          )}

          {(phase === "logo-appear" || phase === "welcome-message" || phase === "complete") && (
            <div
              className="flex flex-col items-center gap-8 text-center animate-in fade-in duration-400"
            >
              <div>
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WeDo Talent"
                  width={180}
                  height={60}
                  priority
                  style={{width: 'auto', height: 'auto'}}
                />
              </div>

              {(phase === "welcome-message" || phase === "complete") && (
                <div
                  className="flex flex-col items-center gap-4 animate-in fade-in slide-in-from-bottom-4 duration-400"
                >
                  <h1 className="text-3xl font-['Open_Sans',sans-serif] text-lia-text-primary">
                    Olá, <span className="text-lia-text-secondary dark:text-lia-text-tertiary font-semibold">{userName}</span>
                  </h1>
                  <p className="text-lia-text-primary dark:text-lia-text-primary text-lg max-w-xl leading-relaxed text-center">
                    Bem-vindo(a) à nova era do recrutamento inteligente e automatizado.
                  </p>
                  <p className="text-lia-text-secondary text-base max-w-xl leading-relaxed text-center">
                    A partir de agora a WeDOTalent vai te dar superpoderes para otimizar seu trabalho de recrutador(a).
                  </p>
                </div>
              )}

              {phase === "complete" && (
                <div
                  className="flex flex-col items-center gap-5 animate-in fade-in slide-in-from-bottom-4 duration-300"
                >
                  <p className="text-lia-text-primary dark:text-lia-text-primary text-lg font-medium">
                    Vamos começar?
                  </p>
                  <Button
                    onClick={handleStart}
                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text px-8 py-6 text-lg font-medium rounded-md transition-colors motion-reduce:transition-none duration-300"
                  >
                    Clique aqui para começar →
                  </Button>
                  
                  <label className="flex items-center gap-2 cursor-pointer group mt-2">
                    <div 
                      className={`w-4 h-4 rounded-md border-2 transition-colors motion-reduce:transition-none duration-200 flex items-center justify-center ${
                        dontShowAgain 
                          ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-subtle' 
                          : 'border-lia-border-medium hover:border-lia-border-medium'
                      }`}
                      onClick={() => setDontShowAgain(!dontShowAgain)}
                    >
                      {dontShowAgain && (
                        <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span 
                      className={`text-sm transition-colors motion-reduce:transition-none duration-200 ${
                        dontShowAgain ? 'text-lia-text-primary dark:text-lia-text-primary' : 'text-lia-text-secondary group-hover:text-lia-text-secondary'
                      }`}
                      onClick={() => setDontShowAgain(!dontShowAgain)}
                    >
                      Não mostrar novamente
                    </span>
                  </label>
                  
                  <p className="text-lia-text-secondary text-sm mt-2">
                    💡 Dica: Acesse <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">Configurações</span> para personalizar sua experiência com a LIA.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
