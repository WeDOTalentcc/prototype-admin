"use client"

import React from "react"
import { useTranslations } from "next-intl"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  MoreVertical,
  Mail,
  MessageCircle,
  Calendar,
  ClipboardList,
  MessageSquareText,
  Bookmark,
  Heart,
} from "lucide-react"

interface KanbanCardActionsProps {
  candidate: {
    id: string
    name: string
    [key: string]: unknown
  }
  shortListedCandidateIds: Set<string>
  favoriteCandidates: Set<string>
  onOpenPreview: (candidate: unknown) => void
  onSendEmail: (candidate: unknown) => void
  onSendWhatsApp: (candidate: unknown) => void
  onScheduleInterview: (candidate: unknown) => void
  onSendWSIInvite: (candidate: unknown) => void
  onSendFeedback: (candidate: unknown) => void
  onToggleShortList: (candidateId: string) => void
  onToggleFavorite: (candidateId: string) => void
}

export function KanbanCardActions({
  candidate,
  shortListedCandidateIds,
  favoriteCandidates,
  onOpenPreview,
  onSendEmail,
  onSendWhatsApp,
  onScheduleInterview,
  onSendWSIInvite,
  onSendFeedback,
  onToggleShortList,
  onToggleFavorite,
}: KanbanCardActionsProps) {
  const t = useTranslations('kanban')
  return (
    <>
{/* Ações rápidas - Posicionadas no canto direito */}
<div className="absolute right-2 top-8 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none z-10">
  {/* Menu de opções - Primeiro */}
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <button
        className="p-1 hover:bg-lia-bg-tertiary rounded-xl transition-opacity motion-reduce:transition-none bg-lia-bg-primary/80"
        onClick={(e) => e.stopPropagation()}
        title={t('moreOptions')}
        aria-label={t('moreOptionsCandidateAria')}
      >
        <MoreVertical className="w-3 h-3 text-lia-text-secondary" aria-hidden="true" />
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent side="right" align="start" sideOffset={8} className="w-48">
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendEmail(candidate)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <Mail className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        {t('sendEmail')}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendWhatsApp(candidate)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <MessageCircle className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        {t('sendWhatsApp')}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onScheduleInterview(candidate)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <Calendar className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        {t('scheduleInterview')}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendWSIInvite(candidate)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <ClipboardList className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        {t('wsiScreening')}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendFeedback(candidate)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <MessageSquareText className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        {t('sendFeedback')}
      </DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onToggleShortList(candidate.id)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <Bookmark
          className={`w-3.5 h-3.5 mr-2 ${
            shortListedCandidateIds.has(candidate.id)
              ? "fill-lia-btn-primary-bg text-lia-text-primary dark:fill-lia-bg-secondary"
              : "text-lia-text-tertiary"
          }`}
        />
        {shortListedCandidateIds.has(candidate.id)
          ? t('removeFromShortList')
          : t('addToShortList')}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onToggleFavorite(candidate.id)
        }}
        className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer"
      >
        <Heart
          className={`w-3.5 h-3.5 mr-2 ${
            favoriteCandidates.has(candidate.id)
              ? "fill-red-500 text-status-error"
              : "text-lia-text-tertiary"
          }`}
        />
        {favoriteCandidates.has(candidate.id)
          ? t('removeFromFavorites')
          : t('addToFavorites')}
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>

</div>
    </>
  )
}
