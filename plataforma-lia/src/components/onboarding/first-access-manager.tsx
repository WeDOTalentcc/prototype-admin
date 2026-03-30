"use client"

import './onboarding-styles.css'
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Shield, Mail, CheckCircle, AlertCircle, Loader2,
  Building, User, Eye, EyeOff, Key, ArrowRight,
  Globe, Phone, MapPin, Calendar, RefreshCw
} from "lucide-react"

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

  // Simular validação do token
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
      // Simular chamada API para validar token
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Mock data - em produção viria da API
      const mockData: FirstAccessData = {
        token: tokenValue,
        companyName: 'Sodexo Enterprise',
        contactName: 'Ana Silva',
        contactEmail: 'ana.silva@sodexo.com',
        contactPhone: '+55 11 99999-0001',
        companyData: {
          razaoSocial: 'Sodexo do Brasil Comercial Ltda',
          endereco: 'Av. Paulista, 1000 - São Paulo, SP',
          telefone: '+55 11 3000-0000'
        },
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date().toISOString()
      }

      // Verificar se token não expirou
      if (new Date(mockData.expiresAt) < new Date()) {
        throw new Error('Token expirado')
      }

      setAccessData(mockData)
      setUserData(prev => ({
        ...prev,
        name: mockData.contactName,
        email: mockData.contactEmail,
        phone: mockData.contactPhone || ''
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
      // Simular registro do usuário
      await new Promise(resolve => setTimeout(resolve, 1500))

      const newUser = {
        id: Date.now().toString(),
        ...userData,
        companyId: accessData?.token,
        companyName: accessData?.companyName,
        isFirstAccess: true,
        permissions: ['admin', 'recruitment', 'users', 'settings'],
        createdAt: new Date().toISOString()
      }

      // Salvar flag de primeiro acesso
      localStorage.setItem('lia_first_access', 'true')
      localStorage.setItem('lia_user_data', JSON.stringify(newUser))

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
    // Limpar flag de primeiro acesso
    localStorage.removeItem('lia_first_access')

    // Notificar componente pai que o acesso foi concedido
    onAccessGranted({
      ...userData,
      companyData: accessData?.companyData,
      companyName: accessData?.companyName,
      isFirstAccess: false
    })
  }

  const handleOnboardingSkip = () => {
    // Mesmo fluxo do complete, mas mantém flag de "pode ver onboarding novamente"
    localStorage.setItem('lia_can_replay_onboarding', 'true')
    handleOnboardingComplete()
  }

  // Renderizar step de validação
  if (step === 'validating') {
    return (
      <div className="lia-onboarding-container lia-bg-cream flex items-center justify-center p-8">
        <Card
          className="max-w-md w-full animate-in fade-in zoom-in-95 duration-500"
        >
          <div className="text-center p-8">
            <div
              className="w-20 h-20 lia-bg-blue rounded-full flex items-center justify-center mx-auto mb-8"
            >
              <Loader2 className="w-10 h-10 lia-text-white animate-spin" />
            </div>

            <h2 className="lia-title-large lia-text-black mb-4">
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

            <h2 className="lia-title-large lia-text-black mb-4">
              Acesso Negado
            </h2>
            <p className="lia-text-medium lia-text-black mb-8">
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

          <h1 className="lia-title-hero lia-text-black mb-6">
            Bem-vindo à Plataforma LIA
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
            <Card className="">
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-blue rounded-xl flex items-center justify-center">
                    <Building className="w-8 h-8 lia-text-white" />
                  </div>
                  <div>
                    <h3 className="lia-title-medium lia-text-black">Dados da Empresa</h3>
                    <p className="lia-text-small">Informações do seu convite</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <h4 className="lia-title-medium lia-text-black mb-3">
                      {accessData?.companyName}
                    </h4>
                    <Badge className="lia-bg-mint lia-text-black border-0 px-4 py-2 lia-font-sans font-semibold">
                      ✓ Convite válido
                    </Badge>
                  </div>

                  <div className="space-y-4 lia-text-medium">
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-lia-border-subtle">
                      <Building className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.razaoSocial}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-lia-border-subtle">
                      <MapPin className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.endereco}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-lia-border-subtle">
                      <Phone className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.telefone}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-lia-border-subtle">
                      <Calendar className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>Convite expira em {new Date(accessData?.expiresAt || '').toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                </div>

                {/* Contato que enviou o convite */}
                <div className="pt-8 border-t border-lia-border-subtle mt-8">
                  <h4 className="lia-title-medium lia-text-black mb-4">
                    Convite enviado por:
                  </h4>
                  <div className="flex items-center gap-4 p-4 lia-bg-lavender rounded-md">
                    <div className="w-14 h-14 lia-bg-blue rounded-full flex items-center justify-center">
                      <User className="w-7 h-7 lia-text-white" />
                    </div>
                    <div>
                      <p className="lia-text-bold lia-text-black text-lg">
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
            <Card className="">
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-coral rounded-xl flex items-center justify-center">
                    <User className="w-8 h-8 lia-text-white" />
                  </div>
                  <div>
                    <h3 className="lia-title-medium lia-text-black">Criar sua Conta</h3>
                    <p className="lia-text-small">Configure seu acesso à plataforma</p>
                  </div>
                </div>
              </div>

              <form className="space-y-6">
                {/* Nome */}
                <div>
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Nome Completo *
                  </label>
                  <input
                    type="text"
                    value={userData.name}
                    onChange={(e) => setUserData(prev => ({...prev, name: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
                    placeholder="Seu nome completo"
                  />
                </div>

                {/* Email */}
                <div>
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Email Corporativo *
                  </label>
                  <input
                    type="email"
                    value={userData.email}
                    onChange={(e) => setUserData(prev => ({...prev, email: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
                    placeholder="seu.email@empresa.com"
                  />
                </div>

                {/* Telefone */}
                <div>
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Telefone
                  </label>
                  <input
                    type="tel"
                    value={userData.phone}
                    onChange={(e) => setUserData(prev => ({...prev, phone: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
                    placeholder="+55 11 99999-9999"
                  />
                </div>

                {/* Cargo */}
                <div>
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Seu Cargo
                  </label>
                  <select
                    value={userData.role}
                    onChange={(e) => setUserData(prev => ({...prev, role: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
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
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Senha *
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={userData.password}
                      onChange={(e) => setUserData(prev => ({...prev, password: e.target.value}))}
                      className="w-full px-6 py-4 pr-14 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
                      placeholder="Mínimo 8 caracteres"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 transform -translate-y-1/2 lia-text-black hover:lia-text-blue transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Confirmar Senha */}
                <div>
                  <label className="block lia-text-bold lia-text-black mb-3">
                    Confirmar Senha *
                  </label>
                  <input
                    type="password"
                    value={userData.confirmPassword}
                    onChange={(e) => setUserData(prev => ({...prev, confirmPassword: e.target.value}))}
                    className="w-full px-6 py-4 border-2 border-lia-border-subtle rounded-lg focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-lia-bg-primary lia-font-sans lia-text-medium transition-colors duration-200"
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
                    className="mt-1 w-5 h-5 rounded-md text-lia-text-secondary dark:text-lia-text-tertiary focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                  />
                  <label htmlFor="terms" className="lia-text-medium lia-text-black">
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
                    <Loader2 className="w-6 h-6 animate-spin mr-3" />
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
          <div className="inline-flex items-center gap-4 lia-font-sans lia-text-medium lia-text-black lia-bg-lia-bg-primary rounded-full px-8 py-4 border border-lia-border-subtle">
            <Shield className="w-6 h-6 lia-text-mint" />
            Seus dados estão seguros e protegidos
          </div>
        </div>
      </div>
    </div>
  )
}
