"use client"

import { useState, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  User,
  Mail,
  Shield,
  Camera,
  Loader2,
  Check,
  Bell,
  ExternalLink,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ProfileModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user: {
    name: string
    email: string
    role: string
    avatar_url?: string | null
    sso_provider?: string | null
  }
  onNavigateToSettings?: () => void
  onProfileUpdated?: (updated: { name: string; avatar_url?: string }) => void
}

const SSO_BADGES: Record<string, { label: string; color: string }> = {
  microsoft: { label: "Microsoft", color: "bg-[#00A4EF]/10 text-[#00A4EF] border-[#00A4EF]/20" },
  google: { label: "Google", color: "bg-[#4285F4]/10 text-[#4285F4] border-[#4285F4]/20" },
  azure_ad: { label: "Microsoft", color: "bg-[#00A4EF]/10 text-[#00A4EF] border-[#00A4EF]/20" },
}

export function ProfileModal({
  open,
  onOpenChange,
  user,
  onNavigateToSettings,
  onProfileUpdated,
}: ProfileModalProps) {
  const [editName, setEditName] = useState(user.name)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState("")

  const isSSOUser = !!user.sso_provider
  const initials = user.name.split(" ").map((n) => n[0]).join("").slice(0, 2)
  const ssoBadge = user.sso_provider ? SSO_BADGES[user.sso_provider] || { label: user.sso_provider, color: "bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle" } : null

  const handleSave = useCallback(async () => {
    if (!editName.trim() || editName.trim().length < 2) {
      setError("O nome deve ter pelo menos 2 caracteres")
      return
    }

    setIsSaving(true)
    setError("")

    try {
      const res = await fetch("/api/backend-proxy/auth/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editName.trim() }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || "Erro ao salvar perfil")
      }

      setSaveSuccess(true)
      setIsEditing(false)
      onProfileUpdated?.({ name: editName.trim() })

      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar perfil")
    } finally {
      setIsSaving(false)
    }
  }, [editName, onProfileUpdated])

  const handleCancel = () => {
    setEditName(user.name)
    setIsEditing(false)
    setError("")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lia-text-primary">
            <User className="w-5 h-5 text-lia-text-secondary" />
            Meu Perfil
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 pt-2">
          <div className="flex flex-col items-center gap-3">
            <div className="relative group">
              <Avatar className="h-20 w-20 border-2 border-lia-border-subtle">
                <AvatarImage src={user.avatar_url || undefined} alt={user.name} />
                <AvatarFallback className="text-xl bg-lia-bg-inverse text-lia-text-on-inverse">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <button
                type="button"
                className="absolute bottom-0 right-0 w-7 h-7 rounded-full bg-lia-bg-primary border border-lia-border-default flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-not-allowed"
                title="Upload de foto (em breve)"
                disabled
              >
                <Camera className="w-3.5 h-3.5 text-lia-text-secondary" />
              </button>
            </div>

            {ssoBadge && (
              <span className={cn(
                "text-[11px] font-medium px-2.5 py-0.5 rounded-full border",
                ssoBadge.color
              )}>
                Login via {ssoBadge.label}
              </span>
            )}
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs text-lia-text-secondary flex items-center gap-1.5">
                <User className="w-3 h-3" />
                Nome
              </Label>
              {isEditing ? (
                <div className="space-y-2">
                  <Input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="text-sm"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={handleSave}
                      disabled={isSaving}
                      className="text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:opacity-90"
                    >
                      {isSaving ? (
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      ) : saveSuccess ? (
                        <Check className="w-3 h-3 mr-1" />
                      ) : null}
                      Salvar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleCancel}
                      className="text-xs"
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <div
                  className="text-sm text-lia-text-primary px-3 py-2 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer hover:border-lia-border-default transition-colors flex items-center justify-between"
                  onClick={() => setIsEditing(true)}
                >
                  <span>{user.name}</span>
                  <span className="text-[10px] text-lia-text-tertiary">Editar</span>
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-lia-text-secondary flex items-center gap-1.5">
                <Mail className="w-3 h-3" />
                E-mail
                {isSSOUser && (
                  <span className="text-[10px] text-lia-text-tertiary">(gerenciado pelo SSO)</span>
                )}
              </Label>
              <div className="text-sm text-lia-text-primary px-3 py-2 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary">
                {user.email}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-lia-text-secondary flex items-center gap-1.5">
                <Shield className="w-3 h-3" />
                Perfil de acesso
              </Label>
              <div className="text-sm text-lia-text-primary px-3 py-2 rounded-lg border border-lia-border-subtle bg-lia-bg-secondary">
                {user.role}
              </div>
            </div>
          </div>

          {error && (
            <p className="text-xs text-status-error">{error}</p>
          )}

          <div className="pt-4">
            <button
              type="button"
              onClick={() => {
                onOpenChange(false)
                onNavigateToSettings?.()
              }}
              className="flex items-center gap-2 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors w-full px-3 py-2 rounded-lg hover:bg-lia-bg-tertiary"
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Gerenciar preferências de notificação</span>
              <ExternalLink className="w-3 h-3 ml-auto" />
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
