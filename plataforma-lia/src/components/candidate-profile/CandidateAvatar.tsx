"use client"

import React, { memo } from "react"
import { useTranslations } from "next-intl"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

interface CandidateAvatarProps {
  name: string
  avatarUrl?: string | null
  size?: "sm" | "md" | "lg"
  className?: string
  showRing?: boolean
}

const SIZE_MAP: Record<string, string> = {
  sm: "w-7 h-7",
  md: "w-10 h-10",
  lg: "w-12 h-12",
}

const TEXT_SIZE_MAP: Record<string, string> = {
  sm: "text-micro",
  md: "text-xs",
  lg: "text-sm",
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase()
}

const CandidateAvatar = memo(function CandidateAvatar({
  name,
  avatarUrl,
  size = "md",
  className,
  showRing = false,
}: CandidateAvatarProps) {
  const t = useTranslations('candidates.profile')
  return (
    <Avatar
      className={cn(
        SIZE_MAP[size],
        "flex-shrink-0",
        showRing && "ring-2 ring-white",
        className
      )}
    >
      <AvatarImage src={avatarUrl || undefined} alt={t('avatarAlt', { name })} />
      <AvatarFallback
        className={cn(
          "font-semibold bg-lia-bg-tertiary text-lia-text-primary",
          TEXT_SIZE_MAP[size]
        )}
      >
        {getInitials(name)}
      </AvatarFallback>
    </Avatar>
  )
})

CandidateAvatar.displayName = "CandidateAvatar"

export { CandidateAvatar, getInitials }
export type { CandidateAvatarProps }
