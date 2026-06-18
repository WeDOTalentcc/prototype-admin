"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useCallback } from "react"
import { useAuth } from "@/contexts/auth-context"
import { useAuthenticatedUserId } from "@/hooks/shared/use-authenticated-user-id"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  User,
  KeyRound,
  LogOut,
  Bell,
  Eye,
  EyeOff,
  Check,
  X,
  Loader2,
} from "lucide-react"
import { NotificationSystem } from "@/components/notification-system"
import { HitlPendingBadge } from "@/components/hitl-pending-badge"
import { ProfileModal } from "@/components/modals/profile-modal"
import type { Notification as AppNotification } from "@/hooks/shared/use-notifications"

interface TopBarProps {
  onNavigate?: (page: string) => void
  currentPage?: string
}

export function TopBar({ onNavigate, currentPage }: TopBarProps = {}) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('topbar-password', showPasswordModal)

  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  const { user: authUser, refreshUser } = useAuth()
  const { userId: authenticatedUserId, isReady: isAuthReady } = useAuthenticatedUserId()

  const handleNotificationClick = useCallback((_notification: AppNotification) => {
    // digest notifications are now handled by WeeklyDigestChatProvider
  }, [])

  const roleLabels: Record<string, string> = {
    admin: "Administrador(a)",
    recruiter: "Recrutador(a)",
    viewer: "Visualizador(a)",
  }

  const isSSOUser = !!(authUser && 'sso_provider' in authUser && authUser.sso_provider)

  const currentUser = {
    name: authUser?.name || "Usuário",
    email: authUser?.email || "usuario@empresa.com",
    role: authUser?.role ? (roleLabels[authUser.role] ?? authUser.role) : "Recrutador(a)",
    company: authUser?.company || "",
    avatar_url: (authUser && 'avatar_url' in authUser ? authUser.avatar_url : undefined) as string | undefined,
    sso_provider: (authUser && 'sso_provider' in authUser ? authUser.sso_provider : null) as string | null,
  }

  const handleOpenPasswordModal = () => {
    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")
    setPasswordError("")
    setPasswordSuccess(false)
    setIsChangingPassword(false)
    setShowPasswordModal(true)
  }

  const handleClosePasswordModal = () => {
    setShowPasswordModal(false)
    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")
    setPasswordError("")
    setPasswordSuccess(false)
    setIsChangingPassword(false)
  }

  const handlePasswordChange = async () => {
    setPasswordError("")

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("Todos os campos são obrigatórios")
      return
    }

    if (newPassword.length < 8) {
      setPasswordError("A nova senha deve ter no mínimo 8 caracteres")
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("As senhas não coincidem")
      return
    }

    setIsChangingPassword(true)

    try {
      const res = await fetch("/api/backend-proxy/auth/change-password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || "Erro ao alterar senha")
      }

      setPasswordSuccess(true)
      setTimeout(() => {
        handleClosePasswordModal()
      }, 2000)
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Erro ao alterar senha")
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleNavigateToNotifications = () => {
    onNavigate?.("Configurações")
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "alertas" }))
    }, 300)
  }

  return (
    <div className="px-2 py-3">
      <div className="flex items-center justify-between">
        <div className="flex-1" />

        <div className="flex items-center space-x-1.5">
          <HitlPendingBadge />
          {/* BUG-08: gating de auth — evita request com default_user pré-hidratação */}
          {isAuthReady && authenticatedUserId && (
            <NotificationSystem userId={authenticatedUserId} onNotificationClick={handleNotificationClick} />
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-7 w-7 p-0 rounded-full hover:bg-lia-interactive-hover"
                title={currentUser.name}
              >
                <Avatar className="h-7 w-7">
                  <AvatarImage src={currentUser.avatar_url} alt={currentUser.name} />
                  <AvatarFallback className="text-xs bg-lia-bg-inverse text-lia-text-on-inverse">
                    {currentUser.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              side="bottom"
              sideOffset={8}
              className="w-64"
            >
              <div className="p-3 pb-4">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={currentUser.avatar_url} alt={currentUser.name} />
                    <AvatarFallback className="text-sm bg-lia-bg-inverse text-lia-text-on-inverse">
                      {currentUser.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-lia-text-primary truncate">
                      {currentUser.name}
                    </div>
                    <div className="text-xs text-lia-text-tertiary truncate">
                      {currentUser.email}
                    </div>
                    <div className="text-xs text-lia-text-tertiary mt-0.5">
                      {currentUser.role}
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-1">
                <DropdownMenuItem
                  className="cursor-pointer text-xs"
                  onClick={() => setShowProfileModal(true)}
                >
                  <User className="w-3.5 h-3.5 mr-2" />
                  Meu Perfil
                </DropdownMenuItem>
                {!isSSOUser && (
                  <DropdownMenuItem
                    className="cursor-pointer text-xs"
                    onClick={handleOpenPasswordModal}
                  >
                    <KeyRound className="w-3.5 h-3.5 mr-2" />
                    Alterar Senha
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  className="cursor-pointer text-xs"
                  onClick={handleNavigateToNotifications}
                >
                  <Bell className="w-3.5 h-3.5 mr-2" />
                  Preferências de Notificação
                </DropdownMenuItem>
              </div>

              <DropdownMenuSeparator />

              <div className="p-1">
                <DropdownMenuItem
                  className="cursor-pointer text-xs text-status-error dark:text-status-error"
                  onClick={() => onNavigate?.("Sair")}
                >
                  <LogOut className="w-3.5 h-3.5 mr-2" />
                  Sair
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <ProfileModal
        open={showProfileModal}
        onOpenChange={setShowProfileModal}
        user={currentUser}
        onNavigateToSettings={handleNavigateToNotifications}
        onProfileUpdated={() => {
          refreshUser()
        }}
      />

      <Dialog open={showPasswordModal} onOpenChange={(open) => { if (!open) handleClosePasswordModal(); else setShowPasswordModal(true); }}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-lia-text-secondary" />
              Alterar Senha
            </DialogTitle>
            <DialogDescription>
              Digite sua senha atual e a nova senha para alterá-la.
            </DialogDescription>
          </DialogHeader>

          {passwordSuccess ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mb-4">
                <Check className="w-8 h-8 text-status-success" />
              </div>
              <p className="text-lg font-medium text-status-success">Senha alterada com sucesso!</p>
            </div>
          ) : (
            <>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Senha Atual</Label>
                  <div className="relative">
                    <Input
                      id="current-password"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Digite sua senha atual"
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    >
                      {showCurrentPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password">Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="new-password"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Digite a nova senha (mín. 8 caracteres)"
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirmar Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirme a nova senha"
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                {passwordError && (
                  <div className="flex items-center gap-2 text-status-error text-sm">
                    <X className="w-4 h-4" />
                    {passwordError}
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={handleClosePasswordModal}>
                  Cancelar
                </Button>
                <Button
                  onClick={handlePasswordChange}
                  disabled={isChangingPassword}
                  className="text-lia-btn-primary-text hover:opacity-90 bg-lia-btn-primary-bg"
                >
                  {isChangingPassword && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Alterar Senha
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
