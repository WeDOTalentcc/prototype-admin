"use client"

import React from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  MoreVertical,
  Eye,
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
  return (
    <>
{/* Ações rápidas - Posicionadas no canto direito */}
<div className="absolute right-2 top-8 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none z-10">
  {/* Menu de opções - Primeiro */}
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <button
        className="p-1 hover:bg-gray-100 rounded-md transition-opacity motion-reduce:transition-none bg-lia-bg-primary/80"
        onClick={(e) => e.stopPropagation()}
        title="Mais opções"
        aria-label="Mais opções do candidato"
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
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <Mail className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        Enviar Email
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendWhatsApp(candidate)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <MessageCircle className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        Enviar WhatsApp
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onScheduleInterview(candidate)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <Calendar className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        Agendar Entrevista
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendWSIInvite(candidate)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <ClipboardList className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        Triagem WSI
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onSendFeedback(candidate)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <MessageSquareText className="w-3.5 h-3.5 mr-2 text-lia-text-tertiary" />
        Enviar Feedback
      </DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onToggleShortList(candidate.id)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <Bookmark
          className={`w-3.5 h-3.5 mr-2 ${
            shortListedCandidateIds.has(candidate.id)
              ? "fill-gray-900 text-lia-text-primary dark:fill-gray-50 dark:text-lia-text-primary"
              : "text-lia-text-tertiary"
          }`}
        />
        {shortListedCandidateIds.has(candidate.id)
          ? "Remover da Short List"
          : "Adicionar à Short List"}
      </DropdownMenuItem>
      <DropdownMenuItem
        onClick={(e) => {
          e.stopPropagation()
          onToggleFavorite(candidate.id)
        }}
        className="text-xs text-lia-text-primary dark:text-lia-text-primary hover:bg-gray-50 cursor-pointer"
      >
        <Heart
          className={`w-3.5 h-3.5 mr-2 ${
            favoriteCandidates.has(candidate.id)
              ? "fill-red-500 text-status-error"
              : "text-lia-text-tertiary"
          }`}
        />
        {favoriteCandidates.has(candidate.id)
          ? "Remover dos Favoritos"
          : "Adicionar a Favoritos"}
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>

  {/* Botão de Preview */}
  <button
    className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none bg-lia-bg-primary/80"
    onClick={(e) => {
      e.stopPropagation()
      onOpenPreview(candidate)
    }}
    title="Ver detalhes do candidato"
    aria-label={`Ver detalhes de ${candidate.name}`}
  >
    <Eye className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" aria-hidden="true" />
  </button>
</div>
    </>
  )
}
