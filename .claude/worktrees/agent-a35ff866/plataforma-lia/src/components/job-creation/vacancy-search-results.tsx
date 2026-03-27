"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { 
  Loader2,
  CheckCircle2,
  Clock,
  User,
  Calendar,
  DollarSign,
  MapPin,
  Briefcase,
  Building2
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export interface VacancySummary {
  id: string
  title: string
  department: string
  manager: string
  hired_candidate?: string
  date_closed: string
  salary_range: { min: number; max: number }
  work_model: string
  status: 'hired' | 'cancelled'
}

export interface VacancySearchResultsProps {
  vacancies: VacancySummary[]
  onSelect: (vacancy: VacancySummary) => void
  isLoading?: boolean
}

const NUMBER_EMOJIS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

const STATUS_CONFIG: Record<'hired' | 'cancelled', {
  icon: React.ElementType
  label: string
  className: string
  bgClassName: string
  borderClassName: string
}> = {
  hired: {
    icon: CheckCircle2,
    label: '✅ Contratado',
    className: 'text-green-600 dark:text-green-400',
    bgClassName: 'bg-green-50 dark:bg-green-950/30',
    borderClassName: 'border-green-200 dark:border-green-800'
  },
  cancelled: {
    icon: Clock,
    label: '⏳ Cancelada',
    className: 'text-amber-600 dark:text-amber-400',
    bgClassName: 'bg-amber-50 dark:bg-amber-950/30',
    borderClassName: 'border-amber-200 dark:border-amber-800'
  }
}

const WORK_MODEL_CONFIG: Record<string, { label: string; className: string }> = {
  'remote': { label: 'Remoto', className: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800' },
  'hybrid': { label: 'Híbrido', className: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-400 dark:border-purple-800' },
  'onsite': { label: 'Presencial', className: 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-700' },
  'presencial': { label: 'Presencial', className: 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-700' },
  'remoto': { label: 'Remoto', className: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800' },
  'híbrido': { label: 'Híbrido', className: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-400 dark:border-purple-800' },
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

function VacancyCard({ 
  vacancy, 
  index, 
  onClick 
}: { 
  vacancy: VacancySummary
  index: number
  onClick: () => void 
}) {
  const statusConfig = STATUS_CONFIG[vacancy.status]
  const workModelConfig = WORK_MODEL_CONFIG[vacancy.work_model.toLowerCase()] || WORK_MODEL_CONFIG['onsite']

  return (
    <div 
      className="p-3 rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all cursor-pointer group"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <span className="text-lg flex-shrink-0">{NUMBER_EMOJIS[index] || `${index + 1}.`}</span>
        
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-gray-800 dark:text-white truncate group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors">
              {vacancy.title}
            </h4>
            <Badge 
              variant="outline" 
              className={cn("text-[9px] h-5 px-1.5 border flex-shrink-0", statusConfig.bgClassName, statusConfig.borderClassName, statusConfig.className)}
            >
              {statusConfig.label}
            </Badge>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Building2 className="h-3 w-3 text-gray-600 dark:text-gray-400" />
              <span className="truncate">{vacancy.department}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <User className="h-3 w-3 text-gray-600 dark:text-gray-400" />
              <span className="truncate">{vacancy.manager}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="h-3 w-3 text-gray-600 dark:text-gray-400" />
              <span>{formatDate(vacancy.date_closed)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign className="h-3 w-3 text-gray-600 dark:text-gray-400" />
              <span>{formatCurrency(vacancy.salary_range.min)} - {formatCurrency(vacancy.salary_range.max)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <Badge 
              variant="outline" 
              className={cn("text-[9px] h-4 px-1.5 border", workModelConfig.className)}
            >
              {workModelConfig.label}
            </Badge>
            {vacancy.hired_candidate && vacancy.status === 'hired' && (
              <span className="text-[10px] text-green-600 dark:text-green-400 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {vacancy.hired_candidate}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function VacancySearchResults({
  vacancies,
  onSelect,
  isLoading = false
}: VacancySearchResultsProps) {
  if (isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-gray-600 dark:text-gray-400" />
            <span className="text-sm text-muted-foreground">Buscando vagas anteriores...</span>
          </div>
        </div>
      </div>
    )
  }

  if (vacancies.length === 0) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-muted-foreground">
            Não encontrei vagas anteriores com esses critérios. Podemos criar uma vaga do zero! Me diga o cargo e vou te ajudar.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 max-w-[90%]">
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 space-y-4">
          <p className="text-xs text-muted-foreground">
            Encontrei <span className="font-semibold text-gray-900 dark:text-gray-50">{vacancies.length}</span> vaga{vacancies.length > 1 ? 's' : ''} que pode{vacancies.length > 1 ? 'm' : ''} servir como base:
          </p>

          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {vacancies.map((vacancy, index) => (
              <VacancyCard 
                key={vacancy.id} 
                vacancy={vacancy} 
                index={index}
                onClick={() => onSelect(vacancy)}
              />
            ))}
          </div>

          <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-muted-foreground italic">
              Digite o número (ex: "1" ou "2") ou parte do título para selecionar uma vaga. 
              Se preferir criar do zero, digite "criar nova".
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VacancySearchResults
