"use client"

import * as React from"react"
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
} from"lucide-react"

import { cn } from"@/lib/utils"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { 
  VARIABLE_REGISTRY, 
  formatVariable,
  type VariableGroup,
  type TemplateVariable 
} from"@/lib/template-variables"

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
  side?:"top" |"right" |"bottom" |"left"
  align?:"start" |"center" |"end"
}

export function VariableSelector({
  onSelect,
  trigger,
  disabled = false,
  className,
  side ="bottom",
  align ="end"
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
        className="w-80 p-0 border rounded-xl overflow-hidden z-max bg-lia-bg-primary border-lia-border-subtle" 
        side={side} 
        align={align}
      >
        <div className="p-3">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                <Variable className="w-3.5 h-3.5 text-lia-text-secondary" />
              </div>
              <h3 className="text-xs font-semibold text-lia-text-primary">
                Variáveis Disponíveis
              </h3>
            </div>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary">
              {totalVariables} variáveis
            </Chip>
          </div>
          
          <div className="relative mb-2.5">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar variável..."
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium focus:outline-none"
             
            />
          </div>

          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveGroup(null)}
              className={cn("px-2 py-0.5 rounded-md text-micro font-medium transition-colors",
                !activeGroup 
                  ?"bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                  :"bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active"
              )}
            >
              Todas
            </button>
            {VARIABLE_REGISTRY.map((group) => (
              <button
                key={group.id}
                onClick={() => setActiveGroup(activeGroup === group.id ? null : group.id)}
                className={cn("px-2 py-0.5 rounded-md text-micro font-medium transition-colors",
                  activeGroup === group.id 
                    ?"bg-lia-btn-primary-bg text-lia-btn-primary-text" 
                    :"bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active"
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
              <Variable className="w-8 h-8 mx-auto mb-2 text-lia-text-tertiary" />
              <p className="text-xs text-lia-text-secondary">
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
          <p className="text-micro text-lia-text-secondary text-center">
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
        <Icon className="w-3 h-3 text-lia-text-secondary" />
        <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
          {group.label}
        </span>
      </div>
      <div className="space-y-0.5">
        {group.variables.map((variable) => (
          <button
            key={variable.key}
            onClick={() => onSelect(variable)}
            className="w-full p-2 rounded-xl text-left transition-colors motion-reduce:transition-none group hover:bg-lia-interactive-hover border border-transparent hover:border-lia-border-subtle"
          >
            <div className="flex items-start gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0 group-hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none">
                <code className="text-micro font-mono text-lia-text-secondary">
                  {"{{}}"}
                </code>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <code className="text-micro font-mono px-1.5 py-0.5 rounded-xl bg-lia-bg-tertiary group-hover:bg-lia-interactive-active text-lia-text-secondary">
                    {`{{${variable.key}}}`}
                  </code>
                  <span className="text-xs font-medium text-lia-text-primary truncate">
                    {variable.label}
                  </span>
                  <ChevronRight className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none ml-auto flex-shrink-0" />
                </div>
                <p className="text-micro text-lia-text-secondary line-clamp-1">
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
