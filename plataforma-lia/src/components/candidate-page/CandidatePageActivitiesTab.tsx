"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Brain, Activity, ChevronDown, List,
  PlusCircle, GitBranch
} from "lucide-react"
import { type LucideIcon } from "lucide-react"

interface ActivityDetail {
  technicalScore?: number
  culturalFit?: number
  experience?: number
  softSkills?: number
  strengths?: string[]
  improvements?: string[]
  weaknesses?: string[]
  recommendation?: string
  notes?: string
  salary?: string
  contractType?: string
  benefits?: string[]
  startDate?: string
  expirationDate?: string
  approvedBy?: string
  testType?: string
  duration?: string
  score?: number
  maxScore?: number
  evaluator?: string
  conversation?: Array<{ sender: string; message: string; time: string }>
  keyPoints?: Record<string, string>
  videoUrl?: string
  thumbnail?: string
  questions?: string[]
  transcription?: string
  aiAnalysis?: Record<string, number>
  culturalFit_score?: number
  leadership?: number
  communication?: number
  overallImpression?: string
  concerns?: string
  suggestedLevel?: string
  suggestedSalary?: string
}

interface ActivityRecord {
  id: string
  type: string
  icon: LucideIcon
  iconColor: string
  title: string
  author: string
  authorRole: string
  date: string
  timestamp: string
  jobId?: string
  jobTitle?: string
  score?: number
  status: string
  statusLabel?: string
  summary: string
  details: ActivityDetail
  platform?: string
  duration?: string
}

interface AIPrediction {
  id: string
  title: string
  probability: number
  timeframe: string
  recommendation: string
  icon: string
  color: string
}

export interface CandidatePageActivitiesTabProps {
  filteredActivities: ActivityRecord[]
  periodFilter: string
  setPeriodFilter: (value: string) => void
  viewMode: 'timeline' | 'list'
  setViewMode: (value: 'timeline' | 'list') => void
  setShowLiaModal: (value: boolean) => void
  activityFilter: string
  setActivityFilter: (value: string) => void
  showAIPredictions: boolean
  setShowAIPredictions: (value: boolean) => void
  aiPredictions: AIPrediction[]
  expandedActivity: string | null
  setExpandedActivity: (value: string | null) => void
  getBgColor: (color: string) => string
}

