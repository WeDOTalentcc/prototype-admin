"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { WeDOLogo } from "@/components/wedo-logo"
import {
  Eye, EyeOff, Mail, Lock, User, Building, Zap,
  Instagram, Twitter, Globe, MessageCircle, Linkedin,
  ArrowRight, Brain, Bot, Users
} from "lucide-react"

interface LoginPageProps {
  onLogin: (user: { name: string; email: string; role: string; company: string }) => void
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
    company: "",
    role: "recruiter"
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Simulate API call
    setTimeout(() => {
      const user = {
        name: isLogin ? "Ana Silva" : formData.name,
        email: formData.email,
        role: formData.role,
        company: isLogin ? "Sodexo" : formData.company
      }

      onLogin(user)
      setIsLoading(false)
    }, 1500)
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Left Section - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-white border-r border-gray-200">
        <div className="relative z-10 flex flex-col justify-center px-8 lg:px-12 max-w-lg">
          {/* Logo */}
          <div className="mb-8 animate-fade-in">
            <WeDOLogo className="text-2xl text-gray-950 dark:text-gray-50" />
          </div>

          {/* Main Headline */}
          <div className="mb-8 animate-slide-in">
            <h1 className="text-4xl font-light mb-4 leading-tight text-gray-950 dark:text-gray-50">
              O futuro do recrutamento é
              <span className="block font-semibold mt-2 text-gray-700">
                inteligente.
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-6 leading-relaxed">
              LIA revoluciona a forma como você recruta, usando IA avançada para encontrar,
              avaliar e engajar os melhores talentos.
            </p>

            <div className="space-y-4 mb-8">
              <div className="flex items-center gap-3 animate-fade-in">
                <div
                  className="w-2 h-2 rounded-full bg-gray-900"
                ></div>
                <span className="text-gray-800 dark:text-gray-200">Triagem automática com IA</span>
              </div>
              <div className="flex items-center gap-3 animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div
                  className="w-2 h-2 rounded-full bg-gray-900"
                ></div>
                <span className="text-gray-800 dark:text-gray-200">Assistente de IA de recrutamento</span>
              </div>
              <div className="flex items-center gap-3 animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div
                  className="w-2 h-2 rounded-full bg-gray-900"
                ></div>
                <span className="text-gray-800 dark:text-gray-200">Experiência personalizada do candidato</span>
              </div>
            </div>
          </div>

          {/* LIA Highlight */}
          <div className="bg-gray-100 rounded-2xl p-6 mb-8 animate-scale-in">
            <div className="flex items-center gap-4 mb-4">
              <div
                className="w-12 h-12 rounded-md flex items-center justify-center bg-gray-900"
              >
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50">Conheça a LIA</h3>
                <p className="text-gray-600 text-sm">Sua assistente de IA de recrutamento</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed">
              A LIA não é apenas um chatbot. É uma IA especializada que entende recrutamento,
              aprende com seus processos e otimiza continuamente seus resultados.
            </p>
          </div>

          {/* Social Media */}
          <div className="animate-slide-in">
            <p className="text-gray-500 text-sm mb-4">Siga-nos nas redes sociais</p>
            <div className="flex gap-4">
              <Button
                variant="ghost"
                size="sm"
                className="w-10 h-10 p-0 bg-gray-100 hover:bg-gray-200 rounded-md transition-all duration-200"
              >
                <Globe className="w-4 h-4 text-gray-600" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-10 h-10 p-0 bg-gray-100 hover:bg-gray-200 rounded-md transition-all duration-200"
              >
                <Linkedin className="w-4 h-4 text-gray-600" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-10 h-10 p-0 bg-gray-100 hover:bg-gray-200 rounded-md transition-all duration-200"
              >
                <Instagram className="w-4 h-4 text-gray-600" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-10 h-10 p-0 bg-gray-100 hover:bg-gray-200 rounded-md transition-all duration-200"
              >
                <Twitter className="w-4 h-4 text-gray-600" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-10 h-10 p-0 bg-gray-100 hover:bg-gray-200 rounded-md transition-all duration-200"
              >
                <MessageCircle className="w-4 h-4 text-gray-600" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Section - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md animate-fade-in">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="text-left mx-auto w-fit">
              <div className="text-2xl font-light text-gray-950 dark:text-gray-50 tracking-wide">
                we<span className="font-semibold">DO</span>
              </div>
              <div className="text-xs font-medium text-gray-800 dark:text-gray-200 tracking-widest uppercase mt-0.5">
                TALENT
              </div>
            </div>
            <div className="flex items-center gap-2 justify-center mt-4">
              <Zap className="w-4 h-4" style={{ color: '#0094c6' }} />
              <span className="text-sm text-gray-800 dark:text-gray-200">Powered by LIA</span>
            </div>
          </div>

