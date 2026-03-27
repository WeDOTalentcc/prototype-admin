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
            style={{ fontFamily: 'Open Sans, sans-serif' }}
          >
            <Variable className="h-3.5 w-3.5" />
            Inserir Variável
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0 border rounded-md overflow-hidden z-[10000]" 
        side={side} 
        align={align}
        style={{ 
          backgroundColor: 'white',
          borderColor: 'var(--eleven-border, #e5e7eb)'
        }}
      >
        <div className="p-3 border-b" style={{ borderColor: 'var(--eleven-border, #e5e7eb)' }}>
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-100 dark:bg-gray-800">
                <Variable className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              </div>
              <h3 className="text-xs font-semibold text-gray-900">
                Variáveis Disponíveis
              </h3>
            </div>
            <Badge variant="secondary" className="text-micro px-1.5 py-0.5 bg-gray-100 text-gray-600">
              {totalVariables} variáveis
            </Badge>
          </div>
          
          <div className="relative mb-2.5">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar variável..."
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 focus:outline-none"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            />
          </div>

          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveGroup(null)}
              className={cn(
                "px-2 py-0.5 rounded-md text-micro font-medium transition-all",
                !activeGroup 
                  ? "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              Todas
            </button>
            {VARIABLE_REGISTRY.map((group) => (
              <button
                key={group.id}
                onClick={() => setActiveGroup(activeGroup === group.id ? null : group.id)}
                className={cn(
                  "px-2 py-0.5 rounded-md text-micro font-medium transition-all",
                  activeGroup === group.id 
                    ? "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900" 
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
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
              <Variable className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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

        <div className="p-2 border-t" style={{ borderColor: 'var(--eleven-border, #e5e7eb)' }}>
          <p className="text-micro text-gray-500 text-center" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
        <Icon className="w-3 h-3 text-gray-400" />
        <span className="text-micro font-semibold text-gray-500 uppercase tracking-wide" style={{ fontFamily: 'Open Sans, sans-serif' }}>
          {group.label}
        </span>
      </div>
      <div className="space-y-0.5">
        {group.variables.map((variable) => (
          <button
            key={variable.key}
            onClick={() => onSelect(variable)}
            className="w-full p-2 rounded-md text-left transition-all group hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
          >
            <div className="flex items-start gap-2.5">
              <div className="w-7 h-7 rounded-md bg-gray-100 flex items-center justify-center flex-shrink-0 group-hover:bg-gray-200 dark:group-hover:bg-gray-700 transition-colors">
                <code className="text-micro font-mono text-gray-600 dark:text-gray-400">
                  {"{{}}"}
                </code>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <code className="text-micro font-mono px-1.5 py-0.5 rounded bg-gray-100 group-hover:bg-gray-200 dark:group-hover:bg-gray-700 text-gray-700 dark:text-gray-300">
                    {`{{${variable.key}}}`}
                  </code>
                  <span className="text-xs font-medium text-gray-900 truncate" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    {variable.label}
                  </span>
                  <ChevronRight className="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity ml-auto flex-shrink-0" />
                </div>
                <p className="text-micro text-gray-500 line-clamp-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
