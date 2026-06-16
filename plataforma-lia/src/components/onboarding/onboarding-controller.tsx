"use client"

import { useState, useEffect } from "react"
import { FirstAccessManager } from "./first-access-manager"
import { Button } from "@/components/ui/button"
import { useOnboardingStore } from "@/stores/onboarding-store"
import { useAuthStore } from "@/stores/auth-store"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Clock, Lightbulb, AlertTriangle, CheckCircle, ArrowRight } from "lucide-react"
import './onboarding-styles.css'
import { useAiPersona } from "@/hooks/company/use-ai-persona"

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
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [isFirstAccess, setIsFirstAccess] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showSetupIntroModal, setShowSetupIntroModal] = useState(false)
  const [showThankYouScreen, setShowThankYouScreen] = useState(false)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [dontShowAgainFlag, setDontShowAgainFlag] = useState(false)

  const onboardingStore = useOnboardingStore()
  const authUser = useAuthStore((s) => s.user)
  const authIsAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const authIsLoading = useAuthStore((s) => s.isLoading)

  const [userData, setUserData] = useState<UserData | null>(null)

  const [isDevMode, setIsDevMode] = useState(process.env.NODE_ENV !== 'production')

  useEffect(() => {
    const storeState = useOnboardingStore.getState()
    const storedUserData = storeState.userData
    if (storedUserData && !userData) {
      setUserData(storedUserData as unknown as UserData)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!userData && authIsAuthenticated && authUser && !authIsLoading) {
      const syntheticUserData: UserData = {
        id: authUser.id || 'auto',
        name: authUser.name || authUser.email,
        email: authUser.email,
        role: ('role' in authUser ? authUser.role : 'viewer') || 'viewer',
        companyId: ('company_id' in authUser ? (authUser as any).company_id : '') || 'demo_company',
        companyName: ('company' in authUser ? (authUser as any).company : '') || 'WeDO Talent',
        isFirstAccess: false,
        permissions: ('permissions' in authUser ? (authUser as any).permissions : []) || [],
        createdAt: ('created_at' in authUser ? (authUser as any).created_at : new Date().toISOString()),
      }
      setUserData(syntheticUserData)
      onboardingStore.setUserData(syntheticUserData as unknown as Record<string, unknown>)
    }
  }, [authUser, authIsAuthenticated, authIsLoading, userData, onboardingStore])

  useEffect(() => {
    if (isDevMode && !userData) {
      const fallbackUser: UserData = {
        id: 'dev-auto',
        name: 'Demo User',
        email: 'demo@wedotalent.com',
        role: 'recruiter',
        companyId: 'demo_company',
        companyName: 'WeDO Talent',
        isFirstAccess: false,
        permissions: [],
        createdAt: new Date().toISOString(),
      }
      setUserData(fallbackUser)
      onboardingStore.setUserData(fallbackUser as unknown as Record<string, unknown>)
    }
  }, [isDevMode, userData, onboardingStore])

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
    
    onboardingStore.setFirstAccess(false)
    onboardingStore.setCanReplayOnboarding(false)
    if (dontShowAgain) {
      onboardingStore.setOnboardingDismissed(true)
    }
  }

  const handleOnboardingSkip = (dontShowAgain?: boolean) => {
    setShowOnboarding(false)
    setShowSetupIntroModal(false)
    
    if (dontShowAgain) {
      onboardingStore.setOnboardingDismissed(true)
      onboardingStore.setCanReplayOnboarding(false)
    } else {
      onboardingStore.setCanReplayOnboarding(true)
    }
  }

  const handleStartWizard = () => {
    setShowSetupIntroModal(false)
    if (typeof window !== "undefined") {
      // Task #712: stop swallowing the setup intent — kick off the
      // conversational onboarding flow (OnboardingChatPage) instead of
      // dropping the user back into an empty dashboard.
      window.location.href = "/onboarding"
    }
  }

  const handleSkipSetup = () => {
    setShowSetupIntroModal(false)
    onboardingStore.setCanReplayOnboarding(true)
  }

  const handleThankYouClose = () => {
    setShowThankYouScreen(false)
  }

  if (isFirstAccess && accessToken) {
    return (
      <FirstAccessManager
        token={accessToken}
        onAccessGranted={handleAccessGranted as any}
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

  if (userData || isDevMode) {
    return <>{children}</>
  }

  if (authIsLoading || (authIsAuthenticated && !userData)) {
    return (
      <div className="min-h-screen bg-lia-bg-primary flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lia-border-strong" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-lia-bg-primary flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl p-8 max-w-md w-full text-center">
        <h2 className="text-2xl font-semibold text-lia-text-primary mb-4">
          Acesso Restrito
        </h2>
        <p className="text-lia-text-primary mb-6">
          Você precisa de um convite para acessar a WeDOTalent.
        </p>
        <div className="space-y-3">
          <button
            onClick={() => window.location.href = '/login'}
            className="w-full text-white px-6 py-2 rounded-xl hover:opacity-90 transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg"
          >
            Fazer Login
          </button>
        </div>
      </div>
    </div>
  )
}

function SetupIntroModal({ onStartSetup, onSkip }: { onStartSetup: () => void, onSkip: () => void }) {
  return (
    <div className="fixed inset-0 z-50 overflow-hidden lia-bg-lavender">
      {/* OPT-027: Decorative particles — static (replaced framer-motion infinite float) */}
      <div className="absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
        {[8, 15, 25, 35, 45, 55, 65, 75, 85, 20, 50, 80].map((left, i) => (
          <div
            key={i}
            className="absolute w-4 h-4 lia-bg-lia-bg-primary opacity-5 rounded-full"
            style={{left: `${left}%`, top: `${(i * 8 + 5) % 100}%`}}
          />
        ))}
      </div>

      <div className="relative z-10 h-full flex items-center justify-center p-4">
        <Card
          className="max-w-2xl w-full animate-in fade-in zoom-in-95 slide-in-from-bottom-6 duration-500"
        >
          <div className="text-center mb-8">
            <div
              className="inline-flex items-center justify-center w-20 h-20 lia-bg-coral rounded-full mb-6 animate-in zoom-in-75 duration-300"
            >
              <Brain className="w-10 h-10 text-white" />
            </div>
            
            <h1
              className="text-xl font-semibold text-lia-text-primary mb-3 animate-in fade-in slide-in-from-bottom-3 duration-300"
            >
              Vamos Configurar sua Plataforma
            </h1>
            
            <p
              className="lia-text-medium animate-in fade-in slide-in-from-bottom-3 duration-300"
            >
              {`Personalize ${personaName} para atender às necessidades da sua empresa`}
            </p>
          </div>

          <div
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
                  Calibrar a IA para funcionar de forma personalizada considerando as particularidades da sua empresa e processo de recrutamento
                </span>
              </li>
            </ul>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              <div className="flex items-center gap-3 bg-lia-bg-secondary rounded-xl p-4">
                <Clock className="w-5 h-5 text-lia-text-secondary" />
                <div>
                  <p className="lia-text-bold text-sm">Tempo estimado</p>
                  <p className="lia-text-small">3-5 minutos</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 bg-lia-bg-secondary rounded-xl p-4">
                <Lightbulb className="w-5 h-5 text-lia-text-secondary" />
                <div>
                  <p className="lia-text-bold text-sm">Pode continuar depois</p>
                  <p className="lia-text-small">Menu Configurações</p>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-status-warning/10 border border-status-warning/30 rounded-xl p-4">
              <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
              <p className="text-sm text-status-warning">
                Preencher essas informações é extremamente importante para que a plataforma seja configurada e customizada de forma adequada.
              </p>
            </div>
          </div>

          <div
            className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in duration-300"
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
          </div>
        </Card>
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
      <style>{`@keyframes check-pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.1); } }`}</style>
      {/* OPT-027: Decorative particles — static (replaced framer-motion infinite float) */}
      <div className="absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
        {[5,10,18,28,38,48,58,68,78,88,14,24,44,54,74,84,33,63,93,7].map((left, i) => (
          <div
            key={i}
            className="absolute w-3 h-3 lia-bg-lia-bg-primary opacity-5 rounded-full"
            style={{left: `${left}%`, top: `${(i * 5 + 3) % 100}%`}}
          />
        ))}
      </div>

      <div className="relative z-10 h-full flex items-center justify-center p-4">
        <div
          className="text-center max-w-2xl animate-in fade-in zoom-in-90 duration-700"
        >
          <div
            className="inline-flex items-center justify-center w-32 h-32 bg-lia-bg-primary rounded-full mb-8 animate-in zoom-in-50 duration-500"
          >
            <div
             
            >
              <CheckCircle className="w-16 h-16 text-[var(--wedo-green-pastel)]" />
            </div>
          </div>
          
          <h1
            className="text-xl font-semibold text-lia-text-primary mb-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            Parabéns! Configuração Concluída
          </h1>
          
          <div
            className="space-y-4 mb-10 animate-in fade-in duration-500"
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
          </div>
          
          <div
            className="space-y-4 animate-in fade-in duration-500"
          >
            <Button
              onClick={onClose}
              variant="primary" className="text-lg px-10 py-5"
            >
              Acessar Plataforma
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            
            <p
              className="lia-text-small animate-in fade-in duration-500"
            >
              Redirecionando automaticamente em {countdown} segundos...
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export function useUserData() {
  const storeUserData = useOnboardingStore((s) => s.userData)
  const setStoreUserData = useOnboardingStore((s) => s.setUserData)
  const clearOnboarding = useOnboardingStore((s) => s.clearOnboarding)

  const [userData, setUserData] = useState<UserData | null>(
    storeUserData as unknown as UserData | null
  )

  useEffect(() => {
    if (storeUserData) {
      setUserData(storeUserData as unknown as UserData)
    }
  }, [storeUserData])

  const updateUserData = (newData: Partial<UserData>) => {
    if (userData) {
      const updatedData = { ...userData, ...newData }
      setUserData(updatedData)
      setStoreUserData(updatedData as unknown as Record<string, unknown>)
    }
  }

  const logout = () => {
    setUserData(null)
    clearOnboarding()
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
  return useOnboardingStore.getState().canReplayOnboarding
}

export function triggerOnboarding() {
  useOnboardingStore.getState().setFirstAccess(true)
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
  data?: Record<string, unknown>
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
