"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FirstAccessManager } from "./first-access-manager"
import { Button } from "@/components/ui/button"
import { Brain, Clock, Lightbulb, AlertTriangle, CheckCircle, ArrowRight } from "lucide-react"
import './onboarding-styles.css'

interface OnboardingControllerProps {
  children: React.ReactNode
  forceOnboarding?: boolean
}

interface UserData {
  id: string
  name: string
  email: string
  phone?: string
  role: string
  companyId: string
  companyName: string
  isFirstAccess: boolean
  permissions: string[]
  createdAt: string
  companyData?: {
    razaoSocial: string
    endereco: string
    telefone: string
  }
}

export function OnboardingController({ children, forceOnboarding = false }: OnboardingControllerProps) {
  const [isFirstAccess, setIsFirstAccess] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showSetupIntroModal, setShowSetupIntroModal] = useState(false)
  const [showThankYouScreen, setShowThankYouScreen] = useState(false)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [dontShowAgainFlag, setDontShowAgainFlag] = useState(false)

  // Initialize userData synchronously using a function initializer
  // This avoids the loading spinner by initializing userData on first render
  const [userData, setUserData] = useState<UserData | null>(() => {
    // SSR: window is undefined, return demo user to avoid hydration mismatch
    if (typeof window === 'undefined') {
      const demoUser: UserData = {
        id: 'demo-user-1',
        name: 'Usuário Demo',
        email: 'demo@wedotalent.com',
        phone: '+55 11 99999-9999',
        role: 'Recrutador',
        companyId: 'demo-company',
        companyName: 'WeDo Talent Demo',
        isFirstAccess: false,
        permissions: ['admin', 'recruitment', 'users', 'settings'],
        createdAt: new Date().toISOString(),
        companyData: {
          razaoSocial: 'WeDo Talent Soluções Ltda',
          endereco: 'São Paulo, SP',
          telefone: '+55 11 3000-0000'
        }
      }
      return demoUser
    }

    let userToSet: UserData | null = null

    try {
      const storedUserData = localStorage.getItem('lia_user_data')
      if (storedUserData) {
        const user = JSON.parse(storedUserData)
        userToSet = user

        const firstAccessFlag = localStorage.getItem('lia_first_access')
        const canReplay = localStorage.getItem('lia_can_replay_onboarding')
        const onboardingDismissed = localStorage.getItem('lia_onboarding_dismissed')

        if (onboardingDismissed === 'true' && !forceOnboarding) {
          // Don't show onboarding
        } else if (firstAccessFlag === 'true' || forceOnboarding || canReplay === 'true') {
          // Show onboarding (handled separately in rendering)
        }
      }
    } catch (error) {
      try {
        localStorage.removeItem('lia_user_data')
      } catch (e) {
        // Ignore
      }
    }

    if (!userToSet) {
      const demoUser: UserData = {
        id: 'demo-user-1',
        name: 'Usuário Demo',
        email: 'demo@wedotalent.com',
        phone: '+55 11 99999-9999',
        role: 'Recrutador',
        companyId: 'demo-company',
        companyName: 'WeDo Talent Demo',
        isFirstAccess: false,
        permissions: ['admin', 'recruitment', 'users', 'settings'],
        createdAt: new Date().toISOString(),
        companyData: {
          razaoSocial: 'WeDo Talent Soluções Ltda',
          endereco: 'São Paulo, SP',
          telefone: '+55 11 3000-0000'
        }
      }
      userToSet = demoUser

      try {
        localStorage.setItem('lia_user_data', JSON.stringify(demoUser))
        localStorage.setItem('lia_can_replay_onboarding', 'true')
      } catch (e) {
      }
    }

    return userToSet
  })

  useEffect(() => {
    if (showThankYouScreen) {
      const timer = setTimeout(() => {
        handleThankYouClose()
      }, 10000)
      return () => clearTimeout(timer)
    }
  }, [showThankYouScreen])

  // Handle token-based access check in effect (must update state)
  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const urlParams = new URLSearchParams(window.location.search)
    const token = urlParams.get('token')

    if (token) {
      setAccessToken(token)
      setIsFirstAccess(true)
    }
  }, [])

  const handleAccessGranted = (newUserData: UserData) => {
    setUserData(newUserData)
    setIsFirstAccess(false)
    setAccessToken(null)

    if (typeof window !== 'undefined' && window.history.replaceState) {
      const url = new URL(window.location.href)
      url.searchParams.delete('token')
      window.history.replaceState({}, document.title, url.toString())
    }
  }

  const handleAccessDenied = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/acesso-negado'
    }
  }

  const handleOnboardingComplete = (dontShowAgain?: boolean) => {
    setShowOnboarding(false)
    setShowSetupIntroModal(true)
    setDontShowAgainFlag(!!dontShowAgain)
    
    if (typeof window !== 'undefined') {
      localStorage.removeItem('lia_first_access')
      localStorage.removeItem('lia_can_replay_onboarding')
      if (dontShowAgain) {
        localStorage.setItem('lia_onboarding_dismissed', 'true')
      }
    }
  }

  const handleOnboardingSkip = (dontShowAgain?: boolean) => {
    setShowOnboarding(false)
    setShowSetupIntroModal(false)
    
    if (typeof window !== 'undefined') {
      if (dontShowAgain) {
        localStorage.setItem('lia_onboarding_dismissed', 'true')
        localStorage.removeItem('lia_can_replay_onboarding')
      } else {
        localStorage.setItem('lia_can_replay_onboarding', 'true')
      }
    }
  }

  const handleStartWizard = () => {
    setShowSetupIntroModal(false)
  }

  const handleSkipSetup = () => {
    setShowSetupIntroModal(false)
    if (typeof window !== 'undefined') {
      localStorage.setItem('lia_can_replay_onboarding', 'true')
    }
  }

  const handleThankYouClose = () => {
    setShowThankYouScreen(false)
  }

  if (isFirstAccess && accessToken) {
    return (
      <FirstAccessManager
        token={accessToken}
        onAccessGranted={handleAccessGranted}
        onAccessDenied={handleAccessDenied}
      />
    )
  }

  if (showSetupIntroModal) {
    return (
      <SetupIntroModal 
        onStartSetup={handleStartWizard}
        onSkip={handleSkipSetup}
      />
    )
  }

  if (showThankYouScreen) {
    return (
      <ThankYouScreen onClose={handleThankYouClose} />
    )
  }

  if (userData) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-md p-8 max-w-md w-full text-center">
        <h2 className="text-2xl font-bold text-gray-950 mb-4">
          Acesso Restrito
        </h2>
        <p className="text-gray-800 mb-6">
          Você precisa de um convite para acessar a plataforma LIA.
        </p>
        <div className="space-y-3">
          <button
            onClick={() => window.location.href = '/login'}
            className="w-full text-white px-6 py-2 rounded-md hover:opacity-90 transition-colors bg-gray-900"
          >
            Fazer Login
          </button>
          <button
            onClick={() => window.location.href = '/demo-onboarding'}
            className="w-full bg-gray-700 text-white px-6 py-2 rounded-md hover:bg-gray-800 transition-colors"
           
          >
            🚀 Demonstração do Onboarding
          </button>
        </div>
      </div>
    </div>
  )
}

