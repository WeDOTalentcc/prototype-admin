"use client"

import { useState, useEffect, Suspense } from"react"
import { useSearchParams, useRouter } from"next/navigation"
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import Image from"next/image"
import Link from"next/link"
import { toast } from"sonner"
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  UserPlus,
  Building2,
  Calendar,
  Briefcase
} from"lucide-react"

interface InvitationInfo {
  name: string
  email: string
  company_name: string
  role: string
  expires_at: string
  valid: boolean
}

type PageState ="loading" |"valid" |"expired" |"accepted" |"error"

function AceitarConviteContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get("token")

  const [pageState, setPageState] = useState<PageState>("loading")
  const [invitationInfo, setInvitationInfo] = useState<InvitationInfo | null>(null)
  const [error, setError] = useState("")
  const [isAccepting, setIsAccepting] = useState(false)

  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setError("Token de convite não fornecido")
        setPageState("error")
        return
      }

      try {
        const response = await fetch(`/api/backend-proxy/invitations/validate?token=${encodeURIComponent(token)}`)
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          if (response.status === 410 || errorData.details?.code ==="EXPIRED") {
            setPageState("expired")
          } else {
            setError(errorData.details?.detail || errorData.error ||"Convite inválido")
            setPageState("error")
          }
          return
        }

        const data = await response.json()
        setInvitationInfo(data)
        setPageState("valid")
      } catch (err: unknown) {
        setError("Erro ao conectar com o servidor")
        setPageState("error")
      }
    }

    validateToken()
  }, [token])

  const handleAcceptInvitation = async () => {
    if (!token) return

    setIsAccepting(true)
    setError("")

    try {
      const response = await fetch("/api/backend-proxy/invitations/accept", {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify({ token }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.details?.detail || errorData.error ||"Erro ao aceitar convite")
      }

      setPageState("accepted")
      toast.success("Convite aceito com sucesso!")
      
      setTimeout(() => {
        router.push("/login")
      }, 2000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) ||"Erro ao aceitar convite. Tente novamente.")
    } finally {
      setIsAccepting(false)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString("pt-BR", {
        day:"2-digit",
        month:"2-digit",
        year:"numeric"
      })
    } catch {
      return dateString
    }
  }

  const getRoleName = (role: string) => {
    const roleNames: Record<string, string> = {
      admin:"Administrador",
      recruiter:"Recrutador",
      manager:"Gestor",
      viewer:"Visualizador"
    }
    return roleNames[role?.toLowerCase()] || role ||"Membro"
  }

  if (pageState ==="loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
        <Card className="w-full max-w-md mx-4 border-0">
          <CardContent className="p-8 text-center">
            <Loader2 className="w-10 h-10 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary mx-auto mb-4" />
            <p className="text-lia-text-secondary text-sm">Validando seu convite...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (pageState ==="expired") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-4">
        <Card className="w-full max-w-md border-0">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WEDOTALENT"
                  width={120}
                  height={40}
                  className="w-auto h-auto"
                  priority
                />
              </div>
              
              <div className="w-16 h-16 bg-status-warning/15 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-status-warning" />
              </div>
              
              <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
                Convite Expirado
              </h2>
              <p className="text-lia-text-secondary text-sm mb-6">
                Este convite expirou. Por favor, solicite um novo convite ao administrador da empresa.
              </p>
              
              <Link href="/login">
                <Button className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active">
                  Ir para o Login
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (pageState ==="error") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-4">
        <Card className="w-full max-w-md border-0">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WEDOTALENT"
                  width={120}
                  height={40}
                  className="w-auto h-auto"
                  priority
                />
              </div>
              
              <div className="w-16 h-16 bg-status-error/15 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-status-error" />
              </div>
              
              <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
                Convite Inválido
              </h2>
              <p className="text-lia-text-secondary text-sm mb-6">
                {error ||"O link de convite é inválido. Por favor, verifique o link ou solicite um novo convite."}
              </p>
              
              <Link href="/login">
                <Button className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active">
                  Ir para o Login
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (pageState ==="accepted") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-4">
        <Card className="w-full max-w-md border-0">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <Image
                  src="/logos/wedo-logo.png"
                  alt="WEDOTALENT"
                  width={120}
                  height={40}
                  className="w-auto h-auto"
                  priority
                />
              </div>
              
              <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>
              
              <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
                Convite Aceito!
              </h2>
              <p className="text-lia-text-secondary text-sm mb-4">
                Você agora faz parte de <span className="font-medium">{invitationInfo?.company_name}</span>.
              </p>
              <p className="text-lia-text-secondary text-xs">
                Redirecionando para o login...
              </p>
              
              <div className="mt-6" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary mx-auto" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-4">
      <Card className="w-full max-w-md border-0">
        <CardContent className="p-8">
          <div className="text-center mb-6">
            <div className="flex justify-center mb-6">
              <Image
                src="/logos/wedo-logo.png"
                alt="WeDo Talent"
                width={120}
                height={40}
                className="w-auto h-auto"
                priority
              />
            </div>
            
            <div className="w-16 h-16 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
              <UserPlus className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            
            <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
              Você foi convidado!
            </h2>
            <p className="text-lia-text-secondary text-sm">
              Você foi convidado para participar da plataforma
            </p>
          </div>

          {invitationInfo && (
            <div className="space-y-4 mb-6">
              <div className="p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <div>
                    <p className="font-semibold text-lia-text-primary dark:text-lia-text-primary">{invitationInfo.company_name}</p>
                    <p className="text-xs text-lia-text-secondary">Empresa</p>
                  </div>
                </div>

                <div className="space-y-2 pt-3 border-t border-lia-border-subtle">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
                      <Briefcase className="w-4 h-4" />
                      <span>Sua função:</span>
                    </div>
                    <Chip variant="info">{getRoleName(invitationInfo.role)}</Chip>
                  </div>

                  {invitationInfo.expires_at && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
                        <Calendar className="w-4 h-4" />
                        <span>Válido até:</span>
                      </div>
                      <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">{formatDate(invitationInfo.expires_at)}</span>
                    </div>
                  )}
                </div>
              </div>

              {invitationInfo.name && (
                <div className="text-center">
                  <p className="text-sm text-lia-text-secondary">
                    Bem-vindo(a), <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{invitationInfo.name}</span>!
                  </p>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-status-error/10 border border-status-error/30 rounded-xl flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-status-error mt-0.5 flex-shrink-0" />
              <p className="text-xs text-status-error">{error}</p>
            </div>
          )}

          <Button
            onClick={handleAcceptInvitation}
            disabled={isAccepting}
            className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active h-11"
          >
            {isAccepting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                Aceitando...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Aceitar Convite
              </span>
            )}
          </Button>

          <p className="text-center text-xs text-lia-text-tertiary mt-4">
            Ao aceitar, você concorda com os{""}
            <Link href="/privacidade" className="text-lia-text-secondary dark:text-lia-text-tertiary hover:underline">
              Termos de Uso
            </Link>{""}
            da plataforma.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function AceitarConvitePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
          <Card className="w-full max-w-md mx-4 border-0">
            <CardContent className="p-8 text-center">
              <Loader2 className="w-10 h-10 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary mx-auto mb-4" />
              <p className="text-lia-text-secondary text-sm">Carregando...</p>
            </CardContent>
          </Card>
        </div>
      }
    >
      <AceitarConviteContent />
    </Suspense>
  )
}
