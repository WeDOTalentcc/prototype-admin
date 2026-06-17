"use client"

import React, { memo, useCallback } from "react"
import { useTranslations } from "next-intl"
import { Mail, Phone, Linkedin } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface CandidateContactActionsProps {
  email?: string | null
  phone?: string | null
  linkedinUrl?: string | null
  size?: "sm" | "md"
  className?: string
  onSendEmail?: () => void
  onSendWhatsApp?: () => void
  onOpenLinkedIn?: () => void
}

const CandidateContactActions = memo(function CandidateContactActions({
  email,
  phone,
  linkedinUrl,
  size = "sm",
  className,
  onSendEmail,
  onSendWhatsApp,
  onOpenLinkedIn,
}: CandidateContactActionsProps) {
  const t = useTranslations('candidates.profile')
  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4"
  const buttonSize = size === "sm" ? "h-6 w-6 p-0" : "h-7 w-7 p-0"

  const handleEmail = useCallback(() => {
    if (onSendEmail) {
      onSendEmail()
    } else if (email) {
      window.open(`mailto:${email}`, "_self")
    }
  }, [onSendEmail, email])

  const handleWhatsApp = useCallback(() => {
    if (onSendWhatsApp) {
      onSendWhatsApp()
    } else if (phone) {
      window.open(
        `https://wa.me/${phone.replace(/\D/g, "")}`,
        "_blank"
      )
    }
  }, [onSendWhatsApp, phone])

  const handleLinkedIn = useCallback(() => {
    if (onOpenLinkedIn) {
      onOpenLinkedIn()
    } else if (linkedinUrl) {
      window.open(linkedinUrl, "_blank", "noopener,noreferrer")
    }
  }, [onOpenLinkedIn, linkedinUrl])

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      {(email || onSendEmail) && (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              buttonSize,
              "hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-secondary"
            )}
            onClick={handleEmail}
            aria-label={t("contactEmail")}
          >
            <Mail
              className={cn(
                iconSize,
                "text-lia-text-secondary"
              )}
            />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs">
          {t('contactEmail')}
        </TooltipContent>
      </Tooltip>
      )}

      {(phone || onSendWhatsApp) && (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              buttonSize,
              "hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-secondary"
            )}
            onClick={handleWhatsApp}
            aria-label={t("contactWhatsApp")}
          >
            <Phone
              className={cn(
                iconSize,
                "text-lia-text-secondary"
              )}
            />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs">
          {t('contactWhatsApp')}
        </TooltipContent>
      </Tooltip>
      )}

      {(linkedinUrl || onOpenLinkedIn) && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                buttonSize,
                "hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              )}
              onClick={handleLinkedIn}
              aria-label={t("contactLinkedIn")}
            >
              <Linkedin
                className={cn(
                  iconSize,
                  "text-lia-text-secondary"
                )}
              />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">
            {t('contactLinkedIn')}
          </TooltipContent>
        </Tooltip>
      )}
    </div>
  )
})

CandidateContactActions.displayName = "CandidateContactActions"

export { CandidateContactActions }
export type { CandidateContactActionsProps }
