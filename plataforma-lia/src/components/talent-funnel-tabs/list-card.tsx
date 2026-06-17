"use client"

import { Button } from "@/components/ui/button"
import {
  List, MoreHorizontal, Edit2, Trash2, Users,
  Calendar, Briefcase, ChevronRight, UserPlus, Share2
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { ListCardProps, formatDate, truncateText } from "./lists-tab-types"

export function ListCard({
  list,
  onSelect,
  onEdit,
  onDelete,
  onAddToJobs,
  onAddCandidate,
  onShare,
}: ListCardProps) {
  return (
    <div
      onClick={() => onSelect(list.id)}
      className="group relative flex items-center gap-4 p-4 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none cursor-pointer"
    >
      <div
        className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center relative bg-lia-bg-tertiary"
      >
        <List className="w-5 h-5 text-lia-text-secondary" />
        <div
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white"
          style={{backgroundColor: list.color || 'var(--lia-text-tertiary)'}}
        />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-sm font-medium text-lia-text-primary truncate transition-colors motion-reduce:transition-none">
            {list.name}
          </p>
        </div>
        {list.description && (
          <p className="text-xs text-lia-text-secondary truncate">
            {truncateText(list.description, 60)}
          </p>
        )}
      </div>

      <div className="flex-shrink-0 flex flex-col items-center justify-center px-4 border-l border-r border-lia-border-subtle dark:border-lia-border-subtle">
        <span className="text-2xl font-semibold text-lia-text-primary">
          {list.candidate_count || 0}
        </span>
        <span className="text-micro text-lia-text-tertiary uppercase tracking-wide" aria-live="polite" aria-atomic="true">
          {(list.candidate_count || 0) === 1 ? 'candidato' : 'candidatos'}
        </span>
      </div>

      <div className="flex-shrink-0 flex items-center gap-1.5 text-xs text-lia-text-secondary min-w-[100px]">
        <Calendar className="w-3.5 h-3.5" />
        <span>{formatDate(list.updated_at || list.created_at)}</span>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary"
          onClick={(e) => { e.stopPropagation(); onAddCandidate(list) }}
          title="Adicionar candidatos"
        >
          <UserPlus className="w-4 h-4 text-lia-text-secondary" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary"
          onClick={(e) => { e.stopPropagation(); onShare(list) }}
          title="Compartilhar lista"
        >
          <Share2 className="w-4 h-4 text-lia-text-secondary" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary"
          onClick={(e) => { e.stopPropagation(); onEdit(list) }}
          title="Editar lista"
        >
          <Edit2 className="w-4 h-4 text-lia-text-secondary" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary"
          onClick={(e) => { e.stopPropagation(); onAddToJobs(list.id) }}
          title="Adicionar a vagas"
        >
          <Briefcase className="w-4 h-4 text-lia-text-secondary" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:text-status-error hover:bg-status-error/10"
          onClick={(e) => { e.stopPropagation(); onDelete(list) }}
          title="Excluir lista"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onAddCandidate(list) }}>
              <UserPlus className="w-4 h-4 mr-2" />
              Adicionar candidatos
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onSelect(list.id) }}>
              <Users className="w-4 h-4 mr-2" />
              Ver candidatos
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onAddToJobs(list.id) }}>
              <Briefcase className="w-4 h-4 mr-2" />
              Adicionar a vagas
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onShare(list) }}>
              <Share2 className="w-4 h-4 mr-2" />
              Compartilhar lista
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(list) }}>
              <Edit2 className="w-4 h-4 mr-2" />
              Editar lista
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => { e.stopPropagation(); onDelete(list) }}
              className="text-status-error focus:text-status-error focus:bg-status-error/10"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Excluir lista
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <ChevronRight className="w-5 h-5 text-lia-text-tertiary group-hover:text-lia-text-secondary transition-colors motion-reduce:transition-none flex-shrink-0" />
    </div>
  )
}
