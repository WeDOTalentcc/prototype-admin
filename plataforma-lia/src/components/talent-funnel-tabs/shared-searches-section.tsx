"use client"

import { Chip } from"@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Link2, MoreHorizontal, ThumbsUp, ThumbsDown,
  HelpCircle, Clock, Eye, Copy, Send, XCircle, Loader2
} from"lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from"@/components/ui/dropdown-menu"
import { SharedSearchesSectionProps } from"./lists-tab-types"

function getStatusBadge(status: 'active' | 'expired' | 'revoked') {
  switch (status) {
    case 'active':
      return <Chip variant="success">Ativo</Chip>
    case 'expired':
      return <Chip variant="danger">Expirado</Chip>
    case 'revoked':
      return <Chip variant="neutral" muted>Revogado</Chip>
  }
}

export function SharedSearchesSection({
  sharedSearches,
  loadingShared,
  totalNewFeedbacks,
  onViewDetails,
  onCopyLink,
  onResendInvite,
  onRevokeShare,
}: SharedSearchesSectionProps) {
  return (
    <div className="mt-8 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
          <Link2 className="w-4 h-4 text-lia-text-secondary" />
          Compartilhados
          {totalNewFeedbacks > 0 && (
            <Chip variant="neutral" muted className="ml-2">
              {totalNewFeedbacks} {totalNewFeedbacks === 1 ? 'novo' : 'novos'} ●
            </Chip>
          )}
        </h3>
      </div>

      {loadingShared ? (
        <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          <span className="ml-2 text-xs text-lia-text-secondary">Carregando compartilhamentos...</span>
        </div>
      ) : sharedSearches.length > 0 ? (
        <div className="space-y-2">
          {sharedSearches.map((shared) => (
            <div
              key={shared.id}
              className="group relative p-4 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                    <Link2 className="w-5 h-5 text-lia-text-secondary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-lia-text-primary">
                        {shared.title}
                      </p>
                      {getStatusBadge(shared.status)}
                    </div>
                    <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                      {shared.share_type === 'search' ? 'Busca' : 'Lista'} • {shared.candidate_count} {shared.candidate_count === 1 ? 'candidato' : 'candidatos'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mb-3">
                <p className="text-xs text-lia-text-secondary">
                  <span className="font-medium">Destinatário:</span> {shared.recipient_name || shared.recipient_email}
                </p>
                <p className="text-xs flex items-center gap-1">
                  {shared.first_accessed_at ? (
                    <>
                      <Eye className="w-3 h-3 text-status-success" />
                      <span className="text-status-success">Acessado</span>
                    </>
                  ) : (
                    <>
                      <Clock className="w-3 h-3 text-lia-text-secondary" />
                      <span className="lia-text-secondary">Não acessou ainda</span>
                    </>
                  )}
                </p>
              </div>

              <div className={`flex items-center gap-3 text-xs ${shared.feedback_counts?.new_count > 0 ? 'text-lia-text-primary font-medium' : 'text-lia-text-secondary'}`}>
                <span className="font-medium">Feedbacks:</span>
                <span className="flex items-center gap-1">
                  <ThumbsUp className="w-3 h-3" />
                  {shared.feedback_counts?.approved || 0}
                </span>
                <span className="flex items-center gap-1">
                  <ThumbsDown className="w-3 h-3" />
                  {shared.feedback_counts?.rejected || 0}
                </span>
                <span className="flex items-center gap-1">
                  <HelpCircle className="w-3 h-3" />
                  {shared.feedback_counts?.maybe || 0}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {shared.feedback_counts?.pending || 0}
                </span>
              </div>

              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => onViewDetails(shared.id)}
                >
                  <Eye className="w-3 h-3" />
                  Ver Detalhes
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => onCopyLink(shared.share_url)}
                >
                  <Copy className="w-3 h-3" />
                  Copiar Link
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-44">
                    <DropdownMenuItem onClick={() => onResendInvite(shared.id)}>
                      <Send className="w-4 h-4 mr-2" />
                      Reenviar Convite
                    </DropdownMenuItem>
                    {shared.status === 'active' && (
                      <DropdownMenuItem
                        onClick={() => onRevokeShare(shared.id)}
                        className="text-status-error focus:text-status-error focus:bg-status-error/10"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Encerrar
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-10 px-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl border border-dashed border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
            <Link2 className="w-6 h-6 text-lia-text-muted" />
          </div>
          <p className="text-sm text-lia-text-secondary text-center max-w-sm">
            Nenhum compartilhamento. Compartilhe buscas ou listas com gestores para receber feedback.
          </p>
        </div>
      )}
    </div>
  )
}