          {/* Login Form */}
          <div className="w-full">
            <div className="mb-8 animate-slide-in">
              <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50 mb-2">
                {isLogin ? "Bem-vindo de volta" : "Criar sua conta"}
              </h1>
              <p className="text-gray-800 dark:text-gray-200">
                {isLogin ? "Entre em sua conta para acessar a plataforma" : "Junte-se à revolução do recrutamento inteligente"}
              </p>
            </div>

            {/* Social Login Options - Alinhados à esquerda */}
            <div className="space-y-3 mb-6 animate-scale-in">
              <Button
                variant="outline"
                className="justify-start h-12 gap-3 bg-white hover:bg-gray-50 w-full text-left hover-lift micro-bounce"
                onClick={() => console.log("Microsoft login")}
              >
                <div className="w-5 h-5 bg-gray-700 dark:bg-gray-300 rounded flex items-center justify-center">
                  <span className="text-white text-xs font-bold">M</span>
                </div>
                Continuar com Microsoft
              </Button>

              <Button
                variant="outline"
                className="justify-start h-12 gap-3 bg-white hover:bg-gray-50 w-full text-left hover-lift micro-bounce"
                onClick={() => console.log("Google login")}
              >
                <div className="w-5 h-5">
                  <svg viewBox="0 0 24 24" className="w-5 h-5">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </div>
                Continuar com Google Workspace
              </Button>
            </div>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full bg-gray-200 dark:bg-gray-600 h-px"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-900 text-gray-600">ou continue com email</span>
              </div>
            </div>

