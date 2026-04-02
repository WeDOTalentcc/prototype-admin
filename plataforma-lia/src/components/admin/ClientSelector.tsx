"use client"

import * as React from "react"
import { Check, ChevronsUpDown, Building2, Users } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { useClient, Client } from "@/contexts/ClientContext"

function getStatusVariant(status: string): "success" | "warning" | "secondary" | "default" {
  switch (status?.toLowerCase()) {
    case "active":
    case "ativo":
      return "success"
    case "trial":
      return "warning"
    case "suspended":
    case "suspenso":
      return "destructive" as "secondary"
    default:
      return "default"
  }
}

function getStatusLabel(status: string): string {
  switch (status?.toLowerCase()) {
    case "active":
      return "Ativo"
    case "trial":
      return "Trial"
    case "suspended":
      return "Suspenso"
    case "inactive":
      return "Inativo"
    default:
      return status || "N/A"
  }
}

function getClientInitials(client: Client): string {
  const name = client.tradeName || client.name || ""
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

export function ClientSelector() {
  const { clients, selectedClient, setSelectedClient, isLoading } = useClient()
  const [open, setOpen] = React.useState(false)

  const handleSelect = (client: Client | null) => {
    setSelectedClient(client)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[280px] justify-between bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary"
        >
          {selectedClient ? (
            <div className="flex items-center gap-2 truncate">
              <Avatar className="h-5 w-5">
                {selectedClient.logoUrl ? (
                  <AvatarImage src={selectedClient.logoUrl} alt={selectedClient.name} />
                ) : null}
                <AvatarFallback 
                  className="text-micro bg-lia-btn-primary-bg text-lia-btn-primary-text"
                >
                  {getClientInitials(selectedClient)}
                </AvatarFallback>
              </Avatar>
              <span className="truncate">
                {selectedClient.tradeName || selectedClient.name}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span>Todos os Clientes</span>
            </div>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Buscar cliente..." />
          <CommandList>
            <CommandEmpty>
              {isLoading ? "Carregando..." : "Nenhum cliente encontrado."}
            </CommandEmpty>
            <CommandGroup>
              <CommandItem
                onSelect={() => handleSelect(null)}
                className="flex items-center gap-3 py-2"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                  <Users className="h-4 w-4 text-lia-text-secondary" />
                </div>
                <div className="flex flex-col">
                  <span className="font-medium">Todos os Clientes</span>
                  <span className="text-xs text-lia-text-secondary">Visão global do admin</span>
                </div>
                {!selectedClient && (
                  <Check className="ml-auto h-4 w-4 text-lia-text-secondary" />
                )}
              </CommandItem>
            </CommandGroup>
            {clients.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Clientes">
                  {clients.map((client) => (
                    <CommandItem
                      key={client.id}
                      value={`${client.name} ${client.tradeName || ""} ${client.cnpj || ""}`}
                      onSelect={() => handleSelect(client)}
                      className="flex items-center gap-3 py-2"
                    >
                      <Avatar className="h-8 w-8">
                        {client.logoUrl ? (
                          <AvatarImage src={client.logoUrl} alt={client.name} />
                        ) : null}
                        <AvatarFallback 
                          className="text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text"
                        >
                          {getClientInitials(client)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex flex-1 flex-col min-w-0">
                        <span className="font-medium truncate">
                          {client.tradeName || client.name}
                        </span>
                        {client.cnpj && (
                          <span className="text-xs text-lia-text-secondary truncate">
                            CNPJ: {client.cnpj}
                          </span>
                        )}
                      </div>
                      <Badge 
                        variant={getStatusVariant(client.status)}
                        className="shrink-0 ml-1"
                      >
                        {getStatusLabel(client.status)}
                      </Badge>
                      {selectedClient?.id === client.id && (
                        <Check className="h-4 w-4 text-lia-text-secondary shrink-0" />
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
