"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Building2, Users, Calendar, UserCircle } from "lucide-react"
import { Client, statusConfig } from "./types"

export interface ClientCardProps {
  client: Client
  onSelect?: (client: Client) => void
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function formatCNPJ(cnpj: string) {
  const cleaned = cnpj.replace(/\D/g, '')
  if (cleaned.length !== 14) return cnpj
  return cleaned.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
}

export function ClientCard({ client, onSelect }: ClientCardProps) {
  const status = statusConfig[client.status] || statusConfig.pending_setup

  return (
    <Card 
      className="overflow-hidden hover:transition-shadow cursor-pointer group"
      onClick={() => onSelect?.(client)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {client.logo_url ? (
            <img
              src={client.logo_url}
              alt={client.name}
              className="w-12 h-12 rounded-md object-cover border border-gray-200 dark:border-gray-600"
            />
          ) : (
            <div className="w-12 h-12 rounded-md bg-gray-100 dark:bg-gray-700 flex items-center justify-center border border-gray-200 dark:border-gray-600">
              <Building2 className="w-6 h-6 text-gray-400" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-950 dark:text-gray-50 truncate group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors">
              {client.name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {formatCNPJ(client.cnpj)}
            </p>
          </div>
          <Badge variant={status.variant}>{status.label}</Badge>
        </div>
        
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gray-50 dark:bg-gray-700 flex items-center justify-center">
              <Users className="w-3 h-3 text-gray-400" />
            </div>
            <div>
              <p className="text-micro text-gray-500 dark:text-gray-400 uppercase">Usuários</p>
              <p className="text-xs font-medium text-gray-950 dark:text-gray-50">
                {client.active_users}/{client.user_limit}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gray-50 dark:bg-gray-700 flex items-center justify-center">
              <Calendar className="w-3 h-3 text-gray-400" />
            </div>
            <div>
              <p className="text-micro text-gray-500 dark:text-gray-400 uppercase">Início</p>
              <p className="text-xs font-medium text-gray-950 dark:text-gray-50">
                {formatDate(client.start_date)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-micro">
              {client.plan}
            </Badge>
          </div>
          {client.account_manager && (
            <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <UserCircle className="w-3 h-3" />
              <span className="truncate max-w-[100px]">{client.account_manager}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
