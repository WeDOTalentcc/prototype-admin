"use client"

import { useState, FormEvent } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Pencil, Globe, Linkedin
} from "lucide-react"
import CloudsBackground from "@/components/clouds-background"

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading } = useJWTAuth()

  const [step, setStep] = useState<"email" | "password">("email")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleEmailStep = (e: FormEvent) => {
    e.preventDefault()
    setError("")
    if (!email || !email.includes("@") || !email.includes(".")) {
      setError("Insira um email válido.")
      return
    }
    setStep("password")
  }

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setIsSubmitting(true)
    try {
      await login(email, password)
      router.push("/login/welcome")
    } catch (err: any) {
      setError(err.message || "Senha incorreta. Verifique suas credenciais.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleBack = () => {
    setStep("email")
    setPassword("")
    setError("")
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex font-['Open_Sans',sans-serif] relative overflow-hidden">
      <CloudsBackground />

      {/* Left Section - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col z-10">
        {/* Logo — absoluto no topo, fora do fluxo */}
        <div className="absolute top-10 left-[38px]" style={{ width: "230px" }}>
          <Image
            src="/logos/wedo-logo-transparent.png"
            alt="WeDo Talent"
            width={230}
            height={73}
            style={{ width: "230px", height: "auto", maxWidth: "230px" }}
            priority
          />
          <span
            className="block text-right text-gray-950 font-semibold uppercase tracking-[0.18em] text-[18px]"
            style={{ marginTop: "-5px", paddingRight: "6px" }}
          >
            talent
          </span>
        </div>

        {/* Conteúdo centralizado na altura total do painel */}
        <div className="flex-1 flex flex-col justify-center px-14 pr-10">
          <div className="mb-7">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/10 text-gray-700 text-sm font-medium">
              <span className="text-wedo-cyan text-base leading-none">»</span>
              IA Agêntica para Recrutamento
            </span>
          </div>
          {/* Headline — primeiro, maior impacto */}
          <h1 className="text-5xl text-gray-950 font-light leading-tight mb-7 font-['Open_Sans',sans-serif]">
            Entre. A <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> já está<br />
            trabalhando por você.
          </h1>
          {/* Sequência de suporte — abaixo, mais leve */}
          <p className="text-base text-gray-500 font-normal leading-relaxed font-['Open_Sans',sans-serif]">
            Sourcing global&nbsp;·&nbsp;Triagem inteligente&nbsp;·&nbsp;Agendamentos automáticos<br />
            Recrutamento <span className="text-wedo-cyan font-bold">simples</span>
          </p>
        </div>

        {/* Footer esquerdo — ícones + copyright */}
        <div className="absolute bottom-0 left-0 pb-8 px-12">
          <div className="flex items-center gap-4 mb-1.5">
            <a
              href="https://www.wedotalent.cc"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Website"
            >
              <Globe className="w-4 h-4" />
            </a>
            <a
              href="https://www.linkedin.com/company/wedotalent/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="LinkedIn"
            >
              <Linkedin className="w-4 h-4" />
            </a>
            <a
              href="mailto:tech@wedotalent.cc"
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Contato"
            >
              <Mail className="w-4 h-4" />
            </a>
          </div>
          <p className="text-xs text-gray-400">© 2025 <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> by WeDoTalent</p>
        </div>

      </div>

      {/* Right Section - Card flutuante */}
      <div className="w-full lg:w-1/2 flex flex-col relative z-10">
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 lg:p-10">

          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center mb-8">
            <Image
              src="/logos/wedo-logo-transparent.png"
              alt="WeDo Talent"
              width={120}
              height={40}
              style={{ width: "auto", height: "auto" }}
              priority
            />
          </div>

          {/* Header */}
          <div className="mb-6 text-center">
            <h2 className="text-xl font-semibold text-gray-950">
              Entrar na plataforma
            </h2>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-md flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-red-600">{error}</p>
            </div>
          )}

          {/* ── ETAPA 1: EMAIL ── */}
          {step === "email" && (
            <form onSubmit={handleEmailStep} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-800 mb-1.5">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-md bg-white text-gray-950 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 transition-colors"
                    placeholder="seu@email.com"
                    required
                    autoFocus
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-10 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium"
              >
                Entrar
              </Button>
            </form>
          )}

          {/* ── ETAPA 2: SENHA ── */}
          {step === "password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              {/* Email confirmado */}
              <div className="flex items-center justify-between px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-md">
                <div className="flex items-center gap-2 min-w-0">
                  <Mail className="w-4 h-4 text-gray-400 shrink-0" />
                  <span className="text-sm text-gray-700 truncate">{email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 transition-colors ml-2 shrink-0"
                >
                  <Pencil className="w-3 h-3" />
                  Alterar
                </button>
              </div>

              {/* Senha */}
              <div>
                <label className="block text-xs font-medium text-gray-800 mb-1.5">
                  Senha
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 rounded-md bg-white text-gray-950 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 transition-colors"
                    placeholder="••••••••"
                    required
                    autoFocus
                    disabled={isSubmitting}
                    autoComplete="current-password"
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

              {/* Lembrar / Esqueceu */}
              <div className="flex items-center justify-between text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-gray-300 focus:ring-gray-900/20"
                  />
                  <span className="text-gray-600">Lembrar de mim</span>
                </label>
                <Link
                  href="/forgot-password"
                  className="text-gray-600 hover:text-wedo-cyan font-medium transition-colors"
                >
                  Esqueceu a senha?
                </Link>
              </div>

              {/* Confirmar */}
              <Button
                type="submit"
                className="w-full h-10 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Entrando...
                  </span>
                ) : (
                  "Confirmar"
                )}
              </Button>

              {/* Separador + Microsoft */}
              <div className="relative pt-1">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-3 bg-white text-gray-400">ou</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full h-10 justify-start gap-3 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 text-sm font-normal"
                onClick={() => {
                  window.location.href = `/api/auth/workos/sso?${email ? `email=${encodeURIComponent(email)}&` : ""}connection=conn_microsoft_entra`
                }}
                disabled={isSubmitting}
              >
                <svg width="16" height="16" viewBox="0 0 21 21" className="shrink-0" aria-hidden="true">
                  <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                  <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                  <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                  <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                </svg>
                Continuar com Microsoft
              </Button>
            </form>
          )}

        </div>
        </div>

        {/* Footer rodapé — absoluto para não deslocar o card */}
        <div className="absolute bottom-0 left-0 right-0 pb-8 px-12 text-gray-500 text-xs space-y-1 text-center">
          <p>
            A WeDoTalent é uma HRTech brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro.
          </p>
          <p>© 2025 WeDoTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
