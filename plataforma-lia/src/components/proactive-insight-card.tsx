'use client'

import React from 'react'
import { 
  Users, Phone, Mail, Linkedin, MapPin, Briefcase,
  Star, ChevronDown, ChevronUp, 
  TrendingUp, AlertTriangle, Info, CheckCircle,
  Building, GraduationCap, Globe
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

export interface SearchAnalytics {
  summary: {
    total_candidates: number
    local_count: number
    global_count: number
    average_lia_score: number
  }
  contact_quality: {
    with_valid_phone: number
    with_valid_email: number
    with_linkedin: number
    phone_percentage: number
    email_percentage: number
  }
  distributions: {
    seniority: Record<string, number>
    location: Record<string, number>
    work_model: Record<string, number>
  }
  top_skills: Array<{ skill: string; count: number; percentage: number }>
  top_companies: Array<{ company: string; count: number }>
  experience_range: {
    min: number
    max: number
    average: number
    median: number
  }
  alerts: Array<{ type: 'warning' | 'info' | 'success'; message: string }>
  suggested_actions: Array<{
    id: string
    label: string
    icon: string
    description: string
    action_type: string
  }>
  narrative?: string
}

interface ProactiveInsightCardProps {
  analytics: SearchAnalytics
  onAction?: (actionId: string, actionType: string) => void
  isExpanded?: boolean
  className?: string
}


const getAlertIcon = (type: 'warning' | 'info' | 'success') => {
  switch (type) {
    case 'warning':
      return <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
    case 'info':
      return <Info className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
    case 'success':
      return <CheckCircle className="w-3.5 h-3.5 text-green-500" />
  }
}

const getAlertBgColor = (type: 'warning' | 'info' | 'success') => {
  switch (type) {
    case 'warning':
      return 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800'
    case 'info':
 return 'bg-gray-50 border-gray-300 dark:bg-gray-800 dark:border-gray-200'
    case 'success':
      return 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
  }
}

export function ProactiveInsightCard({ 
  analytics, 
  onAction,
  isExpanded: initialExpanded = false,
  className
}: ProactiveInsightCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(initialExpanded)
  
  const { summary, contact_quality, distributions, top_skills, top_companies, experience_range, alerts, narrative } = analytics

  const seniorityEntries = Object.entries(distributions?.seniority || {}).sort((a, b) => b[1] - a[1])
  const locationEntries = Object.entries(distributions?.location || {}).sort((a, b) => b[1] - a[1]).slice(0, 5)
  const workModelEntries = Object.entries(distributions?.work_model || {}).sort((a, b) => b[1] - a[1])

  return (
    <Card className={cn("w-full bg-white dark:bg-gray-900 border border-gray-100", className)}>
      <CardHeader className="pb-2 pt-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className={`${textStyles.title} dark:text-gray-100`}>
                Análise da Busca
              </h3>
              <p className={`${textStyles.bodySmall} dark:text-gray-300`}>
                Insights proativos da LIA
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-600" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-4 pt-0 space-y-3">
        <div className="grid grid-cols-4 gap-2">
          <div className={`${cardStyles.compact} dark:bg-gray-800 text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Users className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-bold text-gray-950 dark:text-gray-50">{summary.total_candidates}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-gray-300`}>Total</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-gray-800 text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Building className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-bold text-gray-950 dark:text-gray-50">{summary.local_count}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-gray-300`}>Base Local</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-gray-800 text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Globe className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-bold text-gray-950 dark:text-gray-50">{summary.global_count}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-gray-300`}>Base Global</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-gray-800 text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Star className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              <span className="text-lg font-bold text-gray-950 dark:text-gray-50">{summary.average_lia_score.toFixed(0)}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-gray-300`}>Score Médio</span>
          </div>
        </div>

        {narrative && (
          <div className={`${cardStyles.flat} p-2.5`}>
            <p className={`${textStyles.body} dark:text-gray-300 leading-relaxed`}>
              {narrative}
            </p>
          </div>
        )}

        {alerts && alerts.length > 0 && (
          <div className="space-y-1.5">
            {alerts.map((alert, index) => (
              <div 
                key={index}
                className={cn(
                  "flex items-start gap-2 p-2 rounded-md border text-xs",
                  getAlertBgColor(alert.type)
                )}
              >
                {getAlertIcon(alert.type)}
                <span className="text-gray-800 dark:text-gray-200 flex-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  {alert.message}
                </span>
              </div>
            ))}
          </div>
        )}


        {isExpanded && (
          <>
            {contact_quality && (
              <div className="space-y-2">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300`}>
                  Qualidade dos Contatos
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Phone className="w-3 h-3 text-green-500" />
                        <span className={`${textStyles.bodySmall} dark:text-gray-400`}>Telefone</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{contact_quality.phone_percentage}%</span>
                    </div>
                    <Progress value={contact_quality.phone_percentage} className="h-1.5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Mail className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                        <span className={`${textStyles.bodySmall} dark:text-gray-400`}>Email</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{contact_quality.email_percentage}%</span>
                    </div>
                    <Progress value={contact_quality.email_percentage} className="h-1.5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Linkedin className="w-3 h-3 text-gray-600" />
                        <span className={`${textStyles.bodySmall} dark:text-gray-400`}>LinkedIn</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>
                        {contact_quality.with_linkedin}
                      </span>
                    </div>
                    <Progress 
                      value={(contact_quality.with_linkedin / summary.total_candidates) * 100} 
                      className="h-1.5" 
                    />
                  </div>
                </div>
              </div>
            )}

            {seniorityEntries.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300`}>
                  Senioridade
                </h4>
                <div className="flex flex-wrap gap-1">
                  {seniorityEntries.map(([level, count]) => (
                    <Badge 
                      key={level} 
                      variant="secondary"
                      className="text-xs py-0.5 px-1.5 bg-gray-100 dark:bg-gray-800"
                    >
                      {level}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {locationEntries.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300 flex items-center gap-1`}>
                  <MapPin className="w-3 h-3" />
                  Localização
                </h4>
                <div className="flex flex-wrap gap-1">
                  {locationEntries.map(([location, count]) => (
                    <Badge 
                      key={location} 
                      variant="outline"
                      className="text-xs py-0.5 px-1.5"
                    >
                      {location}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {workModelEntries.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300 flex items-center gap-1`}>
                  <Briefcase className="w-3 h-3" />
                  Modelo de Trabalho
                </h4>
                <div className="flex flex-wrap gap-1">
                  {workModelEntries.map(([model, count]) => (
                    <Badge 
                      key={model} 
                      variant="outline"
                      className={cn(
                        "text-xs py-0.5 px-1.5",
                        model.toLowerCase().includes('remoto') && "bg-green-50 border-green-200 text-green-700",
                        model.toLowerCase().includes('híbrido') && "bg-gray-50 dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-wedo-cyan-dark",
                        model.toLowerCase().includes('presencial') && "bg-purple-50 border-purple-200 text-purple-700"
                      )}
                    >
                      {model}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {top_skills && top_skills.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300 flex items-center gap-1`}>
                  <GraduationCap className="w-3 h-3" />
                  Top Skills
                </h4>
                <div className="flex flex-wrap gap-1">
                  {top_skills.slice(0, 8).map((skill) => (
                    <Badge 
                      key={skill.skill} 
                      className="text-xs py-0.5 px-1.5 bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200"
                    >
                      {skill.skill} ({skill.count})
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {top_companies && top_companies.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300 flex items-center gap-1`}>
                  <Building className="w-3 h-3" />
                  Principais Empresas
                </h4>
                <div className="flex flex-wrap gap-1">
                  {top_companies.slice(0, 6).map((company) => (
                    <Badge 
                      key={company.company} 
                      variant="secondary"
                      className="text-xs py-0.5 px-1.5"
                    >
                      {company.company} ({company.count})
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {experience_range && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-gray-300`}>
                  Experiência
                </h4>
                <div className={`flex items-center gap-3 ${textStyles.bodySmall}`}>
                  <span className="dark:text-gray-400">
                    Mín: <span className="font-medium text-gray-950 dark:text-gray-50">{experience_range.min} anos</span>
                  </span>
                  <span className="dark:text-gray-400">
                    Máx: <span className="font-medium text-gray-950 dark:text-gray-50">{experience_range.max} anos</span>
                  </span>
                  <span className="dark:text-gray-400">
                    Média: <span className="font-medium text-gray-950 dark:text-gray-50">{experience_range.average.toFixed(1)} anos</span>
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
