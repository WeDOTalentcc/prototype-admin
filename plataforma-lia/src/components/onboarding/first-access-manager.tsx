"use client"

import './onboarding-styles.css'
import { useState, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { useOnboardingStore } from"@/stores/onboarding-store"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Shield, Mail, CheckCircle, AlertCircle, Loader2,
  Building, User, Eye, EyeOff, Key, ArrowRight,
  Globe, Phone, MapPin, Calendar, RefreshCw
} from"lucide-react"

interface FirstAccessData {
  token: string
  companyName: string
  contactName: string
  contactEmail: string
  contactPhone?: string
  companyData: {
    razaoSocial: string
    endereco: string
    telefone: string
  }
  expiresAt: string
  createdAt: string
}

interface FirstAccessManagerProps {
  token?: string
  onAccessGranted: (userData: Record<string, unknown>) => void
  onAccessDenied: () => void
}

export function FirstAccessManager({ token, onAccessGranted, onAccessDenied }: FirstAccessManagerProps) {
  const [step, setStep] = useState<'validating' | 'register' | 'onboarding' | 'error'>('validating')
  const [accessData, setAccessData] = useState<FirstAccessData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  // Form data para registro do usuário
  const [userData, setUserData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    role: 'Recrutador',
    acceptTerms: false
  })

  useEffect(() => {
    if (token) {
      validateToken(token)
    } else {
      setStep('error')
      setError('Token de acesso não fornecido')
    }
  }, [token])

  const validateToken = async (tokenValue: string) => {
    setIsLoading(true)

    try {
      const response = await fetch(`/api/backend-proxy/onboarding/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenValue, action: 'validate' }),
      })

      if (!response.ok) {
        throw new Error('Token inválido ou expirado')
      }

      const raw = await response.json()
      const data: FirstAccessData = {
        token: raw.token || tokenValue,
        companyName: raw.companyName || raw.company_name || '',
        contactName: raw.contactName || raw.contact_name || '',
        contactEmail: raw.contactEmail || raw.contact_email || '',
        contactPhone: raw.contactPhone || raw.contact_phone || '',
        companyData: {
          razaoSocial: raw.companyData?.razaoSocial || raw.company_data?.razao_social || raw.companyName || raw.company_name || '',
          endereco: raw.companyData?.endereco || raw.company_data?.endereco || '',
          telefone: raw.companyData?.telefone || raw.company_data?.telefone || '',
        },
        expiresAt: raw.expiresAt || raw.expires_at || '',
        createdAt: raw.createdAt || raw.created_at || new Date().toISOString(),
      }

      if (!data.expiresAt) {
        throw new Error('Resposta inválida do servidor')
      }

      if (new Date(data.expiresAt) < new Date()) {
        throw new Error('Token expirado')
      }

      setAccessData(data)
      setUserData(prev => ({
        ...prev,
        name: data.contactName,
        email: data.contactEmail,
        phone: data.contactPhone || ''
      }))
      setStep('register')

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Token inválido')
      setStep('error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!validateForm()) return

    setIsLoading(true)

    try {
      const response = await fetch('/api/backend-proxy/onboarding/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'register',
          ...userData,
          token: accessData?.token,
          companyName: accessData?.companyName,
        }),
      })

      let newUser: Record<string, unknown>

      if (response.ok) {
        newUser = await response.json()
      } else {
        throw new Error('Erro ao criar conta')
      }

      useOnboardingStore.getState().setFirstAccess(true)
      useOnboardingStore.getState().setUserData(newUser as Record<string, unknown>)

      setStep('onboarding')

    } catch (err) {
      setError('Erro ao criar conta. Tente novamente.')
    } finally {
      setIsLoading(false)
    }
  }

  const validateForm = () => {
    if (!userData.name || userData.name.length < 2) {
      setError('Nome deve ter pelo menos 2 caracteres')
      return false
    }

    if (!userData.email || !userData.email.includes('@')) {
      setError('Email inválido')
      return false
    }

    if (!userData.password || userData.password.length < 8) {
      setError('Senha deve ter pelo menos 8 caracteres')
      return false
    }

    if (userData.password !== userData.confirmPassword) {
      setError('Senhas não coincidem')
      return false
    }

    if (!userData.acceptTerms) {
      setError('Você deve aceitar os termos de uso')
      return false
    }

    setError(null)
    return true
  }

  const handleOnboardingComplete = () => {
    useOnboardingStore.getState().setFirstAccess(false)

    onAccessGranted({
      ...userData,
      companyData: accessData?.companyData,
      companyName: accessData?.companyName,
      isFirstAccess: false
    })
  }

  const handleOnboardingSkip = () => {
    useOnboardingStore.getState().setCanReplayOnboarding(true)
    handleOnboardingComplete()
  }

  // Renderizar step de validação
  if (step === 'validating') {
    return (
      <div className="lia-onboarding-container lia-bg-cream flex items-center justify-center p-8">
        <Card
          className="max-w-md w-full animate-in fade-in zoom-in-95 duration-500"
        >
          <div className="text-center p-8" role="status" aria-live="polite" aria-label="Carregando...">
            <div
              className="w-20 h-20 lia-bg-blue rounded-full flex items-center justify-center mx-auto mb-8"
            >
              <Loader2 className="w-10 h-10 lia-text-white animate-spin motion-reduce:animate-none" />
            </div>

            <h2 className="lia-title-large text-lia-text-primary mb-4">
              Validando seu acesso
            </h2>
            <p className="lia-text-medium">
              Verificando o token de convite e carregando os dados da sua empresa.
            </p>
          </div>
        </Card>
      </div>
    )
  }

  // Renderizar step de erro
  if (step === 'error') {
    return (
      <div className="lia-onboarding-container lia-bg-cream flex items-center justify-center p-8">
        <Card
          className="max-w-md w-full animate-in fade-in slide-in-from-bottom-4 duration-500"
        >
          <div className="text-center p-8">
            <div className="w-20 h-20 lia-bg-coral rounded-full flex items-center justify-center mx-auto mb-8">
              <AlertCircle className="w-10 h-10 lia-text-white" />
            </div>

            <h2 className="lia-title-large text-lia-text-primary mb-4">
              Acesso Negado
            </h2>
            <p className="lia-text-medium text-lia-text-primary mb-8">
              {error || 'Token inválido ou expirado'}
            </p>

            <div className="space-y-4">
              <Button
                onClick={() => window.location.reload()}
                variant="primary" className="w-full"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Tentar Novamente
              </Button>
              <Button
                variant="secondary"
                onClick={onAccessDenied}
                className="w-full"
              >
                Voltar
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  // Skip diretamente para o conteúdo (onboarding slides removidos)
  if (step === 'onboarding') {
    handleOnboardingComplete()
    return null
  }

  // Renderizar step de registro
  return (
    <div className="lia-onboarding-container lia-bg-cream">
      <div className="container mx-auto px-8 py-12">

        {/* Header Premium */}
        <div
          className="text-center mb-16 animate-in fade-in slide-in-from-top-6 duration-700"
        >
          {/* Logo LIA blob */}
          <div className="relative w-32 h-32 mx-auto mb-8">
            <div className="lia-blob-organic w-full h-full flex items-center justify-center">
              <div className="lia-text-coral text-6xl lia-font-sans font-bold">L</div>
            </div>
          </div>

          <h1 className="lia-title-hero text-lia-text-primary mb-6">
            Bem-vindo ao WeDOTalent
          </h1>
          <p className="lia-text-large max-w-3xl mx-auto leading-relaxed">
            Você foi convidado para acessar a plataforma de recrutamento mais avançada do mercado.
            Vamos criar sua conta e começar esta jornada transformadora?
          </p>
        </div>

        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12">

          {/* Dados da Empresa - Premium */}
          <div
            className="animate-in fade-in slide-in-from-left-6 duration-700"
          >
            <Card >
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-blue rounded-xl flex items-center justify-center">
                    <Building className="w-8 h-8 lia-text-white" />
                  </div>
                  <div>
                    <h3 className="lia-title-medium text-lia-text-primary">Dados da Empresa</h3>
                    <p className="lia-text-small">Informações do seu convite</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <h4 className="lia-title-medium text-lia-text-primary mb-3">
                      {accessData?.companyName}
                    </h4>
                    <Chip variant="neutral" muted className="lia-bg-mint text-lia-text-primary border-0 px-1.5 py-0 lia-font-sans">
                      ✓ Convite válido
                    </Chip>
                  </div>

                  <div className="space-y-4 lia-text-medium">
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-xl border border-lia-border-subtle">
                      <Building className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData?.razaoSocial}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-xl border border-lia-border-subtle">
                      <MapPin className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData?.endereco}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-xl border border-lia-border-subtle">
                      <Phone className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData?.telefone}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-xl border border-lia-border-subtle">
                      <Calendar className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>Convite expira em {new Date(accessData?.expiresAt || '').toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                </div>

                {/* Contato que enviou o convite */}
                <div className="pt-8 border-t border-lia-border-subtle mt-8">
                  <h4 className="lia-title-medium text-lia-text-primary mb-4">
                    Convite enviado por:
                  </h4>
                  <div className="flex items-center gap-4 p-4 lia-bg-lavender rounded-xl">
                    <div className="w-14 h-14 lia-bg-blue rounded-full flex items-center justify-center">
                      <User className="w-7 h-7 lia-text-white" />
                    </div>
                    <div>
                      <p className="lia-text-bold text-lia-text-primary text-lg">
                        {accessData?.contactName}
                      </p>
                      <p className="lia-text-medium">
                        {accessData?.contactEmail}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Formulário de Registro Premium */}
          <div
            className="animate-in fade-in slide-in-from-right-6 duration-700"
          >
            <Card >
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-coral rounded-xl flex items-center justify-center">
                    <User className="w-8 h-8 lia-text-white" />
                  </div>
                  <div>
                    <h3 className="lia-title-medium text-lia-text-primary">Criar sua Conta</h3>
                    <p className="lia-text-small">Configure seu acesso à plataforma</p>
                  </div>
                </div>
              </div>

              <form className="space-y-6">
                {/* Nome */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Nome Completo *
                  </label>
                  <input
                    type="text"
                    value={userData.name}
                    onChange={(e) => setUserData(prev => ({...prev, name: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                    placeholder="Seu nome completo"
                  />
                </div>

                {/* Email */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Email Corporativo *
                  </label>
                  <input
                    type="email"
                    value={userData.email}
                    onChange={(e) => setUserData(prev => ({...prev, email: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                    placeholder="seu.email@empresa.com"
                  />
                </div>

                {/* Telefone */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Telefone
                  </label>
                  <input
                    type="tel"
                    value={userData.phone}
                    onChange={(e) => setUserData(prev => ({...prev, phone: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                    placeholder="+55 11 99999-9999"
                  />
                </div>

                {/* Cargo */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Seu Cargo
                  </label>
                  <select
                    value={userData.role}
                    onChange={(e) => setUserData(prev => ({...prev, role: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                  >
                    <option value="Recrutador">Recrutador</option>
                    <option value="Coordenador de RH">Coordenador de RH</option>
                    <option value="Gerente de RH">Gerente de RH</option>
                    <option value="Diretor de RH">Diretor de RH</option>
                    <option value="Head de Talent Acquisition">Head de Talent Acquisition</option>
                  </select>
                </div>

                {/* Senha */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Senha *
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ?"text" :"password"}
                      value={userData.password}
                      onChange={(e) => setUserData(prev => ({...prev, password: e.target.value}))}
                      className="w-full px-6 py-4 pr-14 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                      placeholder="Mínimo 8 caracteres"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 transform -translate-y-1/2 text-lia-text-primary hover:text-wedo-cyan transition-colors motion-reduce:transition-none"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Confirmar Senha */}
                <div>
                  <label className="block lia-text-bold text-lia-text-primary mb-3">
                    Confirmar Senha *
                  </label>
                  <input
                    type="password"
                    value={userData.confirmPassword}
                    onChange={(e) => setUserData(prev => ({...prev, confirmPassword: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors motion-reduce:transition-none duration-200"
                    placeholder="Confirme sua senha"
                  />
                </div>

                {/* Termos */}
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    id="terms"
                    checked={userData.acceptTerms}
                    onChange={(e) => setUserData(prev => ({...prev, acceptTerms: e.target.checked}))}
                    className="mt-1 w-5 h-5 rounded-md text-lia-text-secondary focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20"
                  />
                  <label htmlFor="terms" className="lia-text-medium text-lia-text-primary">
                    Aceito os <a href="#" className="lia-text-blue hover:underline lia-text-bold">termos de uso</a> e a{' '}
                    <a href="#" className="lia-text-blue hover:underline lia-text-bold">política de privacidade</a>
                  </label>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="p-6 lia-bg-salmon rounded-xl border border-status-error/30">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 lia-text-coral flex-shrink-0" />
                      <span className="lia-text-medium lia-text-coral lia-font-sans font-semibold">{error}</span>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="button"
                  onClick={handleRegister}
                  disabled={isLoading}
                  variant="primary" className="w-full text-xl py-6"
                >
                  {isLoading ? (
                    <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none mr-3" />
                  ) : (
                    <ArrowRight className="w-6 h-6 mr-3" />
                  )}
                  {isLoading ? 'Criando conta...' : 'Criar Conta e Continuar'}
                </Button>
              </form>
            </Card>
          </div>
        </div>

        {/* Footer Premium */}
        <div
          className="text-center mt-16 animate-in fade-in slide-in-from-bottom-4 duration-700"
        >
          <div className="inline-flex items-center gap-4 lia-font-sans lia-text-medium text-lia-text-primary lia-bg-lia-bg-primary rounded-full px-8 py-4 border border-lia-border-subtle">
            <Shield className="w-6 h-6 lia-text-mint" />
            Seus dados estão seguros e protegidos
          </div>
        </div>
      </div>
    </div>
  )
}