export function CandidatePageActivitiesTab({
  filteredActivities,
  periodFilter,
  setPeriodFilter,
  viewMode,
  setViewMode,
  setShowLiaModal,
  activityFilter,
  setActivityFilter,
  showAIPredictions,
  setShowAIPredictions,
  aiPredictions,
  expandedActivity,
  setExpandedActivity,
  getBgColor,
}: CandidatePageActivitiesTabProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-lia-text-primary flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Feed de Atividades
              <Badge className="text-xs px-1.5 py-0">{filteredActivities.length}</Badge>
            </h4>
            <div className="flex items-center gap-2">
              <select
                value={periodFilter}
                onChange={(e) => setPeriodFilter(e.target.value)}
                className="text-xs px-2 py-1 bg-white dark:bg-lia-bg-elevated border border-lia-border-subtle dark:border-lia-border-default rounded-md focus:outline-none focus:ring-1 focus:ring-gray-400/20"
              >
                <option value="7days">Últimos 7 dias</option>
                <option value="30days">Últimos 30 dias</option>
                <option value="3months">Últimos 3 meses</option>
                <option value="all">Todo período</option>
              </select>

              <div className="flex items-center bg-white dark:bg-lia-bg-elevated rounded-md p-0.5 border border-lia-border-subtle dark:border-lia-border-default">
                <button
                  onClick={() => setViewMode('timeline')}
                  className={`p-1.5 rounded-md transition-colors ${
 viewMode === 'timeline'
                      ? 'bg-gray-200 text-lia-text-primary dark:text-lia-text-primary'
                      : 'text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
                  }`}
                  title="Visualização Timeline"
                >
                  <GitBranch className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded-md transition-colors ${
 viewMode === 'list'
                      ? 'bg-gray-200 text-lia-text-primary dark:text-lia-text-primary'
                      : 'text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
                  }`}
                  title="Visualização Lista"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>

              <Button
                onClick={() => setShowLiaModal(true)}
                size="sm"
                className="gap-1 text-white px-3 py-1.5 text-xs h-7 bg-status-error hover:bg-status-error/90"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                Nova Atividade
              </Button>
            </div>
          </div>

          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setActivityFilter('all')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'all'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-200'
              }`}
            >
              Todas
            </button>
            <button
              onClick={() => setActivityFilter('emails')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'emails'
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              📧 Emails
            </button>
            <button
              onClick={() => setActivityFilter('interviews')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'interviews'
                  ? 'bg-wedo-purple text-white'
                  : 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple hover:bg-wedo-purple/10'
              }`}
            >
              🎤 Entrevistas
            </button>
            <button
              onClick={() => setActivityFilter('tests')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'tests'
                  ? 'bg-wedo-purple text-white'
                  : 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple hover:bg-wedo-purple'
              }`}
            >
              📝 Testes
            </button>
            <button
              onClick={() => setActivityFilter('lia')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'lia'
                  ? 'bg-status-error text-white'
                  : 'bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error hover:bg-status-error/20'
              }`}
            >
              🤖 LIA
            </button>
            <button
              onClick={() => setActivityFilter('offers')}
              className={`px-2 py-1 text-xs rounded-md transition-colors ${
 activityFilter === 'offers'
                  ? 'bg-status-success text-white'
                  : 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success hover:bg-status-success/20'
              }`}
            >
              💼 Ofertas
            </button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-50 dark:bg-lia-bg-secondary/50">
        <CardHeader
          className="pb-3 cursor-pointer hover:bg-wedo-purple/15/30 dark:hover:bg-wedo-purple/30 transition-colors"
          onClick={() => setShowAIPredictions(!showAIPredictions)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <CardTitle className="text-sm">Previsão de Próximas Etapas - IA</CardTitle>
              <Badge className="text-xs px-1.5 py-0.5 bg-wedo-purple text-white">
                Análise Preditiva
              </Badge>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-wedo-purple transition-transform ${
 showAIPredictions ? 'rotate-180' : ''
              }`}
            />
          </div>
        </CardHeader>

        {showAIPredictions && (
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {aiPredictions.map((prediction) => (
                <div key={prediction.id} className="bg-white dark:bg-lia-bg-secondary rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <span className="text-xl">{prediction.icon}</span>
                    <div className="flex-1">
                      <h5 className="text-xs font-semibold text-lia-text-primary">
                        {prediction.title}
                      </h5>
                      <Badge
                        className="text-xs px-1 py-0 h-4 mt-1"
                        style={{backgroundColor: getBgColor(prediction.color),
                          color: prediction.color}}
                      >
                        {prediction.probability}%
                      </Badge>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                        {prediction.timeframe}
                      </p>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary italic mt-1">
                        💡 {prediction.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      <Card>
        <CardContent className="p-4">
          {viewMode === 'timeline' ? (
            <div className="relative">
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-wedo-green opacity-20"></div>

              <div className="space-y-4">
                {filteredActivities.map((activity) => (
                  <div key={activity.id} className="relative flex items-start">
                    <div
                      className="absolute left-5 w-3 h-3 rounded-full border-2 border-white z-10"
                      style={{backgroundColor: activity.iconColor,
                        marginTop: '6px'}}
                    ></div>

                    <div className="ml-12 flex-1">
                      <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                        <CardContent
                          className="p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                          onClick={() => setExpandedActivity(expandedActivity === activity.id ? null : activity.id)}
                        >
                          <div className="flex items-start gap-3">
                            <div
                              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                              style={{backgroundColor: getBgColor(activity.iconColor)}}
                            >
                              <activity.icon className="w-4 h-4" style={{color: activity.iconColor}} />
                            </div>

                            <div className="flex-1">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h5 className="text-sm font-semibold text-lia-text-primary">
                                    {activity.title}
                                  </h5>
                                  <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                                    {activity.author} • {activity.date}
                                  </p>
                                  <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                                    {activity.summary}
                                  </p>
                                </div>
                                <div className="flex items-center gap-2">
                                  {activity.score && (
                                    <Badge
                                      className="text-xs"
                                      style={{backgroundColor: 'var(--gray-100)',
                                        color: activity.score >= 80 ? 'var(--status-success)' : 'var(--status-warning)'}}
                                    >
                                      {activity.score}%
                                    </Badge>
                                  )}
                                  <ChevronDown
                                    className={`w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary transition-transform ${
 expandedActivity === activity.id ? 'rotate-180' : ''
                                    }`}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>

                        {expandedActivity === activity.id && activity.details && (
                          <CardContent className="pt-0 pb-3 border-t border-lia-border-subtle">
                            {activity.type === 'lia-evaluation' && (
                              <div className="mt-2 space-y-2">
                                <div className="grid grid-cols-2 gap-2">
                                  <div className="bg-gray-50 dark:bg-lia-bg-secondary p-2 rounded-md">
                                    <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Score Técnico</span>
                                    <p className="text-sm font-semibold">{activity.details.technicalScore}%</p>
                                  </div>
                                  <div className="bg-gray-50 dark:bg-lia-bg-secondary p-2 rounded-md">
                                    <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Fit Cultural</span>
                                    <p className="text-sm font-semibold">{activity.details.culturalFit}%</p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {activity.type === 'whatsapp-screening' && activity.details.conversation && (
                              <div className="mt-2 space-y-2">
                                <div className="bg-gray-50 dark:bg-lia-bg-secondary p-2 rounded-md max-h-48 overflow-y-auto">
                                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-2">Conversa via {activity.platform}</p>
                                  <div className="space-y-2">
                                    {activity.details.conversation.map((msg, i: number) => (
                                      <div
                                        key={i}
                                        className={`flex ${msg.sender === 'LIA' ? 'justify-start' : 'justify-end'}`}
                                      >
                                        <div
                                          className={`max-w-[70%] px-3 py-2 rounded-md text-xs ${
 msg.sender === 'LIA'
                                              ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple'
                                              : 'bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary'
                                          }`}
                                        >
                                          <p>{msg.message}</p>
                                          <span className="text-xs opacity-70">{msg.time}</span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}
                          </CardContent>
                        )}
                      </Card>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredActivities.map((activity) => (
                <Card key={activity.id} className="border border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardContent className="p-3">
                    <div className="flex items-start gap-3">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                        style={{backgroundColor: getBgColor(activity.iconColor)}}
                      >
                        <activity.icon className="w-4 h-4" style={{color: activity.iconColor}} />
                      </div>
                      <div className="flex-1">
                        <h5 className="text-sm font-semibold text-lia-text-primary">
                          {activity.title}
                        </h5>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                          {activity.author} • {activity.date}
                        </p>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                          {activity.summary}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
