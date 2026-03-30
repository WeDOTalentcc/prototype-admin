"use client"

import * as React from "react"
import { 
  User, 
  Briefcase, 
  Building2, 
  UserCheck, 
  Calendar, 
  BarChart3, 
  GitBranch, 
  FileText, 
  Settings,
  Variable,
  Search,
  ChevronRight
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { 
  VARIABLE_REGISTRY, 
  formatVariable,
  type VariableGroup,
  type TemplateVariable 
} from "@/lib/template-variables"

const iconMap: Record<string, React.ElementType> = {
  user: User,
  briefcase: Briefcase,
  building: Building2,
  'user-check': UserCheck,
  calendar: Calendar,
  'bar-chart': BarChart3,
  'git-branch': GitBranch,
  'file-text': FileText,
  settings: Settings,
}

function getGroupIcon(iconName?: string): React.ElementType {
  if (!iconName) return Variable
  return iconMap[iconName] || Variable
}

export interface VariableSelectorProps {
  onSelect: (variable: string) => void
  trigger?: React.ReactNode
  disabled?: boolean
  className?: string
  side?: "top" | "right" | "bottom" | "left"
  align?: "start" | "center" | "end"
}

export function VariableSelector({
  onSelect,
  trigger,
  disabled = false,
  className,
  side = "bottom",
  align = "end"
}: VariableSelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeGroup, setActiveGroup] = React.useState<string | null>(null)

  const handleSelect = React.useCallback((variable: TemplateVariable) => {
    const formattedVariable = formatVariable(variable.key)
    onSelect(formattedVariable)
    setOpen(false)
    setSearchQuery("")
    setActiveGroup(null)
  }, [onSelect])

  const filteredRegistry = React.useMemo(() => {
    if (!searchQuery.trim()) {
      return activeGroup 
        ? VARIABLE_REGISTRY.filter(g => g.id === activeGroup)
        : VARIABLE_REGISTRY
    }
    
    const query = searchQuery.toLowerCase()
    return VARIABLE_REGISTRY.map(group => ({
      ...group,
      variables: group.variables.filter(v => 
        v.label.toLowerCase().includes(query) ||
        v.key.toLowerCase().includes(query) ||
        v.description.toLowerCase().includes(query)
      )
    })).filter(group => group.variables.length > 0)
  }, [searchQuery, activeGroup])

  const totalVariables = VARIABLE_REGISTRY.reduce((acc, g) => acc + g.variables.length, 0)

  return (
    <Popover open={open} onOpenChange={(isOpen: boolean) => {
      setOpen(isOpen)
      if (!isOpen) {
        setSearchQuery("")
        setActiveGroup(null)
      }
    }}>
      <PopoverTrigger asChild disabled={disabled}>
        {trigger || (
          <Button
            variant="outline"
            size="sm"
            className={cn("gap-2 rounded-md text-xs", className)}
            disabled={disabled}
           
          >
            <Variable className="h-3.5 w-3.5" />
            Inserir Variável
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0 border rounded-md overflow-hidden z-max bg-lia-bg-primary border-lia-border-subtle" 
        side={side} 
        align={align}
      >
        <div className="p-3 border-b border-lia-border-subtle">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
                <Variable className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
              </div>
              <h3 className="text-xs font-semibold lia-text-strong">
                Variáveis Disponíveis
              </h3>
            </div>
            <Badge variant="secondary" className="text-micro px-1.5 py-0.5 bg-gray-100 lia-text-base">
              {totalVariables} variáveis
            </Badge>
          </div>
          
          <div className="relative mb-2.5">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 lia-text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar variável..."
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 focus:outline-none"
             
            />
          </div>

          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveGroup(null)}
              className={cn(
 "px-2 py-0.5 rounded-md text-micro font-medium transition-colors",
                !activeGroup 
                  ? "bg-gray-900 text-white" 
                  : "bg-gray-100 lia-text-base hover:bg-gray-200"
              )}
            >
              Todas
            </button>
            {VARIABLE_REGISTRY.map((group) => (
              <button
                key={group.id}
                onClick={() => setActiveGroup(activeGroup === group.id ? null : group.id)}
                className={cn(
 "px-2 py-0.5 rounded-md text-micro font-medium transition-colors",
                  activeGroup === group.id 
                    ? "bg-gray-900 text-white" 
                    : "bg-gray-100 lia-text-base hover:bg-gray-200"
                )}
              >
                {group.label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-h-[280px] overflow-y-auto p-2 space-y-1">
          {filteredRegistry.length === 0 ? (
            <div className="py-6 text-center">
              <Variable className="w-8 h-8 mx-auto mb-2 lia-text-muted" />
              <p className="text-xs lia-text-secondary">
                Nenhuma variável encontrada
              </p>
            </div>
          ) : (
            filteredRegistry.map((group) => (
              <VariableGroupComponent
                key={group.id}
                group={group}
                onSelect={handleSelect}
              />
            ))
          )}
        </div>

        <div className="p-2 border-t border-lia-border-subtle">
          <p className="text-micro lia-text-secondary text-center">
            Clique para inserir a variável no template
          </p>
        </div>
      </PopoverContent>
    </Popover>
  )
}

interface VariableGroupComponentProps {
  group: VariableGroup
  onSelect: (variable: TemplateVariable) => void
}

function VariableGroupComponent({ group, onSelect }: VariableGroupComponentProps) {
  const Icon = getGroupIcon(group.icon)
  
  return (
    <div className="mb-2">
      <div className="flex items-center gap-1.5 px-2 py-1">
        <Icon className="w-3 h-3 lia-text-secondary" />
        <span className="text-micro font-semibold lia-text-secondary uppercase tracking-wide">
          {group.label}
        </span>
      </div>
      <div className="space-y-0.5">
        {group.variables.map((variable) => (
          <button
            key={variable.key}
            onClick={() => onSelect(variable)}
            className="w-full p-2 rounded-md text-left transition-colors group hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent hover:border-lia-border-subtle dark:hover:border-gray-700"
          >
            <div className="flex items-start gap-2.5">
              <div className="w-7 h-7 rounded-md bg-gray-100 flex items-center justify-center flex-shrink-0 group-hover:bg-gray-200 dark:group-hover:bg-gray-700 transition-colors">
                <code className="text-micro font-mono text-gray-600 dark:text-lia-text-tertiary">
                  {"{{}}"}
                </code>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <code className="text-micro font-mono px-1.5 py-0.5 rounded-md bg-gray-100 group-hover:bg-gray-200 dark:group-hover:bg-gray-700 text-gray-700 dark:text-lia-text-secondary">
                    {`{{${variable.key}}}`}
                  </code>
                  <span className="text-xs font-medium lia-text-strong truncate">
                    {variable.label}
                  </span>
                  <ChevronRight className="w-3 h-3 lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity ml-auto flex-shrink-0" />
                </div>
                <p className="text-micro lia-text-secondary line-clamp-1">
                  {variable.description}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export { VARIABLE_REGISTRY }
