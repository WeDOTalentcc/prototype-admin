"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { useAuth } from "@/components/auth-context"
import {
  Eye,
  EyeOff,
  Loader2,
  Building2
} from "lucide-react"

interface SSOCheckResult {
  sso_available: boolean
  organization_id?: string
  company_name?: string
}

export function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [rememberMe, setRememberMe] = useState(false)
  const [ssoInfo, setSsoInfo] = useState<SSOCheckResult | null>(null)
  const [checkingSSO, setCheckingSSO] = useState(false)

  const { login } = useAuth()

  const checkSSODomain = useCallback(async (emailValue: string) => {
    if (!emailValue || !emailValue.includes('@')) {
      setSsoInfo(null)
      return
    }

    setCheckingSSO(true)
    try {
      const response = await fetch(`/api/backend-proxy/auth/check-sso-domain?email=${encodeURIComponent(emailValue)}`)
      if (response.ok) {
        const data: SSOCheckResult = await response.json()
        setSsoInfo(data)
      } else {
        setSsoInfo(null)
      }
    } catch (error) {
      setSsoInfo(null)
    } finally {
      setCheckingSSO(false)
    }
  }, [])

  const handleEmailBlur = () => {
    checkSSODomain(email)
  }

  const handleSSOLogin = () => {
    if (ssoInfo?.organization_id) {
      window.location.href = `/api/auth/workos/sso?organization_id=${ssoInfo.organization_id}`
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      await new Promise(resolve => setTimeout(resolve, 1500))

      if (email === "ana.silva@sodexo.com" && password === "123456") {
        login({
          name: "Ana Silva",
          email: "ana.silva@sodexo.com",
          role: "Recrutadora Sênior",
          company: "Sodexo"
        })
      } else {
        setError("Email ou senha inválidos")
      }
    } catch (error) {
      setError("Erro ao fazer login")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocialLogin = (provider: string) => {
    login({
      name: "Ana Silva",
      email: "ana.silva@sodexo.com",
      role: "Recrutadora Sênior",
      company: "Sodexo"
    })
  }

  return (
    <div
      className="min-h-screen flex font-open-sans relative overflow-hidden"
      style={{ background: 'var(--login-bg-gradient)' }}
    >
      {/* Cloud blobs - estático, sem animação */}
      <div className="absolute inset-0 pointer-events-none z-0">
        {/* Nuvem grande - topo direito */}
        <div style={{ position: 'absolute', width: '720px', height: '460px', top: '-90px', right: '-120px', background: 'rgba(255,255,255,0.88)', borderRadius: '50%', filter: 'blur(72px)' }} />
        {/* Nuvem grande - centro direito */}
        <div style={{ position: 'absolute', width: '560px', height: '490px', top: '28%', right: '6%', background: 'rgba(255,255,255,0.82)', borderRadius: '50%', filter: 'blur(82px)' }} />
        {/* Nuvem extra - detalhe topo direito */}
        <div style={{ position: 'absolute', width: '320px', height: '260px', top: '8%', right: '28%', background: 'rgba(255,255,255,0.70)', borderRadius: '50%', filter: 'blur(55px)' }} />
        {/* Nuvem grande - baixo direito */}
        <div style={{ position: 'absolute', width: '780px', height: '390px', bottom: '-90px', right: '3%', background: 'rgba(255,255,255,0.78)', borderRadius: '50%', filter: 'blur(90px)' }} />
        {/* Nuvem centro esquerdo */}
        <div style={{ position: 'absolute', width: '500px', height: '330px', top: '42%', left: '-90px', background: 'rgba(255,255,255,0.68)', borderRadius: '50%', filter: 'blur(76px)' }} />
        {/* Nuvem sutil - topo esquerdo */}
        <div style={{ position: 'absolute', width: '360px', height: '260px', top: '4%', left: '12%', background: 'rgba(255,255,255,0.58)', borderRadius: '50%', filter: 'blur(64px)' }} />
        {/* Nuvem baixo esquerdo */}
        <div style={{ position: 'absolute', width: '520px', height: '310px', bottom: '4%', left: '3%', background: 'rgba(255,255,255,0.64)', borderRadius: '50%', filter: 'blur(80px)' }} />
        {/* Nuvem central pequena */}
        <div style={{ position: 'absolute', width: '280px', height: '200px', top: '55%', left: '35%', background: 'rgba(255,255,255,0.52)', borderRadius: '50%', filter: 'blur(60px)' }} />
      </div>

      {/* Left Side - Content */}
      <div className="hidden lg:flex lg:w-3/5 flex-col justify-between p-12 relative">
        {/* Content - z-index acima das nuvens */}
        <div className="relative z-10 flex flex-col justify-center h-full">
          {/* Logo */}
          <div className="absolute top-0 left-0">
            <div className="flex items-center space-x-3">
              <WeDOLogo className="text-xl text-gray-950 dark:text-gray-50" />
            </div>
          </div>

          {/* Main Content - Centralizado */}
          <div className="max-w-2xl">
            {/* Header Principal */}
            <div className="mb-6">
              <h1 className="text-8xl font-bold text-gray-950 dark:text-gray-50 leading-none mb-4">
                Prazer, Lia
              </h1>
              <p className="text-2xl font-bold text-gray-800 dark:text-gray-200 leading-relaxed">
                Sua assistente de IA de recrutamento.
              </p>
            </div>

            {/* Feature Points - Sem bullets */}
            <div className="space-y-3 mt-12">
              <p className="text-lg text-gray-700 leading-relaxed">Automação inteligente, dados organizados e acessiveis,  processos como nunca vistos antes.</p>
              <p className="text-lg text-gray-700 leading-relaxed"></p>
              <p className="text-lg text-gray-700 leading-relaxed">IA nativa que aprende com você e acelera todo o processo de recrutamento.</p>
              <p className="text-lg text-gray-800 dark:text-gray-200 leading-relaxed font-semibold">Simples. Inteligente. Revolucionário.</p>
            </div>
          </div>
        </div>

        {/* Bottom Content */}
        <div className="relative z-10">
          {/* Bottom - Company Logos */}
          <div className="space-y-4">
            <p className="text-gray-800 dark:text-gray-200 text-sm">
              Empresas inovadoras que trabalham com a LIA.
            </p>
            <div className="flex items-center space-x-8">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Sodexo_logo.svg/2560px-Sodexo_logo.svg.png"
                alt="Sodexo"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/ArcelorMittal.svg/2560px-ArcelorMittal.svg.png"
                alt="ArcelorMittal"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/8/8d/Celcoin.png"
                alt="Celcoin"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://cdn.prod.website-files.com/6154ac78893abf1d1530f251/665dde0177b7a8e897170acd_Wellhub_Horizontal-Logo_Magenta.webp"
                alt="Wellhub"
                className="h-8 object-contain opacity-60"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-2/5 bg-white flex flex-col shadow-2xl relative z-10">
        {/* Demo Notice */}
        <div className="p-4 text-right">
          <div className="text-xs text-gray-800 dark:text-gray-200">
            <span className="font-medium">Demo:</span> ana.silva@sodexo.com / 123456
          </div>
        </div>

        {/* Login Card */}
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md p-10">
            {/* Header */}
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-gray-950 dark:text-gray-50 mb-3">Bem-vindo(a)!</h2>
              <p className="text-gray-800 dark:text-gray-200 text-base leading-relaxed">
                Informe suas credenciais para participar do projeto experimental de tecnologia em recrutamento com a LIA.
              </p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              {/* Email Field */}
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Email
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onBlur={handleEmailBlur}
                    placeholder="Digite seu email"
                    className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                    required
                  />
                  {checkingSSO && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                    </div>
                  )}
                </div>
              </div>

              {/* SSO Available Notice */}
              {ssoInfo?.sso_available && (
                <div className="p-4 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600">
                  <div className="flex items-start gap-3">
                    <Building2 className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-wedo-cyan-dark text-sm font-medium">
                        SSO Corporativo Detectado
                      </p>
                      <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                        {ssoInfo.company_name ? `Sua empresa (${ssoInfo.company_name}) utiliza login corporativo.` : 'Sua empresa utiliza login corporativo.'}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    onClick={handleSSOLogin}
                    className="w-full mt-3 py-3 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-md transition-all font-medium flex items-center justify-center gap-2"
                  >
                    <Building2 className="w-4 h-4" />
                    Entrar com SSO Corporativo
                  </Button>
                </div>
              )}

              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Senha
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Digite sua senha"
                    className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600 hover:text-gray-700"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 text-gray-950 dark:text-gray-50 border-gray-300 rounded focus:ring-gray-900"
                  />
                  <span className="ml-2 text-sm text-gray-800 dark:text-gray-200">Lembrar de mim</span>
                </label>
                <a href="/forgot-password" className="text-sm text-gray-800 dark:text-gray-200 hover:text-gray-950 dark:hover:text-gray-50 transition-colors">
                  Esqueceu a senha?
                </a>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                  <p className="text-status-error text-sm font-medium">{error}</p>
                </div>
              )}

              {/* Login Button */}
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md transition-all font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Entrando...
                  </>
                ) : (
                  "Entrar"
                )}
              </Button>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200">Ou continue com:</span>
                </div>
              </div>

              {/* Social Login Buttons */}
              <div className="space-y-3">
                <Button
                  type="button"
                  onClick={() => handleSocialLogin("Google")}
                  variant="outline"
                  className="w-full py-3 border border-gray-200 hover:border-gray-300 rounded-md transition-all flex items-center justify-center gap-3 bg-white font-medium"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continuar com Google
                </Button>

                <Button
                  type="button"
                  onClick={() => handleSocialLogin("Microsoft")}
                  variant="outline"
                  className="w-full py-3 border border-gray-200 hover:border-gray-300 rounded-md transition-all flex items-center justify-center gap-3 bg-white font-medium"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#F25022" d="M1 1h10.5v10.5H1z"/>
                    <path fill="#00A4EF" d="M12.5 1H23v10.5H12.5z"/>
                    <path fill="#7FBA00" d="M1 12.5h10.5V23H1z"/>
                    <path fill="#FFB900" d="M12.5 12.5H23V23H12.5z"/>
                  </svg>
                  Continuar com Microsoft
                </Button>
              </div>

              {/* Sign Up Link */}
              <p className="text-center text-gray-800 dark:text-gray-200 text-sm">
                Não tem uma conta?{" "}
                <a href="/register" className="text-gray-950 dark:text-gray-50 font-medium hover:underline">
                  Cadastre-se aqui
                </a>
              </p>

              {/* Demo & Onboarding Section */}
              <div className="border-t border-gray-200 pt-6 mt-6">
                <h3 className="text-center text-sm font-medium text-gray-800 dark:text-gray-200 mb-4">
                  🚀 Demonstrações da Plataforma
                </h3>
                <div className="space-y-3">
                  <Button
                    type="button"
                    onClick={() => window.location.href = '/demo-onboarding'}
                    variant="outline"
                    className="w-full py-3 border-2 border-wedo-purple/30 hover:border-wedo-purple/30 rounded-md transition-all flex items-center justify-center gap-3 bg-wedo-purple/10 hover:bg-wedo-purple/15 font-medium text-wedo-purple"
                  >
                    <span className="text-lg">🌟</span>
                    Tour de Onboarding Completo
                  </Button>

                  <Button
                    type="button"
                    onClick={() => {
                      // Trigger onboarding for logged user
                      localStorage.setItem('lia_first_access', 'true')
                      // Login with demo user first
                      login({
                        name: "Demo User",
                        email: "demo@wedotalent.com",
                        role: "Recrutador",
                        company: "WeDo Talent Demo"
                      })
                    }}
                    variant="outline"
 className="w-full py-3 border-2 border-gray-300 hover:border-gray-300 rounded-md transition-all flex items-center justify-center gap-3 hover:bg-gray-100 font-medium text-wedo-cyan-dark"
                  >
                    <span className="text-lg">🎯</span>
                    Acesso Demo + Onboarding
                  </Button>

                  <Button
                    type="button"
                    onClick={() => {
                      // Login and set replay flag
                      localStorage.setItem('lia_can_replay_onboarding', 'true')
                      login({
                        name: "Ana Silva",
                        email: "ana.silva@sodexo.com",
                        role: "Recrutadora Sênior",
                        company: "Sodexo"
                      })
                    }}
                    variant="outline"
                    className="w-full py-3 border-2 border-status-success/30 hover:border-status-success/30 rounded-md transition-all flex items-center justify-center gap-3 bg-status-success/10 hover:bg-status-success/15 font-medium text-status-success"
                  >
                    <span className="text-lg">🔄</span>
                    Login + Replay Onboarding
                  </Button>
                </div>

                <div className="mt-4 p-3 bg-status-warning/10 border border-status-warning/30 rounded-md">
                  <p className="text-xs text-status-warning text-center">
                    💡 <strong>Dica:</strong> Use estes botões para testar o sistema de onboarding completo da plataforma LIA
                  </p>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 text-center text-xs text-gray-800 dark:text-gray-200 space-y-1">
          <p>
            Tecnologia avançada para Recursos Humanos do futuro.
            <br />
            Desenvolvida pela WeDOTalent, HRTech do Grupo Talentese.
          </p>
          <p>© 2024 WeDOTalent. Todos os direitos reservados.</p>
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="lg:hidden w-full bg-gray-50 p-6">
        {/* Demo Notice */}
        <div className="text-center mb-6">
          <div className="text-xs text-gray-800 dark:text-gray-200">
            <span className="font-medium">Demo:</span> ana.silva@sodexo.com / 123456
          </div>
        </div>

        {/* Mobile Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-black rounded-md flex items-center justify-center">
              <WeDOLogo className="h-4 text-white" />
            </div>
            <div className="text-lg font-bold">WeDOTalent</div>
          </div>
          <h1 className="text-4xl font-bold text-gray-950 dark:text-gray-50 mb-3 leading-none">
            Prazer, Lia
          </h1>
          <p className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-6">
            Sua parceira de Inteligência Artificial no recrutamento.
          </p>
          <div className="space-y-2 text-base text-gray-600">
            <p>Automação inteligente e processos como nunca vistos antes.</p>
            <p>Dados organizados e acessíveis.</p>
            <p>IA nativa que aprende com você e acelera todo o processo de recrutamento.</p>
            <p className="font-semibold text-gray-800 dark:text-gray-200">Simples. Inteligente. Revolucionário.</p>
          </div>
        </div>

        {/* Mobile Login Form */}
        <div className="bg-white rounded-2xl p-8">
          <div className="text-center mb-5">
            <h2 className="text-2xl font-bold text-gray-950 dark:text-gray-50 mb-3">Bem-vindo de volta!</h2>
            <p className="text-gray-800 dark:text-gray-200 text-base leading-relaxed">
              Informe suas credenciais para participar do projeto experimental de tecnologia em recrutamento com a LIA.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Email</label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={handleEmailBlur}
                  placeholder="Digite seu email"
                  className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                  required
                />
                {checkingSSO && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  </div>
                )}
              </div>
            </div>

            {/* SSO Available Notice - Mobile */}
            {ssoInfo?.sso_available && (
              <div className="p-4 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600">
                <div className="flex items-start gap-3">
                  <Building2 className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-wedo-cyan-dark text-sm font-medium">
                      SSO Corporativo Detectado
                    </p>
                    <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                      {ssoInfo.company_name ? `Sua empresa (${ssoInfo.company_name}) utiliza login corporativo.` : 'Sua empresa utiliza login corporativo.'}
                    </p>
                  </div>
                </div>
                <Button
                  type="button"
                  onClick={handleSSOLogin}
                  className="w-full mt-3 py-3 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-md transition-all font-medium flex items-center justify-center gap-2"
                >
                  <Building2 className="w-4 h-4" />
                  Entrar com SSO Corporativo
                </Button>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Digite sua senha"
                  className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 text-gray-950 dark:text-gray-50 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-600">Lembrar de mim</span>
              </label>
              <a href="/forgot-password" className="text-sm text-gray-600">Esqueceu a senha?</a>
            </div>

            {error && (
              <div className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                <p className="text-status-error text-sm">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>

            <div className="text-center">
              <p className="text-sm text-gray-800 dark:text-gray-200 mb-3">Ou continue com:</p>
              <Button
                type="button"
                onClick={() => handleSocialLogin("Google")}
                variant="outline"
                className="w-full py-3 border border-gray-200 rounded-md mb-3"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" className="mr-2">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </Button>
            </div>

            <p className="text-center text-gray-600 text-sm">
              Não tem uma conta?{" "}
              <a href="/register" className="text-gray-950 dark:text-gray-50 font-medium hover:underline">
                Cadastre-se aqui
              </a>
            </p>
          </form>
        </div>

        {/* Mobile Footer */}
        <div className="text-center text-xs text-gray-800 dark:text-gray-200 mt-6 space-y-2">
          <p>Tecnologia avançada para Recursos Humanos do futuro.</p>
          <p>© 2024 WeDOTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