function SetupIntroModal({ onStartSetup, onSkip }: { onStartSetup: () => void, onSkip: () => void }) {
  return (
    <div className="fixed inset-0 z-50 overflow-hidden lia-bg-lavender">
      <div className="absolute inset-0 z-0 overflow-hidden">
        {[...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-4 h-4 lia-bg-white opacity-10 rounded-full"
            style={{left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`}}
            animate={{
              y: [0, -100, 0],
              opacity: [0, 0.2, 0],
              scale: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 6 + Math.random() * 4,
              repeat: Infinity,
              delay: Math.random() * 5,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 h-full flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="lia-card max-w-2xl w-full"
        >
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring", bounce: 0.5 }}
              className="inline-flex items-center justify-center w-20 h-20 lia-bg-coral rounded-full mb-6"
            >
              <Brain className="w-10 h-10 text-white" />
            </motion.div>
            
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="lia-title-medium lia-text-black mb-3"
            >
              Vamos Configurar sua Plataforma
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="lia-text-medium"
            >
              Personalize a LIA para atender às necessidades da sua empresa
            </motion.p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="space-y-6 mb-8"
          >
            <p className="lia-text-medium leading-relaxed">
              A partir de agora, vamos coletar algumas informações estratégicas que serão utilizadas para:
            </p>
            
            <ul className="space-y-3 text-left">
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full lia-bg-coral mt-2 flex-shrink-0" />
                <span className="lia-text-medium">
                  Nosso time de Customer Success concluir a configuração e implantação da plataforma
                </span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full lia-bg-coral mt-2 flex-shrink-0" />
                <span className="lia-text-medium">
                  Calibrar a LIA para funcionar de forma personalizada considerando as particularidades da sua empresa e processo de recrutamento
                </span>
              </li>
            </ul>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              <div className="flex items-center gap-3 bg-gray-50 rounded-md p-4">
                <Clock className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="lia-text-bold text-sm">Tempo estimado</p>
                  <p className="lia-text-small">3-5 minutos</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 bg-gray-50 rounded-md p-4">
                <Lightbulb className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="lia-text-bold text-sm">Pode continuar depois</p>
                  <p className="lia-text-small">Menu Configurações</p>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-status-warning/10 border border-status-warning/30 rounded-md p-4">
              <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
              <p className="text-sm text-status-warning">
                Preencher essas informações é extremamente importante para que a plataforma seja configurada e customizada de forma adequada.
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              onClick={onStartSetup}
              variant="primary" className="w-full sm:w-auto"
            >
              <Brain className="w-5 h-5 mr-2 text-wedo-cyan" />
              Começar Configuração
            </Button>
            
            <Button
              variant="secondary"
              onClick={onSkip}
              className="w-full sm:w-auto"
            >
              Fazer depois
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

function ThankYouScreen({ onClose }: { onClose: () => void }) {
  const [countdown, setCountdown] = useState(10)

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="fixed inset-0 z-50 overflow-hidden lia-bg-mint">
      <div className="absolute inset-0 z-0 overflow-hidden">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-3 h-3 lia-bg-white opacity-15 rounded-full"
            style={{left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`}}
            animate={{
              y: [0, -80, 0],
              opacity: [0, 0.25, 0],
              scale: [0.5, 1.2, 0.5],
            }}
            transition={{
              duration: 5 + Math.random() * 3,
              repeat: Infinity,
              delay: Math.random() * 4,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 h-full flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center max-w-2xl"
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ 
              delay: 0.3, 
              type: "spring", 
              bounce: 0.4,
              duration: 1 
            }}
            className="inline-flex items-center justify-center w-32 h-32 bg-white rounded-full mb-8"
          >
            <motion.div
              animate={{ 
                scale: [1, 1.1, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <CheckCircle className="w-16 h-16" style={{color: 'var(--wedo-green-pastel)'}} />
            </motion.div>
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="lia-title-large lia-text-black mb-6"
          >
            Parabéns! Configuração Concluída
          </motion.h1>
          
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="space-y-4 mb-10"
          >
            <p className="lia-text-large">
              Obrigado por completar a configuração inicial da plataforma.
            </p>
            <p className="lia-text-medium">
              Nosso time de Customer Success entrará em contato dentro de 24 horas para finalizar a implantação e tirar qualquer dúvida.
            </p>
            <p className="lia-text-large font-medium">
              Enquanto isso, você já pode explorar a plataforma!
            </p>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="space-y-4"
          >
            <Button
              onClick={onClose}
              variant="primary" className="text-lg px-10 py-5"
            >
              Acessar Plataforma
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.2 }}
              className="lia-text-small"
            >
              Redirecionando automaticamente em {countdown} segundos...
            </motion.p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

export function useUserData() {
  const [userData, setUserData] = useState<UserData | null>(null)

  useEffect(() => {
    const storedUserData = localStorage.getItem('lia_user_data')
    if (storedUserData) {
      try {
        setUserData(JSON.parse(storedUserData))
      } catch (error) {
      }
    }
  }, [])

  const updateUserData = (newData: Partial<UserData>) => {
    if (userData) {
      const updatedData = { ...userData, ...newData }
      setUserData(updatedData)
      localStorage.setItem('lia_user_data', JSON.stringify(updatedData))
    }
  }

  const logout = () => {
    setUserData(null)
    localStorage.removeItem('lia_user_data')
    localStorage.removeItem('lia_first_access')
    localStorage.removeItem('lia_can_replay_onboarding')
    localStorage.removeItem('lia_onboarding_dismissed')
    window.location.href = '/login'
  }

  return {
    userData,
    updateUserData,
    logout,
    isLoggedIn: !!userData
  }
}

export function canReplayOnboarding(): boolean {
  return localStorage.getItem('lia_can_replay_onboarding') === 'true'
}

export function triggerOnboarding() {
  localStorage.setItem('lia_first_access', 'true')
  window.location.reload()
}

export function generateInviteLink(companyData: {
  companyName: string
  contactName: string
  contactEmail: string
  contactPhone?: string
  companyData: {
    razaoSocial: string
    endereco: string
    telefone: string
  }
}): string {
  const token = btoa(JSON.stringify({
    ...companyData,
    timestamp: Date.now(),
    expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000
  }))

  const baseUrl = window.location.origin
  return `${baseUrl}?token=${encodeURIComponent(token)}`
}

export function validateInviteToken(token: string): {
  isValid: boolean
  data?: any
  error?: string
} {
  try {
    const decoded = JSON.parse(atob(token))

    if (decoded.expiresAt < Date.now()) {
      return {
        isValid: false,
        error: 'Token expirado'
      }
    }

    return {
      isValid: true,
      data: decoded
    }
  } catch (error) {
    return {
      isValid: false,
      error: 'Token inválido'
    }
  }
}

export type { UserData, OnboardingControllerProps }
