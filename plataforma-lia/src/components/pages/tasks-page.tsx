"use client"

import React from "react"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import {
  CheckCircle2, Clock, AlertCircle, Calendar, ChevronLeft, ChevronRight,
  Plus, UserPlus, Upload, Search, Share2, Send, FileText, Users, Briefcase,
  TrendingUp, Filter, MoreVertical, Eye, Edit, MessageSquare, Mail,
  Phone, Video, MapPin, DollarSign, Target, Zap, Brain,
  CheckCircle, XCircle, AlertTriangle, Info, ChevronUp, ChevronDown, User,
  Linkedin, Globe, ExternalLink, Copy, Trash2, ArrowUpDown, SlidersHorizontal, X,
  Bell, Play, Download, Paperclip, History, Activity
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ActivityFeed } from "@/components/activity-feed"
import { DailyBriefingCard } from "@/components/daily-briefing-card"

// Camada 1 (hook): Estado e ações centralizadas
import { useTasksCore } from "./use-tasks-core"
// Camada 2 (helpers puros): Formatação e badges
import {
  getTaskPriorityStyle, getAlertSeverityStyle, getPriorityLabel, getSeverityLabel,
  getTaskTypeIcon, getAlertIcon, getAlertStyle, getUrgencyBadge, getConversionRate,
  getConversionStyle, getRequestStatusBadge, getRequestPriorityBadge, getWorkModelLabel
} from "./task-helpers"
import { TaskCard } from "./tasks/TaskCard"
import { ActiveAlertsCard } from "./tasks/ActiveAlertsCard"

interface TasksPageProps {
  onNavigate?: (page: string) => void
}

