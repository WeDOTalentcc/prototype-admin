"use client"

/**
 * LogoUploadField — upload de logo da empresa (audit 2026-05-20 Sessão I Step 4).
 *
 * Backend: POST /api/backend-proxy/company/profile/{profileId}/logo (multipart)
 * → encoda em base64 data URL → persiste em company_profiles.logo_url (TEXT
 *   após migration 152_logo_url_to_text).
 *
 * Auto-fetches profile.id via GET /api/backend-proxy/company/profile.
 * Multi-tenancy: profile já é tenant-scoped pelo JWT no backend.
 * Limites: PNG/JPG/SVG/WEBP, <500KB.
 */

import React, { useState, useRef, useEffect, useCallback } from "react"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import { Upload, Image as ImageIcon, Loader2, AlertCircle, Check } from "lucide-react"
import { Button } from "@/components/ui/button"

interface LogoUploadFieldProps {
  currentValue: string | null
  onUploadSuccess: (newUrl: string) => void
  disabled?: boolean
}

export function LogoUploadField({
  currentValue,
  onUploadSuccess,
  disabled = false,
}: LogoUploadFieldProps) {
  const [profileId, setProfileId] = useState<string | null>(null)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successFlash, setSuccessFlash] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // Fetch profile.id on mount (tenant-scoped via JWT)
  useEffect(() => {
    let cancelled = false
    async function fetchProfileId() {
      try {
        const res = await fetch("/api/backend-proxy/company/profile")
        if (!res.ok) throw new Error(`Profile fetch failed: ${res.status}`)
        const data = await res.json()
        if (!cancelled && data?.id) {
          setProfileId(data.id)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Não foi possível carregar perfil da empresa")
        }
      } finally {
        if (!cancelled) setIsLoadingProfile(false)
      }
    }
    fetchProfileId()
    return () => {
      cancelled = true
    }
  }, [])

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file || !profileId) {
        if (!profileId) setError("ID do perfil ainda não carregado.")
        return
      }
      setError(null)
      setIsUploading(true)
      try {
        const formData = new FormData()
        formData.append("file", file)
        const res = await fetch(
          `/api/backend-proxy/company/profile/${encodeURIComponent(profileId)}/logo`,
          { method: "POST", body: formData },
        )
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}))
          throw new Error(
            errBody.detail ||
              errBody.error ||
              `Upload falhou (HTTP ${res.status})`,
          )
        }
        const data = await res.json()
        if (data.logo_url) {
          onUploadSuccess(data.logo_url)
          notifyChatOfSettingsUpdate({
            actionId: "upload_company_logo",
            section: "profile",
            field: "logo_url",
            value: data.logo_url,
          })
          setSuccessFlash(true)
          setTimeout(() => setSuccessFlash(false), 2000)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro inesperado no upload")
      } finally {
        setIsUploading(false)
        if (fileInputRef.current) fileInputRef.current.value = ""
      }
    },
    [profileId, onUploadSuccess],
  )

  const hasLogo = !!currentValue && currentValue.length > 10
  const isBusy = isLoadingProfile || isUploading
  const canUpload = !disabled && !isBusy && !!profileId

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-3">
        {hasLogo ? (
          <div className="relative w-10 h-10 rounded-md border border-lia-border-default dark:border-lia-border-subtle overflow-hidden bg-lia-bg-secondary flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={currentValue}
              alt="Logo da empresa"
              className="max-w-full max-h-full object-contain"
            />
          </div>
        ) : (
          <div className="w-10 h-10 rounded-md border border-dashed border-lia-border-default dark:border-lia-border-subtle bg-lia-bg-secondary flex items-center justify-center">
            <ImageIcon className="w-4 h-4 text-lia-text-secondary" />
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/svg+xml,image/webp"
          onChange={handleFileChange}
          disabled={!canUpload}
          className="hidden"
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={!canUpload}
          className="gap-1.5"
        >
          {isBusy ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Upload className="w-3 h-3" />
          )}
          <span className="text-xs">
            {hasLogo ? "Trocar" : "Enviar logo"}
          </span>
        </Button>
        {successFlash && (
          <Check className="w-4 h-4 text-status-success" />
        )}
      </div>
      {error && (
        <div className="flex items-center gap-1 text-xs text-status-error">
          <AlertCircle className="w-3 h-3" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
