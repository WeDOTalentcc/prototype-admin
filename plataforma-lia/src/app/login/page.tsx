"use client"

import { useState, FormEvent } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Brain
} from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading } = useJWTAuth()
  
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setIsSubmitting(true)

    try {
      await login(email, password)
      router.push("/login/welcome")
    } catch (err: any) {
      setError(err.message || "Falha ao fazer login. Verifique suas credenciais.")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600 dark:text-gray-400" />
      </div>
    )
  }

  return (
    <div
      className="min-h-screen flex font-['Open_Sans',sans-serif] relative overflow-hidden"
      style={{ background: 'linear-gradient(180deg, #9ac6dc 0%, #b2d6e8 25%, #c8e4f0 55%, #daeef8 100%)' }}
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

      {/* Left Section - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative px-12 py-10 flex-col z-10">
        {/* Logo - Alinhado à esquerda */}
        <div className="mb-auto">
          <Image
            src="/logos/wedo-logo-transparent.png"
            alt="WeDo Talent"
            width={160}
            height={50}
            style={{ width: 'auto', height: 'auto' }}
            priority
          />
        </div>

        {/* Main Content - Largura total com margem esquerda */}
        <div className="flex-1 flex flex-col justify-center pr-8">
          <h1 className="text-4xl text-gray-950 dark:text-gray-50 font-light mb-4 leading-tight font-['Open_Sans',sans-serif]">
            O futuro do recrutamento é
            <span className="block font-semibold mt-1 text-gray-600 dark:text-gray-400">
              inteligente.
            </span>
          </h1>
          
          <p className="text-gray-600 text-base leading-relaxed mb-8 max-w-md">
            LIA revoluciona a forma como você recruta, usando IA avançada para encontrar,
            avaliar e engajar os melhores talentos.
          </p>

          <div className="space-y-3 mb-10">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500" />
              <span className="text-gray-800 dark:text-gray-200 text-base">Triagem automática com IA</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500" />
              <span className="text-gray-800 dark:text-gray-200 text-base">Assistente de IA de recrutamento</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500" />
              <span className="text-gray-800 dark:text-gray-200 text-base">Experiência personalizada do candidato</span>
            </div>
          </div>

          {/* LIA Card - Largura total */}
          <div className="bg-white/75 backdrop-blur-sm rounded-md p-5 w-full mt-4">
            <div className="flex items-center gap-4 mb-3">
              <Brain className="w-12 h-12 text-wedo-cyan" />
              <div>
                <h3 className="text-base font-semibold text-gray-950 dark:text-gray-50">Conheça a LIA</h3>
                <p className="text-gray-600 text-sm">Sua assistente de IA de recrutamento</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed">
              A LIA não é apenas um chatbot. É uma IA especializada que entende recrutamento,
              aprende com seus processos e otimiza continuamente seus resultados.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-gray-700 text-xs space-y-1 mt-auto">
          <p>
            A WeDo Talent é uma HRTech Brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro. Parte do TalensesGroup.
          </p>
          <p className="text-gray-600">
            © 2025 WeDo Talent. Todos os direitos reservados.
          </p>
        </div>
      </div>

      {/* Right Section - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:px-16 bg-white relative z-10 shadow-[-4px_0_24px_rgba(0,0,0,0.08)]">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <Image
              src="/logos/wedo-logo.png"
              alt="WeDo Talent"
              width={120}
              height={40}
              style={{ width: 'auto', height: 'auto' }}
              priority
            />
          </div>

          {/* Header */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50 mb-1">
              Entrar na plataforma
            </h2>
            <p className="text-gray-500 text-sm">
              Acesse sua conta para continuar
            </p>
          </div>

          {/* SSO Buttons */}
          <div className="space-y-2.5 mb-5">
            <Button
              variant="outline"
              className="w-full h-10 justify-start gap-3 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 text-sm font-normal"
              onClick={() => {
                const ssoEmail = email || undefined
                window.location.href = `/api/auth/workos/sso?${ssoEmail ? `email=${encodeURIComponent(ssoEmail)}&` : ''}connection=conn_microsoft_entra`
              }}
              disabled={isSubmitting}
            >
              <div className="w-4 h-4 bg-[#0078D4] rounded-sm flex items-center justify-center">
                <span className="text-white text-[10px] font-bold">M</span>
              </div>
              Continuar com Microsoft
            </Button>

            <Button
              variant="outline"
              className="w-full h-10 justify-start gap-3 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 text-sm font-normal"
              onClick={() => {
                const ssoEmail = email || undefined
                window.location.href = `/api/auth/workos/sso?${ssoEmail ? `email=${encodeURIComponent(ssoEmail)}&` : ''}connection=conn_google`
              }}
              disabled={isSubmitting}
            >
              <svg viewBox="0 0 24 24" className="w-4 h-4">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continuar com Google
            </Button>
          </div>

          {/* Divider */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-white text-gray-400">ou</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-md flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-red-600">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-md bg-white text-gray-950 dark:text-gray-50 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 transition-colors"
                  placeholder="seu@email.com"
                  required
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-800 dark:text-gray-200 mb-1.5">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 rounded-md bg-white text-gray-950 dark:text-gray-50 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 transition-colors"
                  placeholder="••••••••"
                  required
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded border-gray-300 text-gray-600 dark:text-gray-400 focus:ring-gray-900/20 dark:focus:ring-gray-50/20" />
                <span className="text-gray-600">Lembrar de mim</span>
              </label>
              <Link
                href="/forgot-password"
                className="text-gray-600 dark:text-gray-400 hover:text-[#4da8ba] font-medium"
              >
                Esqueceu a senha?
              </Link>
            </div>

            <Button
              type="submit"
              className="w-full h-10 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-sm font-medium"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Entrando...
                </span>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-5 p-3 bg-gray-50 border border-gray-100 rounded-md">
            <div className="flex items-center gap-2 mb-1.5">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Demo</span>
            </div>
            <div className="text-xs text-gray-500 space-y-0.5">
              <div>demo@wedotalent.com</div>
              <div>demo123</div>
            </div>
          </div>

          {/* Footer Links */}
          <div className="mt-6 flex justify-center gap-4 text-xs text-gray-400">
            <button className="hover:text-gray-600">Privacidade</button>
            <span>•</span>
            <button className="hover:text-gray-600">Termos</button>
            <span>•</span>
            <button className="hover:text-gray-600">Suporte</button>
          </div>
        </div>
      </div>
    </div>
  )
}
