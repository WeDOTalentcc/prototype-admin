"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
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
      <div className="min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600 dark:text-gray-400" />
      </div>
    )
  }

  const userName = user?.name?.split(" ")[0] || "Recrutador"

  return (
    <div className="min-h-screen bg-white overflow-hidden relative font-['Open_Sans',sans-serif]">
      <AnimatePresence mode="wait">
        {(phase === "cyan-screen" || phase === "iris-closing") && (
          <motion.div
            key="cyan-overlay"
            className="fixed inset-0 bg-gray-900 flex items-center justify-center z-50"
            initial={{ opacity: 0 }}
            animate={{ 
              opacity: phase === "iris-closing" ? 0 : 1,
              scale: phase === "iris-closing" ? 0 : 1,
              borderRadius: phase === "iris-closing" ? "50%" : "0%"
            }}
            transition={{ 
              duration: phase === "iris-closing" ? 0.8 : 0.4,
              ease: "easeInOut"
            }}
          >
            <Brain className="w-24 h-24 text-white" />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center justify-center w-full max-w-3xl px-8">
          {(phase === "brain-center" || phase === "brain-pulse" || phase === "brain-move" || phase === "typewriter" || phase === "fade-text") && (
            <motion.div
              className="flex items-center gap-6"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ 
                opacity: phase === "fade-text" ? 0 : 1,
                scale: 1,
                x: phase === "brain-move" || phase === "typewriter" || phase === "fade-text" ? -100 : 0
              }}
              transition={{ 
                duration: phase === "brain-move" ? 0.5 : 0.4,
                ease: "easeOut"
              }}
            >
              <motion.div
                animate={{
                  scale: phase === "brain-pulse" ? [1, 1.2, 1] : 1,
                  opacity: phase === "brain-pulse" ? [1, 0.7, 1] : 1
                }}
                transition={{
                  duration: 0.4,
                  repeat: phase === "brain-pulse" ? 2 : 0,
                  ease: "easeInOut"
                }}
              >
                <Brain className="w-20 h-20 text-wedo-cyan" />
              </motion.div>

              {(phase === "typewriter" || phase === "fade-text") && (
                <motion.div
                  className="flex flex-col gap-2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ 
                    opacity: phase === "fade-text" ? 0 : 1,
                    x: 0
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-2xl text-gray-800 font-['Open_Sans',sans-serif] font-light">
                    {typedText1}
                    {typedText1.length < text1.length && (
                      <span className="animate-pulse">|</span>
                    )}
                  </p>
                  {typedText2 && (
                    <p className="text-lg text-gray-600">
                      {typedText2}
                      {typedText2.length < text2.length && typedText1.length === text1.length && (
                        <span className="animate-pulse">|</span>
                      )}
                    </p>
                  )}
                  {typedText3 && (
                    <p className="text-lg text-gray-600">
                      {typedText3}
                      {typedText3.length < text3.length && typedText2.length === text2.length && (
                        <span className="animate-pulse">|</span>
                      )}
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}

          {phase === "logo-zoom" && (
            <motion.div
              className="fixed inset-0 flex items-center justify-center z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                initial={{ scale: 4, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 1, ease: "easeOut" }}
              >
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WeDo Talent"
                  width={300}
                  height={100}
                  priority
                  style={{width: 'auto', height: 'auto'}}
                />
              </motion.div>
            </motion.div>
          )}

          {(phase === "logo-appear" || phase === "welcome-message" || phase === "complete") && (
            <motion.div
              className="flex flex-col items-center gap-8 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <motion.div
                initial={{ scale: 1, opacity: 1 }}
                animate={{ scale: 1, opacity: 1 }}
              >
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WeDo Talent"
                  width={180}
                  height={60}
                  priority
                  style={{width: 'auto', height: 'auto'}}
                />
              </motion.div>

              {(phase === "welcome-message" || phase === "complete") && (
                <motion.div
                  className="flex flex-col items-center gap-4"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.2 }}
                >
                  <h1 className="text-3xl font-['Open_Sans',sans-serif] text-gray-800">
                    Olá, <span className="text-gray-600 dark:text-gray-400 font-semibold">{userName}</span>
                  </h1>
                  <p className="text-gray-800 dark:text-gray-200 text-lg max-w-xl leading-relaxed text-center">
                    Bem-vindo(a) à nova era do recrutamento inteligente e automatizado.
                  </p>
                  <p className="text-gray-600 text-base max-w-xl leading-relaxed text-center">
                    A partir de agora a WeDOTalent vai te dar superpoderes para otimizar seu trabalho de recrutador(a).
                  </p>
                </motion.div>
              )}

              {phase === "complete" && (
                <motion.div
                  className="flex flex-col items-center gap-5"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                >
                  <p className="text-gray-800 dark:text-gray-200 text-lg font-medium">
                    Vamos começar?
                  </p>
                  <Button
                    onClick={handleStart}
                    className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-6 text-lg font-medium rounded-md hover:transition-all duration-300"
                  >
                    Clique aqui para começar →
                  </Button>
                  
                  <label className="flex items-center gap-2 cursor-pointer group mt-2">
                    <div 
                      className={`w-4 h-4 rounded-md border-2 transition-all duration-200 flex items-center justify-center ${
                        dontShowAgain 
                          ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50' 
                          : 'border-gray-400 hover:border-gray-500'
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
                      className={`text-sm transition-colors duration-200 ${
                        dontShowAgain ? 'text-gray-800 dark:text-gray-200' : 'text-gray-500 group-hover:text-gray-600'
                      }`}
                      onClick={() => setDontShowAgain(!dontShowAgain)}
                    >
                      Não mostrar novamente
                    </span>
                  </label>
                  
                  <p className="text-gray-500 text-sm mt-2">
                    💡 Dica: Acesse <span className="font-medium text-gray-800 dark:text-gray-200">Configurações</span> para personalizar sua experiência com a LIA.
                  </p>
                </motion.div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
