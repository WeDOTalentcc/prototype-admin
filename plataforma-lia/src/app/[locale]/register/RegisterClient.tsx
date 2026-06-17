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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) || "Erro ao criar conta. Tente novamente.")
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-secondary font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-status-success" />
          </div>
          <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Conta criada com sucesso!</h2>
          <p className="text-lia-text-secondary mb-6">
            Enviamos um email de verificação para <strong>{email}</strong>. 
            Por favor, verifique sua caixa de entrada e clique no link para ativar sua conta.
          </p>
          <Link href="/login">
            <Button className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md">
              Ir para o Login
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex font-open-sans">
      <div className="hidden lg:flex lg:w-1/2 bg-lia-btn-primary-bg flex-col justify-center items-center p-12 relative">
        <div className="absolute top-8 left-8">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-lia-bg-primary rounded-xl flex items-center justify-center">
              <WeDOLogo className="h-4 text-lia-text-primary dark:text-lia-text-primary" />
            </div>
          </div>
        </div>
        
        <div className="max-w-md text-center">
          <h1 className="text-5xl font-semibold text-white leading-tight mb-6">
            Junte-se à WeDoTalent
          </h1>
          <p className="text-xl text-lia-text-disabled leading-relaxed mb-8">
            Transforme seu processo de recrutamento com inteligência artificial avançada.
          </p>
          <div className="space-y-4 text-left">
            <div className="flex items-center gap-3 text-lia-text-disabled">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>Automação inteligente de processos</span>
            </div>
            <div className="flex items-center gap-3 text-lia-text-disabled">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>IA que aprende com você</span>
            </div>
            <div className="flex items-center gap-3 text-lia-text-disabled">
              <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
              <span>Dados organizados e acessíveis</span>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 bg-lia-bg-primary flex flex-col">
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10">
            <div className="text-center mb-6">
              <div className="lg:hidden flex items-center justify-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-black rounded-md flex items-center justify-center">
                  <WeDOLogo className="h-4 text-white" />
                </div>
              </div>
              <h2 className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Criar Conta</h2>
              <p className="text-lia-text-secondary text-base leading-relaxed">
                Preencha seus dados para começar a usar a plataforma.
              </p>
            </div>

            <form onSubmit={handleRegister} className="space-y-5" aria-label="Formulário de cadastro">
              <div>
                <label htmlFor="campo-nome" className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Nome Completo
                </label>
                <input
                  id="campo-nome"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Digite seu nome completo"
                  className="w-full px-4 py-3 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                  required
                  aria-required="true"
                  aria-describedby={error ? "register-error" : undefined}
                />
              </div>

              <div>
                <label htmlFor="campo-email" className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Email
                </label>
                <input
                  id="campo-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Digite seu email"
                  className="w-full px-4 py-3 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                  required
                  aria-required="true"
                  aria-describedby={error ? "register-error" : undefined}
                />
              </div>

              <div>
                <label htmlFor="campo-senha" className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Senha
                </label>
                <div className="relative">
                  <input
                    id="campo-senha"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mínimo 8 caracteres"
                    className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                    required
                    aria-required="true"
                    aria-describedby={error ? "register-error" : undefined}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary"
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="campo-confirmar-senha" className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Confirmar Senha
                </label>
                <div className="relative">
                  <input
                    id="campo-confirmar-senha"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Digite a senha novamente"
                    className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                    required
                    aria-required="true"
                    aria-describedby={error ? "register-error" : undefined}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary"
                    aria-label={showConfirmPassword ? "Ocultar confirmação de senha" : "Mostrar confirmação de senha"}
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="campo-termos" className="flex items-start gap-3 cursor-pointer">
                  <input
                    id="campo-termos"
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => setAcceptTerms(e.target.checked)}
                    className="w-4 h-4 mt-1 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default rounded-xl focus:ring-lia-btn-primary-bg"
                    aria-required="true"
                    aria-describedby={error ? "register-error" : undefined}
                  />
                  <span className="text-sm text-lia-text-secondary">
                    Li e aceito os{" "}
                    <a href="#" className="text-lia-text-primary dark:text-lia-text-primary font-medium hover:underline">
                      Termos de Uso
                    </a>{" "}
                    e a{" "}
                    <a href="#" className="text-lia-text-primary dark:text-lia-text-primary font-medium hover:underline">
                      Política de Privacidade
                    </a>
                  </span>
                </label>
              </div>

              {error && (
                <div id="register-error" role="alert" className="p-3 rounded-xl bg-status-error/10 border border-status-error/30">
                  <p className="text-status-error text-sm font-medium">
                    <span aria-hidden="true">⚠ </span>
                    {error}
                  </p>
                </div>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md transition-colors motion-reduce:transition-none font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" aria-hidden="true" />
                    Criando conta...
                  </>
                ) : (
                  "Criar Conta"
                )}
              </Button>

              <p className="text-center text-lia-text-secondary text-sm">
                Já tem uma conta?{" "}
                <Link href="/login" className="text-lia-text-primary dark:text-lia-text-primary font-medium hover:underline">
                  Faça login
                </Link>
              </p>
            </form>
          </div>
        </div>

        <div className="p-4 text-center text-xs text-lia-text-primary dark:text-lia-text-primary space-y-1">
          <p>© 2024 WeDOTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