// Camada 3 (componente com estado): Usa hook da Camada 1
export function TasksPage({ onNavigate }: TasksPageProps = {}) {
  const { state, actions } = useTasksCore(onNavigate)
  const {
    pendingTasks, activeAlerts, tasks, jobsWithAlerts, jobRequests, metrics,
    filteredPendingTasks, filteredAndSortedJobs, filteredAndSortedRequests,
    pendingTaskFilter, showJobFilters, jobSearchTerm, selectedDepartments,
    selectedUrgencies, selectedPublications, jobSortBy, activeJobFiltersCount,
    uniqueDepartments, showRequestFilters, requestSearchTerm, selectedRequestStatus,
    selectedRequestDepartments, requestSortBy, activeRequestFiltersCount,
    uniqueRequestDepartments, selectedActivity, showActivityModal
  } = state
  const {
    setPendingTaskFilter, setShowJobFilters, setJobSearchTerm, setSelectedDepartments,
    setSelectedUrgencies, setSelectedPublications, setJobSortBy, clearJobFilters,
    setShowRequestFilters, setRequestSearchTerm, setSelectedRequestStatus,
    setSelectedRequestDepartments, setRequestSortBy, clearRequestFilters,
    setShowActivityModal, handleConfirmTask, handleRejectTask, handleAlertAction,
    handleLIAAction, handleRequestAction, handleActivityClick
  } = actions

  return (
    <>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <div className="p-2 max-w-full overflow-x-auto">

        {/* Header - Saudação no topo (alinhado com outras páginas) */}
        <div className="flex items-center justify-between mb-1.5">
          <div>
            <h1 className="text-base font-['Open_Sans',sans-serif] font-semibold wedo-text-black mb-0.5 flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-primary" />
              Painel de Controle
            </h1>
            <p className={`${textStyles.bodySmall} wedo-text-gray`}>
              Você tem 30 novos candidatos e 4 vagas abertas.
            </p>
          </div>
          <Button 
            className="gap-1.5 h-7 px-2.5 font-open-sans text-xs"
            onClick={() => {
              if (onNavigate) {
                onNavigate('Chat com LIA')
                setTimeout(() => {
                  window.dispatchEvent(new CustomEvent('lia-new-task'))
                }, 100)
              }
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Tarefa
          </Button>
        </div>

        {/* Daily Briefing Card - Resumo do dia gerado por LIA */}
        <div className="mb-2">
          <DailyBriefingCard 
            onNavigate={onNavigate}
            onActionClick={(action, context) => {
              if (action === 'open_pipeline_chat') {
                if (onNavigate) {
                  onNavigate('Chat com LIA')
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('lia-open-pipeline', { 
                      detail: context 
                    }))
                  }, 100)
                }
              }
            }}
          />
        </div>

        <div className="space-y-2">

            {/* Cards de Status de Tarefas - LINHA HORIZONTAL ULTRA COMPACTA */}
            <div className="flex items-center gap-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary p-2 rounded-md">
              <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                <Briefcase className="w-3 h-3 text-lia-text-primary" />
                <span className="text-sm font-inter font-medium text-lia-text-primary">{metrics.total}</span>
                <span className={`${textStyles.description}`}>Total</span>
              </div>
              <div className="w-px h-6 bg-lia-border-default dark:bg-lia-bg-elevated"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                <CheckCircle2 className="w-3 h-3 text-lia-text-primary font-semibold" />
                <span className="text-sm font-inter font-medium text-lia-text-primary">{metrics.completed}</span>
                <span className={`${textStyles.description}`}>Concluídas</span>
              </div>
              <div className="w-px h-6 bg-lia-border-default dark:bg-lia-bg-elevated"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                <Clock className="w-3 h-3 text-lia-text-primary" />
                <span className="text-sm font-inter font-medium text-lia-text-primary">{metrics.pending}</span>
                <span className={`${textStyles.description}`}>Pendentes</span>
              </div>
              <div className="w-px h-6 bg-lia-border-default dark:bg-lia-bg-elevated"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                <span className="text-sm font-inter font-medium text-lia-text-primary">{metrics.iaTasks}</span>
                <span className={`${textStyles.description}`}>IA</span>
              </div>
            </div>

            {/* Grid 2 colunas: Minhas Tarefas + Alertas Ativos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
              
              {/* Card: Minhas Tarefas */}
              <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-lia-text-primary" />
                      <CardTitle className={`${textStyles.label} font-semibold wedo-text-black`}>Minhas Tarefas</CardTitle>
                      <Badge variant="outline" className="text-xs font-inter">
                        {filteredPendingTasks.length}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 pb-2">
                  <Tabs defaultValue="tarefas" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 h-8 mb-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-0.5">
                      <TabsTrigger value="tarefas" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
                        Tarefas ({filteredPendingTasks.length})
                      </TabsTrigger>
                      <TabsTrigger value="historico" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary dark:data-[state=active]:bg-lia-btn-primary-bg dark:data-[state=active]:text-lia-text-inverse">
                        Histórico
                      </TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="tarefas" className="mt-0">
                      {/* Filtros por tipo */}
                      <div className="flex items-center gap-1.5 mb-3 flex-wrap">
                        <button
                          onClick={() => setPendingTaskFilter('all')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors motion-reduce:transition-none ${
                            pendingTaskFilter === 'all'
                              ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg font-medium'
                              : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse'
                          }`}
                        >
                          Todos ({pendingTasks.length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('feedback')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                            pendingTaskFilter === 'feedback'
                              ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg font-medium'
                              : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse'
                          }`}
                        >
                          <MessageSquare className="w-2.5 h-2.5" />
                          Feedback ({pendingTasks.filter(t => t.type === 'feedback').length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('entrevista')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                            pendingTaskFilter === 'entrevista'
                              ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg font-medium'
                              : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse'
                          }`}
                        >
                          <Calendar className="w-2.5 h-2.5" />
                          Entrevista ({pendingTasks.filter(t => t.type === 'entrevista').length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('sourcing')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors motion-reduce:transition-none flex items-center gap-1 ${
                            pendingTaskFilter === 'sourcing'
                              ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-btn-primary-bg font-medium'
                              : 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse'
                          }`}
                        >
                          <Search className="w-2.5 h-2.5" />
                          Sourcing ({pendingTasks.filter(t => t.type === 'sourcing').length})
                        </button>
                      </div>
                      
                      <div className="max-h-[320px] overflow-y-auto space-y-3">
                        {/* Sessão Manhã */}
                        {(() => {
                          const morningTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() < 12)
                          if (morningTasks.length === 0) return null
                          return (
                            <div>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <div className="w-1.5 h-1.5 rounded-full"></div>
                                <h3 className="text-xs font-open-sans font-semibold text-lia-text-primary">Sessão Manhã</h3>
                                <span className="text-xs font-open-sans text-lia-text-primary">{morningTasks.length} atividades</span>
                              </div>
                              <div className="space-y-1.5">
                                 {morningTasks.map((task) => (
                                   <TaskCard
                                     key={task.id}
                                     task={task}
                                     // @ts-ignore TODO: fix type
                                     onConfirm={handleConfirmTask}
                                     // @ts-ignore TODO: fix type
                                     onReject={handleRejectTask}
                                   />
                                 ))}
                              </div>
                            </div>
                          )
                        })()}
                        
                        {/* Sessão Tarde */}
                        {(() => {
                          const afternoonTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() >= 12)
                          if (afternoonTasks.length === 0) return null
                          return (
                            <div>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <div className="w-1.5 h-1.5 rounded-full"></div>
                                <h3 className="text-xs font-open-sans font-semibold text-lia-text-primary">Sessão Tarde</h3>
                                <span className="text-xs font-open-sans text-lia-text-primary">{afternoonTasks.length} atividades</span>
                              </div>
                              <div className="space-y-1.5">
                                 {afternoonTasks.map((task) => (
                                   <TaskCard
                                     key={task.id}
                                     task={task}
                                     // @ts-ignore TODO: fix type
                                     onConfirm={handleConfirmTask}
                                     // @ts-ignore TODO: fix type
                                     onReject={handleRejectTask}
                                   />
                                 ))}
                        
                               </div>
                             </div>
                           )
                         })()}

                        {filteredPendingTasks.length === 0 && (
                          <div className="text-center py-8">
                            <CheckCircle2 className="w-12 h-12 mx-auto text-lia-text-disabled mb-3" />
                            <p className="text-sm font-medium text-lia-text-primary mb-1">Nenhuma tarefa pendente</p>
                            <p className="text-xs text-lia-text-secondary">Todas as tarefas foram concluídas</p>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="historico" className="mt-0">
                      <ActivityFeed limit={15} className="max-h-content-lg overflow-y-auto" />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>


              {/* Card: Alertas Ativos */}
              <ActiveAlertsCard
                activeAlerts={activeAlerts}
                // @ts-ignore TODO: fix type
                onAlertAction={handleAlertAction}
                textStyles={textStyles}
              />
            </div>

            {/* Tabela de Vagas Ativas - COM BUSCA E FILTROS */}
            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-open-sans font-semibold wedo-text-black">Minhas Vagas Ativas</CardTitle>
                  <div className="flex items-center gap-2">
                    {/* Contador de resultados */}
                    <Badge variant="outline" className="text-xs font-inter">
                      {filteredAndSortedJobs.length} vaga{filteredAndSortedJobs.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                </div>

                {/* Barra de Busca e Filtros */}
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    {/* Input de Busca */}
                    <div className="flex-1 relative">
                      <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-tertiary" />
                      <Input
                        placeholder="Buscar vagas por título, ID, gestor ou departamento..."
                        value={jobSearchTerm}
                        onChange={(e) => setJobSearchTerm(e.target.value)}
                        className="pl-8 h-8 text-xs"
                      />
                      {jobSearchTerm && (
                        <button
                          onClick={() => setJobSearchTerm("")}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                          aria-label="Limpar busca"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </div>

                    {/* Botão de Filtros */}
                    <Button
                      // @ts-ignore TODO: fix type
                      variant={showJobFilters || activeJobFiltersCount > 0 ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowJobFilters(!showJobFilters)}
                      className="gap-1.5 h-8 px-3 text-xs"
                    >
                      <SlidersHorizontal className="w-3.5 h-3.5" />
                      Filtros
                      {activeJobFiltersCount > 0 && (
                        <Badge className="ml-1 bg-lia-bg-primary text-lia-text-primary dark:bg-lia-bg-secondary text-xs h-4 px-1 font-semibold">
                          {activeJobFiltersCount}
                        </Badge>
                      )}
                    </Button>

                    {/* Dropdown de Ordenação */}
                    <div className="relative group">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 h-8 px-3 text-xs"
                      >
                        <ArrowUpDown className="w-3.5 h-3.5" />
                        Ordenar
                      </Button>

                      {/* Menu de Ordenação */}
                      <div className="absolute right-0 top-full mt-1 w-40 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity motion-reduce:transition-none duration-200 z-10">
                        <div className="py-1">
                          <button
                            onClick={() => setJobSortBy('urgency')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse ${
                              jobSortBy === 'urgency' ? 'bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' : ''
                            }`}
                          >
                            Por Urgência
                          </button>
                          <button
                            onClick={() => setJobSortBy('daysOpen')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse ${
                              jobSortBy === 'daysOpen' ? 'bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' : ''
                            }`}
                          >
                            Por Dias em Aberto
                          </button>
                          <button
                            onClick={() => setJobSortBy('candidates')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse ${
                              jobSortBy === 'candidates' ? 'bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' : ''
                            }`}
                          >
                            Por Nº Candidatos
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Painel de Filtros Expandido */}
                  {showJobFilters && (
                    <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md p-3 space-y-3 border border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-open-sans font-semibold text-lia-text-primary">Filtros Avançados</span>
                        {activeJobFiltersCount > 0 && (
                          <button
                            onClick={clearJobFilters}
                            className="text-xs text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse flex items-center gap-1 "
                          >
                            <X className="w-3 h-3" />
                            Limpar filtros
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        {/* Filtro por Departamento */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">
                            Departamento
                          </label>
                          <div className="space-y-1">
                            {uniqueDepartments.map(dept => (
                              <label key={dept} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedDepartments.includes(dept)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedDepartments([...selectedDepartments, dept])
                                    } else {
                                      setSelectedDepartments(selectedDepartments.filter(d => d !== dept))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-lia-border-default accent-lia-btn-primary-bg focus:ring-2 focus:ring-lia-btn-primary-bg/20"
                                />
                                <span className="text-xs text-lia-text-primary">{dept}</span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Filtro por Urgência */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">
                            Urgência
                          </label>
                          <div className="space-y-1">
                            {['critical', 'urgent', 'normal'].map(urgency => (
                              <label key={urgency} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedUrgencies.includes(urgency)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedUrgencies([...selectedUrgencies, urgency])
                                    } else {
                                      setSelectedUrgencies(selectedUrgencies.filter(u => u !== urgency))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-lia-border-default accent-lia-btn-primary-bg focus:ring-2 focus:ring-lia-btn-primary-bg/20"
                                />
                                <span className="text-xs text-lia-text-primary capitalize">
                                  {urgency === 'critical' ? 'Crítico' : urgency === 'urgent' ? 'Urgente' : 'Normal'}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Filtro por Publicação */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">
                            Publicado em
                          </label>
                          <div className="space-y-1">
                            {[
                              { id: 'linkedin', label: 'LinkedIn' },
                              { id: 'site', label: 'Site' },
                              { id: 'indeed', label: 'Indeed' }
                            ].map(pub => (
                              <label key={pub.id} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedPublications.includes(pub.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedPublications([...selectedPublications, pub.id])
                                    } else {
                                      setSelectedPublications(selectedPublications.filter(p => p !== pub.id))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-lia-border-default accent-lia-btn-primary-bg focus:ring-2 focus:ring-lia-btn-primary-bg/20"
                                />
                                <span className="text-xs text-lia-text-primary">{pub.label}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Filtros Ativos (Tags) */}
                  {activeJobFiltersCount > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-lia-text-primary">Filtros ativos:</span>
                      {selectedDepartments.map(dept => (
                        <Badge
                          key={dept}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {dept}
                          <button
                            onClick={() => setSelectedDepartments(selectedDepartments.filter(d => d !== dept))}
                            className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                      {selectedUrgencies.map(urgency => (
                        <Badge
                          key={urgency}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {urgency === 'critical' ? 'Crítico' : urgency === 'urgent' ? 'Urgente' : 'Normal'}
                          <button
                            onClick={() => setSelectedUrgencies(selectedUrgencies.filter(u => u !== urgency))}
                            className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                      {selectedPublications.map(pub => (
                        <Badge
                          key={pub}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {pub === 'linkedin' ? 'LinkedIn' : pub === 'site' ? 'Site' : 'Indeed'}
                          <button
                            onClick={() => setSelectedPublications(selectedPublications.filter(p => p !== pub))}
                            className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                {/* Mensagem de resultados vazios */}
                {filteredAndSortedJobs.length === 0 ? (
                  <div className="text-center py-8">
                    <Search className="w-16 h-16 mx-auto text-lia-text-disabled mb-4" />
                    <p className="text-base font-medium text-lia-text-primary mb-1">Nenhuma vaga encontrada</p>
                    <p className="text-sm text-lia-text-secondary">
                      Tente ajustar os filtros ou buscar por outros termos
                    </p>
                    {activeJobFiltersCount > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={clearJobFilters}
                        className="mt-3 text-xs"
                      >
                        Limpar filtros
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredAndSortedJobs.map((job) => (
                      <div key={job.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3 hover:border-lia-border-medium hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:scale-[1.01] transition-[color,background-color,border-color,transform] duration-200 bg-lia-bg-primary dark:bg-lia-bg-primary cursor-pointer">
                        {/* Header da Vaga - Compacto com publicação inline */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 space-y-1">
                            {/* Linha 1: Título + Badges + Publicação */}
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-semibold text-sm text-lia-text-primary">{job.title}</h3>
                              <Badge variant="outline" className="text-xs">{job.jobId}</Badge>
                              {getUrgencyBadge(job.urgencyLevel, job.daysOpen)}
                              {job.publishedLinkedIn && (
                                <Badge className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-subtle text-xs flex items-center gap-1 font-medium">
                                  <Linkedin className="w-2.5 h-2.5" />
                                  LI
                                </Badge>
                              )}
                              {job.publishedWebsite && (
                                <Badge className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-subtle text-xs flex items-center gap-1 font-medium">
                                  <Globe className="w-2.5 h-2.5" />
                                  Site
                                </Badge>
                              )}
                              {job.publishedIndeed && (
                                <Badge className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-subtle text-xs flex items-center gap-1 font-medium">
                                  <Briefcase className="w-2.5 h-2.5" />
                                  Indeed
                                </Badge>
                              )}
                            </div>
                            {/* Linha 2: Informações inline compactas */}
                            <div className="flex items-center gap-3 text-xs text-lia-text-primary flex-wrap">
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                <span className={`font-medium ${""}`}>{job.daysOpen}d</span>
                              </div>
                              <span className="text-lia-text-tertiary">•</span>
                              <div className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                <span>{job.manager.split(' ')[0]}</span>
                              </div>
                              <span className="text-lia-text-tertiary">•</span>
                              <div className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                <span>{job.department}</span>
                              </div>
                              <span className="text-lia-text-tertiary">•</span>
                              <div className="flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                <span>{job.totalCandidates} candidatos</span>
                              </div>
                            </div>
                          </div>
                          {/* Menu Dropdown de Ações Rápidas - Integrado com LIA */}
                          <div className="relative group">
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Ações da vaga">
                              <MoreVertical className="w-3.5 h-3.5" />
                            </Button>
                            {/* Dropdown Menu */}
                            <div className="absolute right-0 top-full mt-1 w-48 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity motion-reduce:transition-none duration-200 z-10">
                              <div className="py-1">
                                <button
                                  onClick={() => handleLIAAction('kanban', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <Eye className="w-3 h-3" />
                                  Ver Kanban Completo
                                </button>
                                <button
                                  onClick={() => handleLIAAction('report', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <FileText className="w-3 h-3" />
                                  Gerar Relatório
                                </button>
                                <button
                                  onClick={() => handleLIAAction('share', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <Share2 className="w-3 h-3" />
                                  Compartilhar Vaga
                                </button>
                                <button
                                  onClick={() => handleLIAAction('edit', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <Edit className="w-3 h-3" />
                                  Editar Requisitos
                                </button>
                                <button
                                  onClick={() => handleLIAAction('duplicate', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <Copy className="w-3 h-3" />
                                  Duplicar Vaga
                                </button>
                                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle my-1"></div>
                                <button
                                  onClick={() => handleLIAAction('cancel', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-status-error/10 dark:hover:bg-status-error/20 text-status-error hover:text-status-error dark:hover:text-status-error transition-colors motion-reduce:transition-none flex items-center gap-2"
                                >
                                  <Trash2 className="w-3 h-3" />
                                  Cancelar Vaga
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Funil Horizontal Unificado - Ultra Compacto */}
                        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md p-1.5 mb-1.5">
                          <div className="flex items-center justify-between gap-1">
                            {/* Novos */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.new}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Novos</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.new, job.stages.uncontacted)}`}>
                                {getConversionRate(job.stages.new, job.stages.uncontacted)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Não Contactados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.uncontacted}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Triag</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.uncontacted, job.stages.contacted)}`}>
                                {getConversionRate(job.stages.uncontacted, job.stages.contacted)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Contactados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.contacted}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Cont</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.contacted, job.stages.replied)}`}>
                                {getConversionRate(job.stages.contacted, job.stages.replied)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Respondidos */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.replied}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Resp</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.replied, job.stages.phoneScreen)}`}>
                                {getConversionRate(job.stages.replied, job.stages.phoneScreen)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Telefone */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.phoneScreen}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Tel</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.phoneScreen, job.stages.onsite)}`}>
                                {getConversionRate(job.stages.phoneScreen, job.stages.onsite)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Entrevista */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.onsite}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Entrev</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.onsite, job.stages.makeOffer)}`}>
                                {getConversionRate(job.stages.onsite, job.stages.makeOffer)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Oferta */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.makeOffer}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Ofert</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionRate(job.stages.makeOffer, job.stages.hired)}`}>
                                {getConversionRate(job.stages.makeOffer, job.stages.hired)}%
                              </span>
                              <span className="text-xs text-lia-text-primary">→</span>
                            </div>

                            {/* Contratados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-lia-text-primary">{job.stages.hired}</span>
                              <span className="text-xs text-lia-text-primary uppercase">Contr</span>
                            </div>
                          </div>
                        </div>

                        {/* Pendências e Alerta em Linha - Ultra Compacto */}
                        <div className="flex items-center gap-1.5">
                          {/* Pendências LIA */}
                          {job.liaPendencies.length > 0 && (
                            <div className="flex items-center gap-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-subtle rounded-md px-1.5 py-1 flex-1">
                              <Brain className="w-2.5 h-2.5 text-wedo-cyan flex-shrink-0" />
                              <span className="text-xs text-lia-text-primary truncate font-medium">
                                {job.liaPendencies.length} pendência{job.liaPendencies.length > 1 ? 's' : ''}
                              </span>
                            </div>
                          )}

                          {/* Alerta LIA */}
                          <div 
                            // @ts-ignore TODO: fix type
                            className={`flex items-center gap-1 ${getAlertColor(job.alert.type)} rounded-md px-1.5 py-1 flex-1`}
                            // @ts-ignore TODO: fix type
                            style={getAlertStyle(job.alert.type)}
                          >
                            {getAlertIcon(job.alert.type)}
                            <span className="text-xs font-medium truncate flex-1">{job.alert.message}</span>
                            <Button
                              size="sm"
                              className="gap-0.5 h-4 text-xs px-1 hover:scale-105 transition-transform motion-reduce:transition-none flex-shrink-0"
                              onClick={() => {
                                const actionPrompt = `${job.alert.action} para a vaga ${job.title} (${job.jobId})`
                                if (typeof window !== 'undefined') {
                                  localStorage.setItem('liaPrompt', actionPrompt)
                                }
                                if (onNavigate) {
                                  onNavigate('Chat com LIA')
                                }
                              }}
                            >
                              {job.alert.action}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

        </div>
      </div>
    </div>
    </>
  )
}