            <Card className="bg-white dark:bg-gray-800 wedo-card animate-fade-in">
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Name field (only for register) */}
                  {!isLogin && (
                    <div className="space-y-2 animate-slide-in">
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        Nome Completo
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 w-4 h-4" />
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => handleInputChange("name", e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 transition-all duration-200"
                          style={{
                            '--tw-ring-color': '#0094c6',
                            '--tw-ring-opacity': '0.5'
                          } as React.CSSProperties}
                          placeholder="Seu nome completo"
                          required={!isLogin}
                        />
                      </div>
                    </div>
                  )}

                  {/* Email field */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                      Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 w-4 h-4" />
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange("email", e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 transition-all duration-200"
                        style={{
                          '--tw-ring-color': '#0094c6',
                          '--tw-ring-opacity': '0.5'
                        } as React.CSSProperties}
                        placeholder="seu@email.com"
                        required
                      />
                    </div>
                  </div>

                  {/* Company field (only for register) */}
                  {!isLogin && (
                    <div className="space-y-2 animate-slide-in">
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        Empresa
                      </label>
                      <div className="relative">
                        <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 w-4 h-4" />
                        <input
                          type="text"
                          value={formData.company}
                          onChange={(e) => handleInputChange("company", e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 transition-all duration-200"
                          style={{
                            '--tw-ring-color': '#0094c6',
                            '--tw-ring-opacity': '0.5'
                          } as React.CSSProperties}
                          placeholder="Nome da empresa"
                          required={!isLogin}
                        />
                      </div>
                    </div>
                  )}

                  {/* Role field (only for register) */}
                  {!isLogin && (
                    <div className="space-y-2 animate-slide-in">
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        Cargo
                      </label>
                      <select
                        value={formData.role}
                        onChange={(e) => handleInputChange("role", e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 transition-all duration-200"
                        style={{
                          '--tw-ring-color': '#0094c6',
                          '--tw-ring-opacity': '0.5'
                        } as React.CSSProperties}
                      >
                        <option value="recruiter">Recrutador</option>
                        <option value="hr_manager">Gerente de RH</option>
                        <option value="hiring_manager">Gestor Contratante</option>
                        <option value="admin">Administrador</option>
                      </select>
                    </div>
                  )}

                  {/* Password field */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                      Senha
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 w-4 h-4" />
                      <input
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={(e) => handleInputChange("password", e.target.value)}
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 transition-all duration-200"
                        style={{
                          '--tw-ring-color': '#0094c6',
                          '--tw-ring-opacity': '0.5'
                        } as React.CSSProperties}
                        placeholder="Sua senha"
                        required
                        minLength={6}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 micro-bounce"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>

                  {/* Submit button */}
                  <Button
                    type="submit"
                    className="w-full text-white py-3 mt-6 hover-lift micro-bounce font-medium"
                    style={{
                      backgroundColor: '#0094c6',
                      '--hover-bg': 'rgba(0, 148, 198, 0.9)'
                    } as React.CSSProperties}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-loading" />
                        {isLogin ? "Entrando..." : "Criando conta..."}
                      </div>
                    ) : (
                      isLogin ? "Entrar" : "Criar Conta"
                    )}
                  </Button>
                </form>

                {/* Additional Options */}
                <div className="flex items-center justify-between text-sm mt-4">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded" />
                    <span className="text-gray-800 dark:text-gray-200">Lembrar de mim</span>
                  </label>
                  {isLogin && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-0 h-auto micro-scale"
                      style={{ color: '#0094c6' }}
                    >
                      Esqueceu a senha?
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Toggle between login/register */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-800 dark:text-gray-200">
                {isLogin ? "Não tem uma conta?" : "Já tem uma conta?"}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsLogin(!isLogin)}
                  className="ml-1 p-0 h-auto font-medium micro-scale"
                  style={{ color: '#0094c6' }}
                >
                  {isLogin ? "Cadastre-se" : "Faça login"}
                </Button>
              </p>
            </div>

            {/* Demo credentials */}
            {isLogin && (
              <div
                className="mt-4 p-4 rounded-md border animate-scale-in"
                style={{
                  backgroundColor: 'rgba(0, 148, 198, 0.1)',
                  borderColor: 'rgba(0, 148, 198, 0.2)'
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <p className="text-sm font-medium" style={{ color: '#0094c6' }}>
                    Credenciais de demonstração
                  </p>
                </div>
                <div className="text-sm space-y-1" style={{ color: 'rgba(0, 148, 198, 0.8)' }}>
                  <div>📧 Email: ana.silva@sodexo.com</div>
                  <div>🔑 Senha: demo123</div>
                </div>
              </div>
            )}

            {/* Footer Links */}
            <div className="mt-8 text-center space-y-3">
              <div className="flex justify-center gap-6 text-sm text-gray-600">
                <Button variant="ghost" size="sm" className="p-0 h-auto text-gray-600 hover:text-gray-800 micro-scale">
                  Política de Privacidade
                </Button>
                <Button variant="ghost" size="sm" className="p-0 h-auto text-gray-600 hover:text-gray-800 micro-scale">
                  Termos de Uso
                </Button>
                <Button variant="ghost" size="sm" className="p-0 h-auto text-gray-600 hover:text-gray-800 micro-scale">
                  Suporte
                </Button>
              </div>
              <p className="text-xs text-gray-600">
                © 2025 WeDo Talent. Powered by Artificial Intelligence.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
