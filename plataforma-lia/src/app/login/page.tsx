"use client"

import { useState, FormEvent } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Pencil
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
      <div className="hidden lg:flex lg:w-1/2 relative px-12 py-10 flex-col z-10">
        <div style={{ width: "230px", marginLeft: "-10px" }}>
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

        <div className="flex-1 flex flex-col justify-center pr-8">
          <h1 className="text-4xl text-gray-950 font-light mb-4 leading-tight font-['Open_Sans',sans-serif]">
            O futuro do recrutamento é inteligente e{" "}
            <span className="font-light text-wedo-cyan">simples.</span>
          </h1>
        </div>

        <div className="text-gray-700 text-xs space-y-1">
          <p>
            A WeDoTalent é uma HRTech brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro. Parte do TalensesGroup.
          </p>
          <p className="text-gray-600">© 2025 WeDoTalent. Todos os direitos reservados.</p>
        </div>
      </div>

      {/* Right Section - Card flutuante */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 relative z-10">
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
            <h2 className="text-xl font-semibold text-gray-950 mb-1">
              Entrar na plataforma
            </h2>
            <p className="text-gray-500 text-sm">Acesse sua conta para continuar</p>
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
                <div className="w-4 h-4 bg-[#0078D4] rounded-sm flex items-center justify-center shrink-0">
                  <span className="text-white text-[10px] font-bold">M</span>
                </div>
                Continuar com Microsoft
              </Button>
            </form>
          )}

        </div>
      </div>
    </div>
  )
}
