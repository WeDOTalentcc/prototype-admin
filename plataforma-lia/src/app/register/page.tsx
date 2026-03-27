"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { Eye, EyeOff, Loader2, CheckCircle } from "lucide-react"
import Link from "next/link"

export default function RegisterPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (password !== confirmPassword) {
      setError("As senhas não coincidem")
      return
    }

    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres")
      return
    }

    if (!acceptTerms) {
      setError("Você deve aceitar os termos de uso")
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("/api/backend-proxy/auth/public-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || data.details?.detail || "Erro ao criar conta")
      }

      setSuccess(true)
    } catch (err: any) {
      setError(err.message || "Erro ao criar conta. Tente novamente.")
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 font-open-sans p-4">
        <div className="w-full max-w-md bg-white rounded-2xl p-10 text-center">
          <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-status-success" />
          </div>
          <h2 className="text-2xl font-bold text-gray-950 dark:text-gray-50 mb-3">Conta criada com sucesso!</h2>
          <p className="text-gray-600 mb-6">
            Enviamos um email de verificação para <strong>{email}</strong>. 
            Por favor, verifique sua caixa de entrada e clique no link para ativar sua conta.
          </p>
          <Link href="/login">
            <Button className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md">
              Ir para o Login
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex font-open-sans">
      <div className="hidden lg:flex lg:w-1/2 bg-gray-900 flex-col justify-center items-center p-12 relative">
        <div className="absolute top-8 left-8">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
              <WeDOLogo className="h-4 text-gray-950 dark:text-gray-50" />
            </div>
          </div>
        </div>
        
        <div className="max-w-md text-center">
          <h1 className="text-5xl font-bold text-white leading-tight mb-6">
            Junte-se à LIA
          </h1>
          <p className="text-xl text-gray-300 leading-relaxed mb-8">
            Transforme seu processo de recrutamento com inteligência artificial avançada.
          </p>
          <div className="space-y-4 text-left">
            <div className="flex items-center gap-3 text-gray-300">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>Automação inteligente de processos</span>
            </div>
            <div className="flex items-center gap-3 text-gray-300">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>IA que aprende com você</span>
            </div>
            <div className="flex items-center gap-3 text-gray-300">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>Dados organizados e acessíveis</span>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 bg-gray-50 flex flex-col">
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white rounded-2xl p-10">
            <div className="text-center mb-6">
              <div className="lg:hidden flex items-center justify-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-black rounded-md flex items-center justify-center">
                  <WeDOLogo className="h-4 text-white" />
                </div>
              </div>
              <h2 className="text-3xl font-bold text-gray-950 dark:text-gray-50 mb-3">Criar Conta</h2>
              <p className="text-gray-600 text-base leading-relaxed">
                Preencha seus dados para começar a usar a LIA.
              </p>
            </div>

            <form onSubmit={handleRegister} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Nome Completo
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Digite seu nome completo"
                  className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Digite seu email"
                  className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Senha
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mínimo 8 caracteres"
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

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Confirmar Senha
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Digite a senha novamente"
                    className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600 hover:text-gray-700"
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => setAcceptTerms(e.target.checked)}
                    className="w-4 h-4 mt-1 text-gray-950 dark:text-gray-50 border-gray-300 rounded focus:ring-gray-900"
                  />
                  <span className="text-sm text-gray-600">
                    Li e aceito os{" "}
                    <a href="#" className="text-gray-950 dark:text-gray-50 font-medium hover:underline">
                      Termos de Uso
                    </a>{" "}
                    e a{" "}
                    <a href="#" className="text-gray-950 dark:text-gray-50 font-medium hover:underline">
                      Política de Privacidade
                    </a>
                  </span>
                </label>
              </div>

              {error && (
                <div className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                  <p className="text-status-error text-sm font-medium">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md transition-all font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Criando conta...
                  </>
                ) : (
                  "Criar Conta"
                )}
              </Button>

              <p className="text-center text-gray-600 text-sm">
                Já tem uma conta?{" "}
                <Link href="/login" className="text-gray-950 dark:text-gray-50 font-medium hover:underline">
                  Faça login
                </Link>
              </p>
            </form>
          </div>
        </div>

        <div className="p-4 text-center text-xs text-gray-800 dark:text-gray-200 space-y-1">
          <p>© 2024 WeDOTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
