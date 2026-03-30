"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Building2, AlertCircle, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react"
import { Client } from "./types"
import { ClientCard } from "./ClientCard"

export interface ClientTableProps {
  clients: Client[]
  isLoading: boolean
  error?: string | null
  onClientSelect?: (client: Client) => void
  emptyMessage?: string
  onRetry?: () => void
  page?: number
  totalPages?: number
  onPageChange?: (page: number) => void
}

function ClientSkeleton() {
  return (
    <Card className="overflow-hidden animate-pulse motion-reduce:animate-none">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-md bg-gray-200 dark:bg-lia-bg-elevated" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-3/4" />
            <div className="h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-1/2" />
          </div>
          <div className="h-5 w-16 bg-gray-200 dark:bg-lia-bg-elevated rounded-full" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-1/2" />
            <div className="h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-3/4" />
          </div>
          <div className="space-y-1">
            <div className="h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-1/2" />
            <div className="h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md w-3/4" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState({ message, onRetry }: { message?: string, onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center mb-4">
        <Building2 className="w-8 h-8 lia-text-secondary" />
      </div>
      <h3 className="text-lg font-medium text-lia-text-primary mb-1">
        Nenhum cliente encontrado
      </h3>
      <p className="text-sm text-lia-text-tertiary dark:text-lia-text-tertiary text-center max-w-md mb-4">
        {message || 'Não encontramos clientes com os filtros selecionados. Tente ajustar sua busca ou adicione um novo cliente.'}
      </p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      )}
    </div>
  )
}

function ErrorState({ message, onRetry }: { message: string, onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-full bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-status-error" />
      </div>
      <h3 className="text-lg font-medium text-lia-text-primary mb-1">
        Erro ao carregar clientes
      </h3>
      <p className="text-sm text-lia-text-tertiary dark:text-lia-text-tertiary text-center max-w-md mb-4">
        {message}
      </p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      )}
    </div>
  )
}

export function ClientTable({
  clients,
  isLoading,
  error,
  onClientSelect,
  emptyMessage,
  onRetry,
  page = 1,
  totalPages = 1,
  onPageChange,
}: ClientTableProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <ClientSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />
  }

  if (clients.length === 0) {
    return <EmptyState message={emptyMessage} onRetry={onRetry} />
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clients.map((client) => (
          <ClientCard
            key={client.id}
            client={client}
            onSelect={onClientSelect}
          />
        ))}
      </div>

      {totalPages > 1 && onPageChange && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
              let pageNum: number
              if (totalPages <= 5) {
                pageNum = i + 1
              } else if (page <= 3) {
                pageNum = i + 1
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i
              } else {
                pageNum = page - 2 + i
              }
              return (
                <Button
                  key={pageNum}
                  variant={page === pageNum ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onPageChange(pageNum)}
                  className={page === pageNum ? 'bg-gray-900 hover:bg-wedo-cyan-dark' : ''}
                >
                  {pageNum}
                </Button>
              )
            })}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </>
  )
}
