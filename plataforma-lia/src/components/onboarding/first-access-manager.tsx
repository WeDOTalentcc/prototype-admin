"use client"

import './onboarding-styles.css'
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
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
  onAccessGranted: (userData: any) => void
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
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="lia-card max-w-md w-full"
        >
          <div className="text-center p-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-20 h-20 lia-bg-blue rounded-full flex items-center justify-center mx-auto mb-8"
            >
              <Loader2 className="w-10 h-10 lia-text-white" />
            </motion.div>

            <h2 className="lia-title-large lia-text-black mb-4">
              Validando seu acesso
            </h2>
            <p className="lia-text-medium">
              Verificando o token de convite e carregando os dados da sua empresa.
            </p>
          </div>
        </motion.div>
      </div>
    )
  }

  // Renderizar step de erro
  if (step === 'error') {
    return (
      <div className="lia-onboarding-container lia-bg-cream flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="lia-card max-w-md w-full"
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
                className="lia-button-primary w-full"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Tentar Novamente
              </Button>
              <Button
                variant="outline"
                onClick={onAccessDenied}
                className="lia-button-secondary w-full"
              >
                Voltar
              </Button>
            </div>
          </div>
        </motion.div>
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
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
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
        </motion.div>

        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12">

          {/* Dados da Empresa - Premium */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="lia-card">
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-blue rounded-2xl flex items-center justify-center">
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
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-gray-200">
                      <Building className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.razaoSocial}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-gray-200">
                      <MapPin className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.endereco}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-gray-200">
                      <Phone className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>{accessData?.companyData.telefone}</span>
                    </div>
                    <div className="flex items-center gap-4 p-4 lia-bg-cream rounded-md border border-gray-200">
                      <Calendar className="w-5 h-5 lia-text-blue flex-shrink-0" />
                      <span>Convite expira em {new Date(accessData?.expiresAt || '').toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                </div>

                {/* Contato que enviou o convite */}
                <div className="pt-8 border-t border-gray-200 mt-8">
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
            </div>
          </motion.div>

          {/* Formulário de Registro Premium */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <div className="lia-card">
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 lia-bg-coral rounded-2xl flex items-center justify-center">
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
                    className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                    className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                    className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                    className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                      className="w-full px-6 py-4 pr-14 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                    className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent lia-bg-white lia-font-sans lia-text-medium transition-all duration-200"
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
                    className="mt-1 w-5 h-5 rounded-md text-gray-600 dark:text-gray-400 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                  />
                  <label htmlFor="terms" className="lia-text-medium lia-text-black">
                    Aceito os <a href="#" className="lia-text-blue hover:underline lia-text-bold">termos de uso</a> e a{' '}
                    <a href="#" className="lia-text-blue hover:underline lia-text-bold">política de privacidade</a>
                  </label>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="p-6 lia-bg-salmon rounded-2xl border-2 border-status-error/30">
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
                  className="lia-button-primary w-full text-xl py-6"
                >
                  {isLoading ? (
                    <Loader2 className="w-6 h-6 animate-spin mr-3" />
                  ) : (
                    <ArrowRight className="w-6 h-6 mr-3" />
                  )}
                  {isLoading ? 'Criando conta...' : 'Criar Conta e Continuar'}
                </Button>
              </form>
            </div>
          </motion.div>
        </div>

        {/* Footer Premium */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="text-center mt-16"
        >
          <div className="inline-flex items-center gap-4 lia-font-sans lia-text-medium lia-text-black lia-bg-white rounded-full px-8 py-4 border border-gray-200">
            <Shield className="w-6 h-6 lia-text-mint" />
            Seus dados estão seguros e protegidos
          </div>
        </motion.div>
      </div>
    </div>
  )
}
