"use client"


import React, { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { 
  ArrowLeft, MapPin, Briefcase, Mail, Phone, Linkedin, ExternalLink,
  Calendar, GraduationCap, Loader2, Building, Globe, Github, Star,
  MessageSquare, UserPlus, Heart, EyeOff, DollarSign, Clock, Users,
  Code, Award, CheckCircle, AlertCircle, Brain, Languages,
  Home, Shield, FileText, Activity, List, Send, CalendarDays, Plus,
  GitBranch, Upload, Download, Eye, X, Tag, ChevronDown, ChevronUp,
  PlusCircle, BarChart3, Target, TrendingUp, Image, File, FileVideo, Video, Play,
  Edit, User, Cake, Contact, Lightbulb, Car, Network, ClipboardCheck, Copy
} from "lucide-react"
import { liaApi, type CandidateLocal } from "@/services/lia-api"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { useToast } from "@/hooks/use-toast"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import dynamic from "next/dynamic"

const LiaAnalysisModal = dynamic(() => import("@/components/modals/lia-analysis-modal").then(m => ({ default: m.LiaAnalysisModal })), { ssr: false })

type ActiveTab = 'profile' | 'activities' | 'files' | 'opinions'
type ActivityCategory = 'all' | 'interview' | 'screening' | 'general'

import { useCandidatePageCore } from "./useCandidatePageCore"

import { CandidateProfileTab } from "./CandidateProfileTab"
export default function CandidateProfilePage() {
  const {
    activeTab,
    activities,
    activityFilter,
    activityView,
    calculateAge,
    candidate,
    candidateFiles,
    cleanMarkdown,
    communicationType,
    copyToClipboard,
    education,
    error,
    expandedAnalysisId,
    expandedOpinionId,
    experiences,
    fetchSavedAnalyses,
    fileCategories,
    formatCurrency,
    formatDate,
    formatDateShort,
    formatFileSize,
    formatRelativeTime,
    getCategoryColor,
    getCategoryLabel,
    getFileIcon,
    getInitials,
    getLanguageLevel,
    getShortId,
    handleDeleteFile,
    handleDownloadFile,
    handleFileUpload,
    handleHideCandidate,
    handleToggleFavorite,
    hasDocuments,
    hasPearchData,
    hasPersonalData,
    isDragging,
    isFavorite,
    isHidden,
    isLoadingActivities,
    isLoadingAnalyses,
    isLoadingFiles,
    isLoadingOpinions,
    isUploading,
    languagesData,
    loading,
    newNoteCategory,
    newNoteContent,
    openCommunicationModal,
    opinion,
    opinionsHistory,
    opinionsSubTab,
    periodFilter,
    router,
    savedAnalyses,
    selectedCategory,
    setActiveTab,
    setActivities,
    setActivityFilter,
    setActivityView,
    setExpandedAnalysisId,
    setExpandedOpinionId,
    setIsDragging,
    setNewNoteCategory,
    setNewNoteContent,
    setOpinionsSubTab,
    setPeriodFilter,
    setSelectedCategory,
    setShowAddToListModal,
    setShowAddToVacancyModal,
    setShowCommunicationModal,
    setShowLiaAnalysisModal,
    showAddToListModal,
    showAddToVacancyModal,
    showCommunicationModal,
    showLiaAnalysisModal,
    skillCategories,
    toast,
    uploadProgress
  } = useCandidatePageCore()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400 mx-auto mb-3" />
          <p className="text-sm text-gray-600 dark:text-gray-400">Carregando perfil...</p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <p className="text-sm text-status-error mb-4">{error || "Candidato não encontrado"}</p>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
        </div>
      </div>
    )
  }


  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>

          {/* HEADER */}
          <Card className="mb-4 border-gray-100">
            <CardContent className="py-5 px-6">
              <div className="flex items-start gap-5">
                <Avatar className="h-20 w-20 border-2 border-gray-100">
                  {candidate.avatar_url && <AvatarImage src={candidate.avatar_url} alt={candidate.name} />}
                  <AvatarFallback className="bg-gray-100 text-gray-600 text-xl font-semibold">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                    <h1 className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                      {candidate.name}
                    </h1>
                    <span className="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-0.5 rounded-md">
                      {getShortId(candidate.id)}
                    </span>
                    
                    {candidate.seniority_level && (
                      <Badge className={badgeStyles.primary}>{candidate.seniority_level}</Badge>
                    )}
                    {candidate.years_of_experience && (
                      <Badge variant="outline" className="text-xs">{candidate.years_of_experience} anos exp.</Badge>
                    )}
                    {candidate.communication_consent && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                            <Shield className="w-3 h-3 mr-1" />
                            LGPD
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>Consentimento LGPD obtido</TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.is_blacklisted && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className="text-xs bg-status-error/10 text-status-error border-status-error/30">⚠️ LCNU</Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="font-medium">Lista de Candidatos Não Utilizáveis</p>
                          {candidate.blacklist_reason && <p className="text-xs">{candidate.blacklist_reason}</p>}
                        </TooltipContent>
                      </Tooltip>
                    )}
                    
                    {/* Tags: Tech & Potencial */}
                    {candidate.is_tech && (
                      <Badge variant="outline" className="text-xs bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600">
                        Tech
                      </Badge>
                    )}
                    {candidate.is_potential && (
                      <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                        Potencial
                      </Badge>
                    )}
                    
                    {/* Status do Candidato */}
                    {(() => {
                      const status = candidate.candidate_status || 'active'
                      const statusConfig: Record<string, { label: string, bg: string, text: string, border: string }> = {
                        'active': { label: 'Ativo', bg: 'bg-status-success/10', text: 'text-status-success', border: 'border-status-success/30' },
                        'do_not_use': { label: 'Não Utilizar', bg: 'bg-status-error/10', text: 'text-status-error', border: 'border-status-error/30' },
                        'hired': { label: 'Contratado', bg: 'bg-gray-50 dark:bg-gray-900', text: 'text-gray-900 dark:text-gray-50', border: 'border-gray-300 dark:border-gray-600' },
                        'inactive': { label: 'Inativo', bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' }
                      }
                      const config = statusConfig[status] || statusConfig['active']
                      return (
                        <Badge className={`text-xs ${config.bg} ${config.text} ${config.border}`}>
                          {config.label}
                        </Badge>
                      )
                    })()}
                    
                    {/* Ícone Cérebro LIA - Análises */}
                    <LiaAnalysisModal
                      isOpen={showLiaAnalysisModal}
                      onClose={() => setShowLiaAnalysisModal(false)}
                      onOpen={() => setShowLiaAnalysisModal(true)}
                      candidate={candidate}
                      onTransportToOpinions={() => {
                        fetchSavedAnalyses()
                      }}
                    >
                      <button 
                        className="p-1.5 rounded-full hover:bg-gray-100 dark:bg-gray-800 transition-colors"
                        title="Análise LIA do Perfil"
                      >
                        <Brain className="w-5 h-5 text-wedo-cyan" />
                      </button>
                    </LiaAnalysisModal>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200 mb-1">
                    {candidate.current_title && (
                      <>
                        <Briefcase className="w-4 h-4 text-gray-400" />
                        <span className="font-medium">{candidate.current_title}</span>
                      </>
                    )}
                    {candidate.current_company && (
                      <>
                        <span className="text-gray-400">•</span>
                        <Building className="w-4 h-4 text-gray-400" />
                        <span>{candidate.current_company}</span>
                      </>
                    )}
                  </div>

                  {(candidate.location_city || candidate.location_state) && (
                    <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-3">
                      <MapPin className="w-4 h-4" />
                      <span>
                        {[candidate.location_city, candidate.location_state, candidate.location_country]
                          .filter(Boolean).join(', ')}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center gap-4 flex-wrap">
                    {candidate.email && (
                      <a href={`mailto:${candidate.email}`} className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                        <Mail className="w-4 h-4" />
                        {candidate.email}
                      </a>
                    )}
                    {(candidate.phone || candidate.mobile_phone) && (
                      <a href={`tel:${candidate.mobile_phone || candidate.phone}`} className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
                        <Phone className="w-4 h-4" />
                        {candidate.mobile_phone || candidate.phone}
                      </a>
                    )}
                    {/* Social Icons - Always visible */}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.linkedin_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.linkedin_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.linkedin_url && e.preventDefault()}
                        >
                          <Linkedin className="w-5 h-5" style={{color: candidate.linkedin_url ? '#0A66C2' : 'var(--gray-400)'}} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>LinkedIn</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.github_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.github_url ? 'hover:bg-gray-100' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.github_url && e.preventDefault()}
                        >
                          <Github className="w-5 h-5" style={{color: candidate.github_url ? '#181717' : 'var(--gray-400)'}} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>GitHub</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.stackoverflow_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.stackoverflow_url ? 'hover:bg-wedo-orange/10' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.stackoverflow_url && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={candidate.stackoverflow_url ? '#F48024' : 'var(--gray-400)'}><path d="M15 21H3v-8h2v6h10v-6h2v8z"/><path d="M5 15h10v-2H5v2zm0-3.5h10v-2H5v2zm.05-3.45l9.85 2.05.4-1.95L5.45 6l-.4 1.95zM7.15 4.55l8.95 4.55.85-1.7L8 2.85l-.85 1.7z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>StackOverflow</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.twitter_url || candidate.x_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${(candidate.twitter_url || candidate.x_url) ? 'hover:bg-gray-100' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !(candidate.twitter_url || candidate.x_url) && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={(candidate.twitter_url || candidate.x_url) ? '#000000' : 'var(--gray-400)'}><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>X / Twitter</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.behance_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.behance_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.behance_url && e.preventDefault()}
                        >
                          <svg className="w-5 h-5" viewBox="0 0 24 24" fill={candidate.behance_url ? '#1769FF' : 'var(--gray-400)'}><path d="M7.5 11c1.5 0 2.5-.8 2.5-2.2S9 6.5 7.5 6.5H4v4.5h3.5zm.5 1H4v5h4c1.8 0 3-1.1 3-2.5S9.8 12 8 12zm8.5-1c-1.5 0-2.5.8-2.5 2h5c0-1.2-1-2-2.5-2z"/><path d="M22.5 6H14v1.5h8.5V6zm-.5 5c0-2.5-2-4.5-4.5-4.5S13 8.5 13 11s2 4.5 4.5 4.5c1.5 0 3-.8 3.8-2h-1.8c-.5.6-1.2 1-2 1-1.5 0-2.5-1-2.5-2.5h6.5v-.5c0-.2 0-.3-.5-.5z"/></svg>
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>Behance</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a 
                          href={candidate.portfolio_url || '#'} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`p-1.5 rounded-md transition-colors ${candidate.portfolio_url ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : 'opacity-30 cursor-default'}`}
                          onClick={(e) => !candidate.portfolio_url && e.preventDefault()}
                        >
                          <Globe className="w-5 h-5" style={{color: candidate.portfolio_url ? 'var(--gray-950)' : 'var(--gray-400)'}} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>Portfolio</TooltipContent>
                    </Tooltip>
                  </div>

                </div>

                {/* RIGHT SIDE COLUMN - Extended Info */}
                <div className="text-right space-y-3 min-w-sidebar-content">
                  {/* Work Preferences (Híbrido, CLT, etc) */}
                  <div className="flex flex-wrap gap-1.5 justify-end">
                    {candidate.work_model && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {candidate.work_model}
                      </Badge>
                    )}
                    {candidate.work_mode && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {candidate.work_mode}
                      </Badge>
                    )}
                    {candidate.contract_type && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {candidate.contract_type}
                      </Badge>
                    )}
                    {candidate.is_remote && (
                      <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600">
                        🌐 Remoto
                      </Badge>
                    )}
                    {candidate.willing_to_relocate && (
                      <Badge variant="outline" className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                        ✈️ Aceita Mudança
                      </Badge>
                    )}
                    {candidate.mobility && (
                      <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                        🚗 Mobilidade
                      </Badge>
                    )}
                    {candidate.availability && (
                      <Badge variant="outline" className="text-xs bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200">
                        {candidate.availability}
                      </Badge>
                    )}
                  </div>
                  
                  {/* Dates Section */}
                  <div className="text-xs text-gray-500 space-y-0.5">
                    <p className="font-medium text-gray-800 dark:text-gray-200">Datas</p>
                    {candidate.updated_at && (
                      <p>Atualizado: {formatDate(candidate.updated_at)}</p>
                    )}
                    {candidate.last_contact_at && (
                      <p>Último contato: {formatDate(candidate.last_contact_at)}</p>
                    )}
                    {candidate.last_activity_at && (
                      <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>
                    )}
                    {!candidate.updated_at && !candidate.last_contact_at && !candidate.last_activity_at && candidate.created_at && (
                      <p>Cadastro: {formatDate(candidate.created_at)}</p>
                    )}
                  </div>
                  
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ACTION BAR - Ícones coloridos como no CandidatePreview */}
          <Card className="mb-4 border-gray-100">
            <CardContent className="py-3 px-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('email')} className="gap-1.5">
                      <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      Email
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Email</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('whatsapp')} className="gap-1.5">
                      <MessageSquare className="w-4 h-4 text-status-success" />
                      WhatsApp
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar WhatsApp</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('agendamento')} className="gap-1.5">
                      <CalendarDays className="w-4 h-4 text-wedo-orange" />
                      Agendar Entrevista
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Agendar Entrevista</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('triagem')} className="gap-1.5">
                      <ClipboardCheck className="w-4 h-4 text-wedo-purple" />
                      Triagem WSI
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Triagem WSI</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => setShowAddToVacancyModal(true)} className="gap-1.5">
                      <UserPlus className="w-4 h-4 text-gray-600" />
                      Adicionar à Vaga
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Adicionar à Vaga</TooltipContent>
                </Tooltip>
                <Separator orientation="vertical" className="h-6 mx-2" />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      size="sm" 
                      variant={isFavorite ? "default" : "outline"} 
                      onClick={handleToggleFavorite} 
                      className={`gap-1.5 ${isFavorite ? 'bg-wedo-magenta hover:bg-wedo-magenta text-white' : ''}`}
                    >
                      <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current text-white' : 'text-wedo-magenta'}`} />
                      {isFavorite ? 'Favoritado' : 'Favoritar'}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{isFavorite ? 'Remover dos Favoritos' : 'Adicionar aos Favoritos'}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => setShowAddToListModal(true)} className="gap-1.5">
                      <Plus className="w-4 h-4 text-gray-600" />
                      Adicionar à Lista
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Adicionar à Lista</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      size="sm" 
                      variant={isHidden ? "default" : "outline"} 
                      onClick={handleHideCandidate}
                      className={`gap-1.5 ${isHidden ? 'bg-gray-500 hover:bg-gray-600 text-white' : ''}`}
                    >
                      <EyeOff className={`w-4 h-4 ${isHidden ? 'text-white' : 'text-gray-500'}`} />
                      {isHidden ? 'Oculto' : 'Ocultar'}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{isHidden ? 'Mostrar Candidato' : 'Ocultar Candidato'}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="outline" onClick={() => openCommunicationModal('feedback')} className="gap-1.5">
                      <Send className="w-4 h-4 text-gray-600" />
                      Feedback
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Enviar Feedback</TooltipContent>
                </Tooltip>
              </div>
            </CardContent>
          </Card>

          {/* TABS */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ActiveTab)} className="space-y-4">
            <TabsList className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <TabsTrigger value="profile" className="gap-1.5">
                <FileText className="w-4 h-4" />
                Perfil Completo
              </TabsTrigger>
              <TabsTrigger value="activities" className="gap-1.5">
                <Activity className="w-4 h-4" />
                Atividades
              </TabsTrigger>
              <TabsTrigger value="files" className="gap-1.5">
                <List className="w-4 h-4" />
                Arquivos
              </TabsTrigger>
              <TabsTrigger value="opinions" className="gap-1.5">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Pareceres e Análises
              </TabsTrigger>
            </TabsList>

            {/* Experience Highlight - AI-generated summary */}
            {candidate && (
              <ExperienceHighlightCard candidate={candidate} companyId="demo_company" />
            )}

            {/* TAB: PROFILE */}
            <CandidateProfileTab
              candidate={candidate}
              education={education}
              experiences={experiences}
              skillCategories={skillCategories}
              languagesData={languagesData}
              calculateAge={calculateAge}
              formatCurrency={formatCurrency}
              formatDate={formatDate}
              formatDateShort={formatDateShort}
              getLanguageLevel={getLanguageLevel}
              hasDocuments={hasDocuments}
              hasPearchData={hasPearchData}
              hasPersonalData={hasPersonalData}
            />

            {/* TAB: ACTIVITIES */}
            <TabsContent value="activities" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    {/* Header com filtros e botão de adicionar */}
                    <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-gray-800 flex items-center gap-2">
                          <Activity className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                          Feed de Atividades
                          <Badge className="text-xs px-1.5 py-0">{activities.length}</Badge>
                        </h4>
                        <div className="flex items-center gap-2">
                          <select
                            value={periodFilter}
                            onChange={(e) => setPeriodFilter(e.target.value as '7days' | '30days' | '3months' | 'all')}
                            className="text-xs px-2 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20 dark:text-gray-200"
                          >
                            <option value="7days">Últimos 7 dias</option>
                            <option value="30days">Últimos 30 dias</option>
                            <option value="3months">Últimos 3 meses</option>
                            <option value="all">Todo período</option>
                          </select>
                          <div className="flex items-center bg-white dark:bg-gray-800 rounded-md p-0.5 border border-gray-200 dark:border-gray-600">
                            <button
                              onClick={() => setActivityView('timeline')}
                              className={`p-1.5 rounded-md transition-colors ${
                                activityView === 'timeline' ? 'bg-gray-200 text-gray-800 dark:text-gray-200' : 'text-gray-600 hover:text-gray-700'
                              }`}
                              title="Visualização Timeline"
                            >
                              <GitBranch className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setActivityView('list')}
                              className={`p-1.5 rounded-md transition-colors ${
                                activityView === 'list' ? 'bg-gray-200 text-gray-800 dark:text-gray-200' : 'text-gray-600 hover:text-gray-700'
                              }`}
                              title="Visualização Lista"
                            >
                              <List className="w-4 h-4" />
                            </button>
                          </div>
                          <Button size="sm" className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:text-gray-200 border border-gray-200">
                            <PlusCircle className="w-3.5 h-3.5" />
                            Nova Atividade
                          </Button>
                        </div>
                      </div>

                      {/* Filtros coloridos */}
                      <div className="flex gap-1.5 flex-wrap">
                        <button
                          onClick={() => setActivityFilter('all')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'all' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          Todas
                        </button>
                        <button
                          onClick={() => setActivityFilter('emails')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'emails' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📧 Emails
                        </button>
                        <button
                          onClick={() => setActivityFilter('interviews')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'interviews' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          🎤 Entrevistas
                        </button>
                        <button
                          onClick={() => setActivityFilter('tests')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'tests' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📝 Testes
                        </button>
                        <button
                          onClick={() => setActivityFilter('lia')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'lia' ? 'bg-status-error text-white' : 'bg-status-error/15 text-status-error hover:bg-status-error/20'
                          }`}
                        >
                          🤖 LIA
                        </button>
                        <button
                          onClick={() => setActivityFilter('offers')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'offers' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          💼 Ofertas
                        </button>
                        <button
                          onClick={() => setActivityFilter('applications')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'applications' ? 'bg-gray-700 text-white font-semibold' : 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-200'
                          }`}
                        >
                          📋 Inscrições
                        </button>
                        <button
                          onClick={() => setActivityFilter('notes')}
                          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                            activityFilter === 'notes' ? 'bg-status-warning text-white' : 'bg-status-warning/15 text-status-warning hover:bg-status-warning/20'
                          }`}
                        >
                          📝 Notas
                        </button>
                      </div>
                    </div>

                    {/* Seção de Adicionar Nota */}
                    {(activityFilter === 'notes' || activityFilter === 'all') && (
                      <div className="p-4 border-b border-gray-100 bg-status-warning/10/30">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0 mt-1">
                            <FileText className="w-4 h-4 text-status-warning" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Categoria:</span>
                              <select 
                                value={newNoteCategory}
                                onChange={(e) => setNewNoteCategory(e.target.value as 'general' | 'interview' | 'screening' | 'feedback' | 'technical')}
                                className="text-xs px-2 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-400 dark:text-gray-200"
                              >
                                <option value="general">📋 Nota Geral</option>
                                <option value="interview">🎤 Nota de Entrevista</option>
                                <option value="screening">📞 Nota de Triagem</option>
                                <option value="feedback">💬 Feedback Interno</option>
                                <option value="technical">💻 Avaliação Técnica</option>
                              </select>
                            </div>
                            <textarea 
                              value={newNoteContent}
                              onChange={(e) => setNewNoteContent(e.target.value)}
                              placeholder="Adicione uma nota sobre este candidato..."
                              className="w-full text-sm px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-amber-400 bg-white dark:bg-gray-800 dark:text-gray-200"
                              rows={2}
                            />
                          </div>
                          <Button 
                            size="sm" 
                            className="gap-1.5 mt-6 bg-status-warning hover:bg-status-warning/10 text-white"
                            disabled={!newNoteContent.trim()}
                            onClick={() => {
                              if (newNoteContent.trim()) {
                                // Add note to local activities (will persist when backend API is available)
                                const newNote = {
                                  id: `note-${Date.now()}`,
                                  type: 'note',
                                  category: newNoteCategory,
                                  content: newNoteContent.trim(),
                                  created_at: new Date().toISOString(),
                                  author: 'Recrutador'
                                }
                                setActivities(prev => [newNote, ...prev])
                                toast({
                                  title: "Nota adicionada",
                                  description: "A nota foi registrada no histórico do candidato"
                                })
                                setNewNoteContent('')
                                setNewNoteCategory('general')
                              }
                            }}
                          >
                            <Plus className="w-3.5 h-3.5" />
                            Salvar
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Feed de Atividades */}
                    <div className="flex-1 p-4">
                      {isLoadingActivities ? (
                        <div className="flex items-center justify-center py-12">
                          <Loader2 className="w-6 h-6 animate-spin text-gray-600 dark:text-gray-400" />
                        </div>
                      ) : (() => {
                        const getCategoryLabel = (cat: string) => {
                          const labels: Record<string, string> = {
                            'general': 'Geral',
                            'interview': 'Entrevista',
                            'screening': 'Triagem',
                            'feedback': 'Feedback',
                            'technical': 'Técnica'
                          }
                          return labels[cat] || 'Geral'
                        }
                        
                        const parseNotes = () => {
                          if (!candidate?.notes) return []
                          if (typeof candidate.notes === 'string') {
                            return [{
                              id: 'note-legacy',
                              type: 'note',
                              category: 'general',
                              content: candidate.notes,
                              created_at: candidate.updated_at || new Date().toISOString()
                            }]
                          }
                          if (Array.isArray(candidate.notes)) {
                            return (candidate.notes as Record<string, unknown>[]).map((note: Record<string, unknown>, idx: number) => ({
                              id: note.id || `note-${idx}`,
                              type: 'note',
                              category: note.category || 'general',
                              content: note.content || note.text || note,
                              created_at: note.created_at || note.date || candidate.updated_at
                            }))
                          }
                          return []
                        }
                        
                        const candidateNotes = parseNotes()
                        
                        const allItems = [
                          ...activities.map(a => ({ ...a, itemType: a.activity_type || a.type || 'activity' })),
                          ...candidateNotes.map(n => ({ ...n, itemType: 'note' }))
                        ].sort((a, b) => {
                          const dateA = new Date(a.created_at || a.timestamp || 0).getTime()
                          const dateB = new Date(b.created_at || b.timestamp || 0).getTime()
                          return dateB - dateA
                        })
                        
                        const filteredItems = allItems.filter(item => {
                          if (activityFilter === 'all') return true
                          if (activityFilter === 'notes') return item.itemType === 'note'
                          if (activityFilter === 'emails') return item.itemType === 'email' || item.type === 'email'
                          if (activityFilter === 'interviews') return item.itemType === 'interview' || item.type === 'interview'
                          if (activityFilter === 'lia') return item.itemType === 'lia' || item.type === 'lia' || item.source === 'lia'
                          if (activityFilter === 'tests') return item.itemType === 'test' || item.type === 'test'
                          if (activityFilter === 'offers') return item.itemType === 'offer' || item.type === 'offer'
                          if (activityFilter === 'applications') return item.itemType === 'application' || item.type === 'application'
                          return true
                        })
                        
                        if (filteredItems.length === 0) {
                          return (
                            <div className="flex flex-col items-center justify-center py-12 px-4">
                              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                                {activityFilter === 'notes' ? (
                                  <FileText className="w-8 h-8 text-status-warning" />
                                ) : (
                                  <Activity className="w-8 h-8 text-gray-600" />
                                )}
                              </div>
                              <h3 className="text-sm font-medium text-gray-800 mb-2">
                                {activityFilter === 'notes' 
                                  ? 'Nenhuma nota registrada ainda'
                                  : 'Nenhuma atividade registrada ainda'}
                              </h3>
                              <p className="text-xs text-gray-600 text-center max-w-xs">
                                {activityFilter === 'notes'
                                  ? 'Use o formulário acima para adicionar notas sobre este candidato'
                                  : 'As atividades aparecerão aqui conforme o processo avança'}
                              </p>
                            </div>
                          )
                        }
                        
                        return (
                          <div className="space-y-3">
                            {filteredItems.map((item: Record<string, unknown>, index: number) => {
                              if (item.itemType === 'note') {
                                return (
                                  <div key={item.id || index} className="flex items-start gap-3 p-3 bg-status-warning/10/50 rounded-md border border-status-warning/30 hover:transition-all">
                                    <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center flex-shrink-0">
                                      <FileText className="w-4 h-4 text-status-warning" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                                        <span className="text-xs font-medium text-gray-800">Nota Interna</span>
                                        <Badge className="text-micro px-1.5 py-0 bg-status-warning/15 text-status-warning border-status-warning/30">
                                          {getCategoryLabel(item.category)}
                                        </Badge>
                                        <span className="text-xs text-gray-400">
                                          {formatRelativeTime(item.created_at)}
                                        </span>
                                      </div>
                                      <p className="text-sm text-gray-600">{item.content}</p>
                                      {item.user_name && (
                                        <p className="text-xs text-gray-500 mt-1">Por: {item.user_name}</p>
                                      )}
                                    </div>
                                  </div>
                                )
                              }
                              
                              return (
                                <div key={item.id || index} className="flex gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700 hover:transition-all">
                                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                                    <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="text-sm font-medium text-gray-800">
                                        {item.activity_type || item.type || item.title || 'Atividade'}
                                      </span>
                                      <span className="text-xs text-gray-500">
                                        {formatRelativeTime(item.created_at || item.timestamp)}
                                      </span>
                                    </div>
                                    {(item.description || item.content || item.details) && (
                                      <p className="text-sm text-gray-600">
                                        {item.description || item.content || item.details}
                                      </p>
                                    )}
                                    {item.user_name && (
                                      <p className="text-xs text-gray-500 mt-1">Por: {item.user_name}</p>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )
                      })()}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: FILES */}
            <TabsContent value="files" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-0">
                  <div className="flex flex-col">
                    {/* Header com botão de adicionar */}
                    <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                          Arquivos e Documentos
                          <Badge className="text-xs px-1.5 py-0">{candidateFiles.length}</Badge>
                          {isLoadingFiles && (
                            <div className="animate-spin rounded-full h-3.5 w-3.5 border border-gray-400 border-t-gray-700"></div>
                          )}
                        </h4>
                        <Button
                          size="sm"
                          className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:text-gray-200 border border-gray-200"
                          onClick={() => {
                            const input = document.createElement('input')
                            input.type = 'file'
                            input.multiple = true
                            input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
                            input.onchange = (e) => {
                              const files = Array.from((e.target as HTMLInputElement).files || [])
                              handleFileUpload(files)
                            }
                            input.click()
                          }}
                          disabled={isUploading}
                        >
                          <Plus className="w-3.5 h-3.5" />
                          {isUploading ? 'Enviando...' : 'Adicionar Arquivo'}
                        </Button>
                      </div>

                      {/* Categorias */}
                      <div className="flex gap-1.5 flex-wrap">
                        <Badge 
                          variant="outline" 
                          className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${!selectedCategory ? 'bg-gray-100' : ''}`}
                          onClick={() => setSelectedCategory(null)}
                        >
                          📁 Todos ({candidateFiles.length})
                        </Badge>
                        {fileCategories.filter((c: Record<string, unknown>) => (c.count as number) > 0).map((cat: Record<string, unknown>) => (
                          <Badge 
                            key={cat.category}
                            variant="outline" 
                            className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${selectedCategory === cat.category ? 'bg-gray-100' : ''}`}
                            onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
                          >
                            {cat.icon} {cat.label} ({cat.count})
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Lista de Arquivos */}
                    <div className="flex-1 p-4 space-y-3">
                      {/* Drag and Drop Area */}
                      <div
                        className={`border-2 border-dashed rounded-md p-6 text-center transition-all cursor-pointer group ${
                          isDragging ? 'border-gray-400 bg-gray-100' : 'border-gray-300 hover:border-gray-400'
                        }`}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={(e) => {
                          e.preventDefault()
                          setIsDragging(false)
                          const files = Array.from(e.dataTransfer.files)
                          handleFileUpload(files)
                        }}
                        onClick={() => {
                          if (isUploading) return
                          const input = document.createElement('input')
                          input.type = 'file'
                          input.multiple = true
                          input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
                          input.onchange = (e) => {
                            const files = Array.from((e.target as HTMLInputElement).files || [])
                            handleFileUpload(files)
                          }
                          input.click()
                        }}
                      >
                        <div className="flex flex-col items-center">
                          {isUploading ? (
                            <>
                              <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center mb-3">
                                <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-400 border-t-gray-700"></div>
                              </div>
                              <p className="text-sm text-gray-800 dark:text-gray-200 font-medium mb-2">Enviando... {uploadProgress}%</p>
                              <div className="w-40 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div className="h-full bg-gray-600 rounded-full transition-all duration-300" style={{width: `${uploadProgress}%`}} />
                              </div>
                            </>
                          ) : (
                            <>
                              <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors ${isDragging ? 'bg-gray-200' : 'bg-gray-100 group-hover:bg-gray-200'}`}>
                                <Upload className={`w-6 h-6 ${isDragging ? 'text-gray-800 dark:text-gray-200' : 'text-gray-600 group-hover:text-gray-700'}`} />
                              </div>
                              <p className="text-sm text-gray-800 dark:text-gray-200 mb-1">
                                {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                              </p>
                              <p className="text-xs text-gray-500">PDF, DOC, DOCX, JPG, PNG, MP4 • Máx 10MB</p>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Lista de arquivos da API */}
                      {candidateFiles
                        .filter((file: Record<string, unknown>) => !selectedCategory || file.file_type === selectedCategory)
                        .map((file: Record<string, unknown>) => {
                          const colors = getCategoryColor(file.file_type)
                          return (
                            <div key={file.id} className="border border-gray-100 dark:border-gray-700 rounded-md hover:transition-all">
                              <div className="p-3">
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                                    {getFileIcon(file.file_type, file.mime_type)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <h5 className="text-sm font-medium text-gray-800 truncate">{file.file_name}</h5>
                                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                                          <span className="text-xs text-gray-500">
                                            {formatFileSize(file.file_size)} • {file.file_name.split('.').pop()?.toUpperCase()}
                                          </span>
                                          <span className="text-xs text-gray-500">{formatRelativeTime(file.created_at)}</span>
                                          <Badge className="text-xs px-1.5 py-0 h-4" style={{backgroundColor: colors.bg, color: colors.text}}>
                                            <Tag className="w-2.5 h-2.5 mr-0.5" />
                                            {getCategoryLabel(file.file_type)}
                                          </Badge>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-1.5">
                                        <Button size="sm" variant="ghost" className="p-1.5 h-7 w-7" onClick={() => handleDownloadFile(file.file_url, file.file_name)} title="Baixar arquivo">
                                          <Download className="w-3.5 h-3.5" />
                                        </Button>
                                        <Button size="sm" variant="ghost" className="p-1.5 h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10" onClick={() => handleDeleteFile(file.id)} title="Excluir arquivo">
                                          <X className="w-3.5 h-3.5" />
                                        </Button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        })}

                      {/* Empty state */}
                      {candidateFiles.length === 0 && !isLoadingFiles && (
                        <div className="text-center py-8 text-gray-500">
                          <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300" />
                          <p className="text-sm">Nenhum arquivo enviado</p>
                          <p className="text-xs text-gray-400 mt-1">Arraste arquivos ou clique acima para enviar</p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: OPINIONS & ANALYSES */}
            <TabsContent value="opinions" className="mt-4">
              <Card className="border-gray-100">
                <CardContent className="p-4 space-y-4">
                  {/* SubTabs */}
                  <div className="flex items-center gap-4 border-b border-gray-100 pb-3">
                    <button
                      onClick={() => setOpinionsSubTab('pareceres')}
                      className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors ${
                        opinionsSubTab === 'pareceres' 
                          ? 'text-gray-600 dark:text-gray-400 border-b-2 border-gray-900 dark:border-gray-50' 
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Pareceres da LIA
                      {opinionsHistory.length > 0 && (
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-900" style={{color: 'white'}}>
                          {opinionsHistory.length}
                        </Badge>
                      )}
                    </button>
                    <button
                      onClick={() => setOpinionsSubTab('analises')}
                      className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors ${
                        opinionsSubTab === 'analises' 
                          ? 'text-wedo-purple border-b-2 border-wedo-purple/30' 
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Análises
                      {(savedAnalyses?.total_analyses || 0) > 0 && (
                        <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple text-white">
                          {savedAnalyses?.total_analyses || 0}
                        </Badge>
                      )}
                    </button>
                  </div>
                  
                  {/* PARECERES SUBTAB */}
                  {opinionsSubTab === 'pareceres' && (
                    <>
                  {/* Loading State */}
                  {isLoadingOpinions && (
                    <div className="space-y-3">
                      {[1, 2].map((i) => (
                        <div key={i} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                            <div className="flex-1">
                              <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-md mb-1"></div>
                              <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                            <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Empty State */}
                  {!isLoadingOpinions && opinionsHistory.length === 0 && (
                    <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-8 text-center">
                      <div className="w-14 h-14 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4">
                        <FileText className="w-7 h-7 text-gray-400" />
                      </div>
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Nenhum parecer disponível</p>
                      <p className="text-xs text-gray-500">
                        Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                      </p>
                    </div>
                  )}
                  
                  {/* Opinions List */}
                  {!isLoadingOpinions && opinionsHistory.length > 0 && (
                    <div className="space-y-3">
                      {opinionsHistory.map((opinion: Record<string, unknown>) => {
                        const isExpanded = expandedOpinionId === opinion.id
                        const isWsi = opinion.opinion_type === 'wsi'
                        const displayScore = isWsi ? opinion.wsi_score : opinion.score
                        
                        const getScoreColor = (score: number | null) => {
                          if (score === null || score === undefined) return 'text-gray-600'
                          if (score >= 80) return 'text-status-success'
                          if (score >= 60) return 'text-status-warning'
                          return 'text-status-error'
                        }
                        
                        const getRecommendationBadge = (rec: string | null) => {
                          if (!rec) return null
                          if (rec === 'approved') return <Badge className="bg-status-success/15 text-status-success text-xs flex items-center gap-0.5"><CheckCircle className="w-2.5 h-2.5" />APROVADO</Badge>
                          if (rec === 'pending_review') return <Badge className="bg-status-warning/15 text-status-warning text-xs flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />PENDENTE</Badge>
                          if (rec === 'not_approved') return <Badge className="bg-status-error/15 text-status-error text-xs flex items-center gap-0.5"><X className="w-2.5 h-2.5" />NÃO APROVADO</Badge>
                          return null
                        }
                        
                        return (
                          <div key={opinion.id} className="relative">
                            {!opinion.is_current && (
                              <Badge className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-500 z-10">
                                v{opinion.version} - Histórico
                              </Badge>
                            )}
                            <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md overflow-hidden">
                              <button
                                onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id)}
                                className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <div className={`w-9 h-9 rounded-full flex items-center justify-center ${isWsi ? 'bg-wedo-purple/15' : 'bg-gray-100 dark:bg-gray-800'}`}>
                                    {isWsi ? <Target className="w-4 h-4 text-wedo-purple" /> : <Brain className="w-4 h-4 text-wedo-cyan" />}
                                  </div>
                                  <div className="text-left">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-sm font-medium text-gray-800">{isWsi ? 'Parecer WSI' : 'Parecer Geral'}</span>
                                      {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title}
                                        </Badge>
                                      ) : opinion.job_vacancy_title ? (
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50 border-gray-300 dark:border-gray-600 flex items-center gap-1">
                                          <Briefcase className="w-2.5 h-2.5" />
                                          {opinion.job_vacancy_title}
                                        </Badge>
                                      ) : null}
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      {displayScore !== null && displayScore !== undefined && (
                                        <span className={`text-xs font-semibold ${getScoreColor(displayScore)}`}>
                                          {isWsi ? `WSI: ${displayScore.toFixed(1)}/5` : `Score: ${Math.round(displayScore)}/100`}
                                        </span>
                                      )}
                                      {opinion.archetype && <><span className="text-gray-300">•</span><span className="text-xs text-gray-500">{opinion.archetype}</span></>}
                                      {getRecommendationBadge(opinion.recommendation)}
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          const parecerText = [
                                            opinion.summary,
                                            opinion.strengths?.length ? `Pontos Fortes:\n${opinion.strengths.join('\n')}` : '',
                                            opinion.gaps?.length ? `Gaps:\n${opinion.gaps.join('\n')}` : '',
                                            opinion.next_steps ? `Próximos Passos: ${opinion.next_steps}` : ''
                                          ].filter(Boolean).join('\n\n')
                                          copyToClipboard(parecerText, 'Parecer')
                                        }}
                                        className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                      >
                                        <Copy className="w-4 h-4 text-gray-400" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent>Copiar Parecer</TooltipContent>
                                  </Tooltip>
                                  {opinion.created_at && <span className="text-micro text-gray-400">{formatDate(opinion.created_at)}</span>}
                                  {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                </div>
                              </button>
                              
                              {isExpanded && (
                                <div className="px-4 pb-4 pt-0 border-t border-gray-100 space-y-4">
                                  {opinion.summary && (
                                    <div className="pt-4">
                                      <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">{opinion.summary}</p>
                                    </div>
                                  )}
                                  
                                  {opinion.score_breakdown && Object.keys(opinion.score_breakdown).length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                        <BarChart3 className="w-3.5 h-3.5" />
                                        Score Breakdown
                                      </h5>
                                      <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(opinion.score_breakdown).map(([key, value]: [string, unknown]) => (
                                          value !== null && value !== undefined && (
                                            <div key={key} className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-700 rounded-md px-3 py-2">
                                              <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                                              <span className="font-medium text-gray-800">{typeof value === 'number' ? `${Math.round(value)}%` : String(value)}</span>
                                            </div>
                                          )
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {opinion.strengths && opinion.strengths.length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
                                        <CheckCircle className="w-3.5 h-3.5" />
                                        Pontos Fortes
                                      </h5>
                                      <ul className="space-y-1">
                                        {opinion.strengths.map((s: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                                            <span className="text-status-success mt-0.5">•</span>{s}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.gaps && opinion.gaps.length > 0 && (
                                    <div>
                                      <h5 className="text-xs font-medium text-status-error mb-2 flex items-center gap-1">
                                        <AlertCircle className="w-3.5 h-3.5" />
                                        Gaps Identificados
                                      </h5>
                                      <ul className="space-y-1">
                                        {opinion.gaps.map((g: string, i: number) => (
                                          <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                                            <span className="text-status-error mt-0.5">•</span>{g}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {opinion.next_steps && (
                                    <div>
                                      <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-1">
                                        <TrendingUp className="w-3.5 h-3.5" />
                                        Próximos Passos
                                      </h5>
                                      <p className="text-xs text-gray-600">{opinion.next_steps}</p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                    </>
                  )}

                  {/* ANALYSES SUBTAB */}
                  {opinionsSubTab === 'analises' && (
                    <>
                      {/* Loading State */}
                      {isLoadingAnalyses && (
                        <div className="space-y-3">
                          {[1, 2].map((i) => (
                            <div key={i} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-4 animate-pulse">
                              <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                                <div className="flex-1">
                                  <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-md mb-1"></div>
                                  <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                                </div>
                              </div>
                              <div className="space-y-2">
                                <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                                <div className="w-3/4 h-3 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Empty State */}
                      {!isLoadingAnalyses && (!savedAnalyses?.analyses || savedAnalyses.analyses.length === 0) && (
                        <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md p-8 text-center">
                          <div className="w-14 h-14 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-4">
                            <Brain className="w-7 h-7 text-wedo-purple" />
                          </div>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Nenhuma análise salva</p>
                          <p className="text-xs text-gray-500">
                            Use o ícone 🧠 no perfil do candidato para gerar análises.
                          </p>
                        </div>
                      )}

                      {/* Analyses List */}
                      {!isLoadingAnalyses && savedAnalyses?.analyses?.length > 0 && (
                        <div className="space-y-3">
                          {(savedAnalyses.analyses as Record<string, unknown>[]).map((analysis: Record<string, unknown>) => {
                            const isExpanded = expandedAnalysisId === analysis.id
                            const analysisLabels: Record<string, string> = {
                              'bullet_points': 'Pontos-chave',
                              'short_paragraph': 'Resumo',
                              'detailed_bullets': 'Análise Detalhada'
                            }
                            
                            return (
                              <div key={analysis.id} className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-md overflow-hidden">
                                <button
                                  onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id)}
                                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                                >
                                  <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-full bg-wedo-purple/15 flex items-center justify-center">
                                      <Brain className="w-4 h-4 text-wedo-purple" />
                                    </div>
                                    <div className="text-left">
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-gray-800">
                                          {analysisLabels[analysis.analysis_type] || analysis.analysis_type}
                                        </span>
                                        <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                                          Análise LIA
                                        </Badge>
                                      </div>
                                      <span className="text-micro text-gray-400 mt-0.5">
                                        {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Data não disponível'}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            copyToClipboard(analysis.content, 'Análise')
                                          }}
                                          className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                        >
                                          <Copy className="w-4 h-4 text-gray-400" />
                                        </button>
                                      </TooltipTrigger>
                                      <TooltipContent>Copiar Análise</TooltipContent>
                                    </Tooltip>
                                    {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                  </div>
                                </button>
                                
                                {isExpanded && (
                                  <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                                    <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                                      {cleanMarkdown(analysis.content)}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* MODALS */}
        {candidate && (
          <>
            <UnifiedCommunicationModal
              isOpen={showCommunicationModal}
              onClose={() => setShowCommunicationModal(false)}
              candidate={{
                id: candidate.id,
                name: candidate.name,
                role: candidate.current_title || '',
                email: candidate.email || '',
                phone: candidate.phone || candidate.mobile_phone || '',
                location: candidate.location_city,
                avatar: candidate.avatar_url
              }}
              type={communicationType}
              companyId="demo_company"
            />
            
            <AddToListModal
              isOpen={showAddToListModal}
              onClose={() => setShowAddToListModal(false)}
              candidateIds={[candidate.id]}
              candidateNames={[candidate.name]}
            />
            
            <AddCandidatesToVacancyModal
              isOpen={showAddToVacancyModal}
              onClose={() => setShowAddToVacancyModal(false)}
              candidateIds={[candidate.id]}
              candidateNames={[candidate.name]}
            />
            
          </>
        )}
      </div>
    </TooltipProvider>
  )
}

