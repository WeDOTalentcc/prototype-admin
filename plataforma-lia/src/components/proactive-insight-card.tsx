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
      return <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
    case 'info':
      return <Info className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
    case 'success':
      return <CheckCircle className="w-3.5 h-3.5 text-status-success" />
  }
}

const getAlertBgColor = (type: 'warning' | 'info' | 'success') => {
  switch (type) {
    case 'warning':
      return 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/20 dark:border-status-warning/30'
    case 'info':
 return 'bg-gray-50 border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    case 'success':
      return 'bg-status-success/10 border-status-success/30 dark:bg-status-success/20 dark:border-status-success/30'
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
    <Card className={cn("w-full bg-white dark:bg-lia-bg-primary border border-lia-border-subtle", className)}>
      <CardHeader className="pb-2 pt-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h3 className={`${textStyles.title} dark:text-lia-text-primary`}>
                Análise da Busca
              </h3>
              <p className={`${textStyles.bodySmall} dark:text-lia-text-secondary`}>
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
              <ChevronUp className="w-4 h-4 lia-text-base" />
            ) : (
              <ChevronDown className="w-4 h-4 lia-text-base" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-4 pt-0 space-y-3">
        <div className="grid grid-cols-4 gap-2">
          <div className={`${cardStyles.compact} dark:bg-lia-bg-secondary text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Users className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
              <span className="text-lg font-bold text-gray-950">{summary.total_candidates}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-lia-text-secondary`}>Total</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-lia-bg-secondary text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Building className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
              <span className="text-lg font-bold text-gray-950">{summary.local_count}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-lia-text-secondary`}>Base Local</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-lia-bg-secondary text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Globe className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
              <span className="text-lg font-bold text-gray-950">{summary.global_count}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-lia-text-secondary`}>Base Global</span>
          </div>
          <div className={`${cardStyles.compact} dark:bg-lia-bg-secondary text-center`}>
            <div className="flex items-center justify-center gap-1 mb-0.5">
              <Star className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
              <span className="text-lg font-bold text-gray-950">{summary.average_lia_score.toFixed(0)}</span>
            </div>
            <span className={`${textStyles.bodySmall} dark:text-lia-text-secondary`}>Score Médio</span>
          </div>
        </div>

        {narrative && (
          <div className={`${cardStyles.flat} p-2.5`}>
            <p className={`${textStyles.body} dark:text-lia-text-secondary leading-relaxed`}>
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
                <span className="text-gray-800 dark:text-lia-text-primary flex-1">
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
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary`}>
                  Qualidade dos Contatos
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Phone className="w-3 h-3 text-status-success" />
                        <span className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Telefone</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950`}>{contact_quality.phone_percentage}%</span>
                    </div>
                    <Progress value={contact_quality.phone_percentage} className="h-1.5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Mail className="w-3 h-3 text-gray-600 dark:text-lia-text-tertiary" />
                        <span className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Email</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950`}>{contact_quality.email_percentage}%</span>
                    </div>
                    <Progress value={contact_quality.email_percentage} className="h-1.5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Linkedin className="w-3 h-3 lia-text-base" />
                        <span className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>LinkedIn</span>
                      </div>
                      <span className={`${textStyles.label} text-gray-950`}>
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
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary`}>
                  Senioridade
                </h4>
                <div className="flex flex-wrap gap-1">
                  {seniorityEntries.map(([level, count]) => (
                    <Badge 
                      key={level} 
                      variant="secondary"
                      className="text-xs py-0.5 px-1.5 bg-gray-100 dark:bg-lia-bg-secondary"
                    >
                      {level}: {count}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {locationEntries.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary flex items-center gap-1`}>
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
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary flex items-center gap-1`}>
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
                        model.toLowerCase().includes('remoto') && "bg-status-success/10 border-status-success/30 text-status-success",
                        model.toLowerCase().includes('híbrido') && "bg-gray-50 dark:bg-lia-bg-primary border-lia-border-default dark:border-lia-border-default text-wedo-cyan-dark",
                        model.toLowerCase().includes('presencial') && "bg-wedo-purple/10 border-wedo-purple/30 text-wedo-purple"
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
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary flex items-center gap-1`}>
                  <GraduationCap className="w-3 h-3" />
                  Top Skills
                </h4>
                <div className="flex flex-wrap gap-1">
                  {top_skills.slice(0, 8).map((skill) => (
                    <Badge 
                      key={skill.skill} 
                      className="text-xs py-0.5 px-1.5 bg-gray-100 lia-text-strong border-lia-border-subtle hover:bg-gray-200"
                    >
                      {skill.skill} ({skill.count})
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {top_companies && top_companies.length > 0 && (
              <div className="space-y-1.5">
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary flex items-center gap-1`}>
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
                <h4 className={`${textStyles.label} uppercase tracking-wider dark:text-lia-text-secondary`}>
                  Experiência
                </h4>
                <div className={`flex items-center gap-3 ${textStyles.bodySmall}`}>
                  <span className="dark:text-lia-text-tertiary">
                    Mín: <span className="font-medium text-gray-950">{experience_range.min} anos</span>
                  </span>
                  <span className="dark:text-lia-text-tertiary">
                    Máx: <span className="font-medium text-gray-950">{experience_range.max} anos</span>
                  </span>
                  <span className="dark:text-lia-text-tertiary">
                    Média: <span className="font-medium text-gray-950">{experience_range.average.toFixed(1)} anos</span>
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
