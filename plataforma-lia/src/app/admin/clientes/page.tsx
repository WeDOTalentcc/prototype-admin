"use client"

import React, { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import {
  ClientFilters,
  ClientTable,
  CreateClientDialog,
  Client as ComponentClient,
} from "@/components/admin/clients"
import { useClients, Client as ServiceClient } from "@/hooks/use-clients"

function mapServiceToComponentClient(client: ServiceClient): ComponentClient {
  const validStatuses = ['active', 'trial', 'suspended', 'churned', 'pending_setup'] as const
  const status = validStatuses.includes(client.status as typeof validStatuses[number])
    ? (client.status as ComponentClient['status'])
    : 'pending_setup'

  return {
    id: client.id,
    name: client.name,
    trading_name: client.tradeName,
    cnpj: client.cnpj || '',
    logo_url: client.logoUrl,
    status,
    plan: client.planId || 'starter',
    active_users: client.usersCount || 0,
    user_limit: 10,
    start_date: client.createdAt || '',
    email: client.email,
    phone: client.phone,
  }
}

export default function AdminClientesPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  
  const [searchValue, setSearchValue] = useState('')
  const [statusValue, setStatusValue] = useState('all')
  const [planFilter, setPlanFilter] = useState('all')

  const {
    clients: serviceClients,
    total,
    page,
    totalPages,
    isLoading,
    error,
    refetch,
    setPage,
    setSearch,
    setStatus,
  } = useClients({
    autoFetch: true,
    initialLimit: 12,
  })

  const clients = useMemo(
    () => serviceClients.map(mapServiceToComponentClient),
    [serviceClients]
  )

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleClientSelect = (client: ComponentClient) => {
    router.push(`/admin/clientes/${client.id}`)
  }

  const handleSearchChange = (value: string) => {
    setSearchValue(value)
    setSearch(value)
  }

  const handleStatusChange = (value: string) => {
    setStatusValue(value)
    setStatus(value === 'all' ? '' : value)
  }

  const handlePlanChange = (value: string) => {
    setPlanFilter(value)
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse motion-reduce:animate-none">
            <div className="h-8 bg-gray-200 rounded-md w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded-md w-1/2 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-lia-bg-primary rounded-md border border-lia-border-subtle p-4 h-32"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-semibold lia-text-950 dark:lia-text-50">
              Gestão de Clientes
            </h1>
            <p className="text-sm lia-text-500 dark:text-lia-text-tertiary mt-1">
              Gerencie todos os clientes da plataforma WedoTalent
            </p>
          </div>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
          >
            <Plus className="w-4 h-4 mr-2" />
            Novo Cliente
          </Button>
        </div>

        <ClientFilters
          search={searchValue}
          onSearchChange={handleSearchChange}
          status={statusValue}
          onStatusChange={handleStatusChange}
          planFilter={planFilter}
          onPlanFilterChange={handlePlanChange}
          total={total}
          isLoading={isLoading}
          mounted={mounted}
        />

        <ClientTable
          clients={clients}
          isLoading={isLoading}
          error={error}
          onClientSelect={handleClientSelect}
          onRetry={refetch}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      </div>

      <CreateClientDialog
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onSuccess={refetch}
      />
    </div>
  )
}
