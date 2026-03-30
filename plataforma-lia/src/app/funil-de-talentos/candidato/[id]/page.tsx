"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  ArrowLeft, MapPin, Briefcase, Mail, Phone, Linkedin, Globe, Github,
  MessageSquare, UserPlus, Heart, EyeOff, CalendarDays, Plus, Send,
  FileText, Activity, List, Brain, Shield, Loader2, ClipboardCheck
} from "lucide-react"
import { badgeStyles } from "@/lib/design-tokens"
import { UnifiedCommunicationModal } from "@/components/modals/unified-communication-modal"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"
import dynamic from "next/dynamic"

import { useCandidatePageCore } from "./useCandidatePageCore"
import { CandidateProfileTab } from "./CandidateProfileTab"
import { CandidatoActivitiesTab } from "./components/CandidatoActivitiesTab"
import { CandidatoFilesTab } from "./components/CandidatoFilesTab"
import { CandidatoOpinionsTab } from "./components/CandidatoOpinionsTab"
import { CANDIDATE_STATUS_CONFIG } from "./candidato-page.constants"
import type { ActiveTab } from "./candidato-page.types"

const LiaAnalysisModal = dynamic(
  () => import("@/components/modals/lia-analysis-modal").then(m => ({ default: m.LiaAnalysisModal })),
  { ssr: false }
)

export default function CandidateProfilePage() {
  const {
    activeTab, activities, activityFilter, activityView, calculateAge,
    candidate, candidateFiles, cleanMarkdown, communicationType,
    copyToClipboard, education, error, expandedAnalysisId, expandedOpinionId,
    experiences, fetchSavedAnalyses, fileCategories, formatCurrency, formatDate,
    formatDateShort, formatFileSize, formatRelativeTime, getCategoryColor,
    getCategoryLabel, getFileIcon, getInitials, getLanguageLevel, getShortId,
    handleDeleteFile, handleDownloadFile, handleFileUpload, handleHideCandidate,
    handleToggleFavorite, hasDocuments, hasPearchData, hasPersonalData, isDragging,
    isFavorite, isHidden, isLoadingActivities, isLoadingAnalyses, isLoadingFiles,
    isLoadingOpinions, isUploading, languagesData, loading, newNoteCategory,
    newNoteContent, openCommunicationModal, opinionsHistory, opinionsSubTab,
    periodFilter, router, savedAnalyses, selectedCategory, setActiveTab,
    setActivities, setActivityFilter, setActivityView, setExpandedAnalysisId,
    setExpandedOpinionId, setIsDragging, setNewNoteCategory, setNewNoteContent,
    setOpinionsSubTab, setPeriodFilter, setSelectedCategory, setShowAddToListModal,
    setShowAddToVacancyModal, setShowCommunicationModal, setShowLiaAnalysisModal,
    showAddToListModal, showAddToVacancyModal, showCommunicationModal,
    showLiaAnalysisModal, skillCategories, toast, uploadProgress,
  } = useCandidatePageCore()

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-lia-bg-primary" role="status" aria-live="polite">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary mx-auto mb-3" />
          <p className="text-sm text-lia-text-secondary">Carregando perfil...</p>
        </div>
      </div>
    )
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (error || !candidate) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-lia-bg-primary" role="alert" aria-live="assertive">
        <div className="text-center">
          <p className="text-sm text-status-error mb-4">{error || "Candidato não encontrado"}</p>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />Voltar
          </Button>
        </div>
      </div>
    )
  }

  const statusConfig = CANDIDATE_STATUS_CONFIG[candidate.candidate_status || "active"] ?? CANDIDATE_STATUS_CONFIG.active

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <Button variant="ghost" size="sm" onClick={() => router.back()} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />Voltar
          </Button>

          {/* ── HEADER CARD ───────────────────────────────────────────── */}
          <Card className="mb-4 border-lia-border-subtle">
            <CardContent className="py-5 px-6">
              <div className="flex items-start gap-5">
                <Avatar className="h-20 w-20 border-2 border-lia-border-subtle">
                  {candidate.avatar_url && <AvatarImage src={candidate.avatar_url} alt={candidate.name} />}
                  <AvatarFallback className="bg-gray-100 text-lia-text-secondary text-xl font-semibold">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  {/* Name row */}
                  <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                    <h1 className="text-xl font-semibold text-lia-text-primary">{candidate.name}</h1>
                    <span className="text-xs font-mono text-lia-text-secondary bg-gray-100 px-2 py-0.5 rounded-md">
                      {getShortId(candidate.id)}
                    </span>
                    {candidate.seniority_level && <Badge className={badgeStyles.primary}>{candidate.seniority_level}</Badge>}
                    {candidate.years_of_experience && (
                      <Badge variant="outline" className="text-xs">{candidate.years_of_experience} anos exp.</Badge>
                    )}
                    {candidate.communication_consent && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                            <Shield className="w-3 h-3 mr-1" />LGPD
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
                    {candidate.is_tech && (
                      <Badge variant="outline" className="text-xs bg-gray-100 text-lia-text-primary border-lia-border-default dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:border-lia-border-default">Tech</Badge>
                    )}
                    {candidate.is_potential && (
                      <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">Potencial</Badge>
                    )}
                    <Badge className={`text-xs ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}>
                      {statusConfig.label}
                    </Badge>
                    <LiaAnalysisModal
                      isOpen={showLiaAnalysisModal}
                      onClose={() => setShowLiaAnalysisModal(false)}
                      onOpen={() => setShowLiaAnalysisModal(true)}
                      candidate={candidate}
                      onTransportToOpinions={() => fetchSavedAnalyses()}
                    >
                      <button
                        className="p-1.5 rounded-full hover:bg-gray-100 dark:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                        title="Análise LIA do Perfil"
                      >
                        <Brain className="w-5 h-5 text-wedo-cyan" />
                      </button>
                    </LiaAnalysisModal>
                  </div>

                  {/* Title / Company */}
                  <div className="flex items-center gap-2 text-sm text-lia-text-primary mb-1">
                    {candidate.current_title && (
                      <><Briefcase className="w-4 h-4 text-lia-text-secondary" /><span className="font-medium">{candidate.current_title}</span></>
                    )}
                    {candidate.current_company && (
                      <><span className="text-lia-text-secondary">•</span><span>{candidate.current_company}</span></>
                    )}
                  </div>

                  {/* Location */}
                  {(candidate.location_city || candidate.location_state) && (
                    <div className="flex items-center gap-1.5 text-sm text-lia-text-secondary mb-3">
                      <MapPin className="w-4 h-4" />
                      <span>{[candidate.location_city, candidate.location_state, candidate.location_country].filter(Boolean).join(", ")}</span>
                    </div>
                  )}

                  {/* Contact + Social */}
                  <div className="flex items-center gap-4 flex-wrap">
                    {candidate.email && (
                      <a href={`mailto:${candidate.email}`} className="flex items-center gap-1.5 text-sm text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                        <Mail className="w-4 h-4" />{candidate.email}
                      </a>
                    )}
                    {(candidate.phone || candidate.mobile_phone) && (
                      <a href={`tel:${candidate.mobile_phone || candidate.phone}`} className="flex items-center gap-1.5 text-sm text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                        <Phone className="w-4 h-4" />{candidate.mobile_phone || candidate.phone}
                      </a>
                    )}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a href={candidate.linkedin_url || "#"} target="_blank" rel="noopener noreferrer"
                          className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${candidate.linkedin_url ? "hover:bg-gray-100 dark:hover:bg-gray-800" : "opacity-30 cursor-default"}`}
                          onClick={(e) => !candidate.linkedin_url && e.preventDefault()}
                        >
                          <Linkedin className="w-5 h-5" style={{ color: candidate.linkedin_url ? "#0A66C2" : "var(--gray-400)" }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>LinkedIn</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a href={candidate.github_url || "#"} target="_blank" rel="noopener noreferrer"
                          className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${candidate.github_url ? "hover:bg-gray-100" : "opacity-30 cursor-default"}`}
                          onClick={(e) => !candidate.github_url && e.preventDefault()}
                        >
                          <Github className="w-5 h-5" style={{ color: candidate.github_url ? "#181717" : "var(--gray-400)" }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>GitHub</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <a href={candidate.portfolio_url || "#"} target="_blank" rel="noopener noreferrer"
                          className={`p-1.5 rounded-md transition-colors motion-reduce:transition-none ${candidate.portfolio_url ? "hover:bg-gray-100 dark:hover:bg-gray-800" : "opacity-30 cursor-default"}`}
                          onClick={(e) => !candidate.portfolio_url && e.preventDefault()}
                        >
                          <Globe className="w-5 h-5" style={{ color: candidate.portfolio_url ? "var(--gray-950)" : "var(--gray-400)" }} />
                        </a>
                      </TooltipTrigger>
                      <TooltipContent>Portfolio</TooltipContent>
                    </Tooltip>
                  </div>
                </div>

                {/* Right column — work prefs + dates */}
                <div className="text-right space-y-3 min-w-sidebar-content">
                  <div className="flex flex-wrap gap-1.5 justify-end">
                    {candidate.work_model && <Badge variant="outline" className="text-xs bg-gray-50 text-lia-text-primary border-lia-border-subtle">{String(candidate.work_model)}</Badge>}
                    {candidate.work_mode && <Badge variant="outline" className="text-xs bg-gray-50 text-lia-text-primary border-lia-border-subtle">{String(candidate.work_mode)}</Badge>}
                    {candidate.contract_type && <Badge variant="outline" className="text-xs bg-gray-50 text-lia-text-primary border-lia-border-subtle">{String(candidate.contract_type)}</Badge>}
                    {candidate.is_remote && <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-lia-bg-primary text-lia-text-primary border-lia-border-default">🌐 Remoto</Badge>}
                    {candidate.willing_to_relocate && <Badge variant="outline" className="text-xs bg-status-success/10 text-status-success border-status-success/30">✈️ Aceita Mudança</Badge>}
                    {candidate.mobility && <Badge variant="outline" className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">🚗 Mobilidade</Badge>}
                    {candidate.availability && <Badge variant="outline" className="text-xs bg-gray-50 text-lia-text-primary border-lia-border-subtle">{String(candidate.availability)}</Badge>}
                  </div>
                  <div className="text-xs text-lia-text-secondary space-y-0.5">
                    <p className="font-semibold text-lia-text-primary">Datas</p>
                    {candidate.updated_at && <p>Atualizado: {formatDate(String(candidate.updated_at))}</p>}
                    {candidate.last_contact_at && <p>Último contato: {formatDate(String(candidate.last_contact_at))}</p>}
                    {candidate.last_activity_at && <p>Última atividade: {formatDate(String(candidate.last_activity_at))}</p>}
                    {!candidate.updated_at && !candidate.last_contact_at && !candidate.last_activity_at && candidate.created_at && (
                      <p>Cadastro: {formatDate(String(candidate.created_at))}</p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── ACTION BAR ────────────────────────────────────────────── */}
          <Card className="mb-4 border-lia-border-subtle">
            <CardContent className="py-3 px-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => openCommunicationModal("email")} className="gap-1.5">
                    <Mail className="w-4 h-4 text-lia-text-secondary" />Email
                  </Button>
                </TooltipTrigger><TooltipContent>Enviar Email</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => openCommunicationModal("whatsapp")} className="gap-1.5">
                    <MessageSquare className="w-4 h-4 text-status-success" />WhatsApp
                  </Button>
                </TooltipTrigger><TooltipContent>Enviar WhatsApp</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => openCommunicationModal("agendamento")} className="gap-1.5">
                    <CalendarDays className="w-4 h-4 text-wedo-orange" />Agendar Entrevista
                  </Button>
                </TooltipTrigger><TooltipContent>Agendar Entrevista</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => openCommunicationModal("triagem")} className="gap-1.5">
                    <ClipboardCheck className="w-4 h-4 text-wedo-purple" />Triagem WSI
                  </Button>
                </TooltipTrigger><TooltipContent>Enviar Triagem WSI</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => setShowAddToVacancyModal(true)} className="gap-1.5">
                    <UserPlus className="w-4 h-4 text-lia-text-secondary" />Adicionar à Vaga
                  </Button>
                </TooltipTrigger><TooltipContent>Adicionar à Vaga</TooltipContent></Tooltip>

                <Separator orientation="vertical" className="h-6 mx-2" />

                <Tooltip><TooltipTrigger asChild>
                  <Button
                    size="sm"
                    variant={isFavorite ? "secondary" : "outline"}
                    onClick={handleToggleFavorite}
                    className={`gap-1.5 ${isFavorite ? "bg-wedo-magenta hover:bg-wedo-magenta text-white" : ""}`}
                  >
                    <Heart className={`w-4 h-4 ${isFavorite ? "fill-current text-white" : "text-wedo-magenta"}`} />
                    {isFavorite ? "Favoritado" : "Favoritar"}
                  </Button>
                </TooltipTrigger><TooltipContent>{isFavorite ? "Remover dos Favoritos" : "Adicionar aos Favoritos"}</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => setShowAddToListModal(true)} className="gap-1.5">
                    <Plus className="w-4 h-4 text-lia-text-secondary" />Adicionar à Lista
                  </Button>
                </TooltipTrigger><TooltipContent>Adicionar à Lista</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button
                    size="sm"
                    variant={isHidden ? "secondary" : "outline"}
                    onClick={handleHideCandidate}
                    className={`gap-1.5 ${isHidden ? "bg-gray-500 hover:bg-gray-600 text-white" : ""}`}
                  >
                    <EyeOff className={`w-4 h-4 ${isHidden ? "text-white" : "text-lia-text-secondary"}`} />
                    {isHidden ? "Oculto" : "Ocultar"}
                  </Button>
                </TooltipTrigger><TooltipContent>{isHidden ? "Mostrar Candidato" : "Ocultar Candidato"}</TooltipContent></Tooltip>

                <Tooltip><TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={() => openCommunicationModal("feedback")} className="gap-1.5">
                    <Send className="w-4 h-4 text-lia-text-secondary" />Feedback
                  </Button>
                </TooltipTrigger><TooltipContent>Enviar Feedback</TooltipContent></Tooltip>
              </div>
            </CardContent>
          </Card>

          {/* ── TABS ──────────────────────────────────────────────────── */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ActiveTab)} className="space-y-4">
            <TabsList className="bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
              <TabsTrigger value="profile" className="gap-1.5"><FileText className="w-4 h-4" />Perfil Completo</TabsTrigger>
              <TabsTrigger value="activities" className="gap-1.5"><Activity className="w-4 h-4" />Atividades</TabsTrigger>
              <TabsTrigger value="files" className="gap-1.5"><List className="w-4 h-4" />Arquivos</TabsTrigger>
              <TabsTrigger value="opinions" className="gap-1.5"><Brain className="w-4 h-4 text-wedo-cyan" />Pareceres e Análises</TabsTrigger>
            </TabsList>

            {candidate && <ExperienceHighlightCard candidate={candidate} companyId="demo_company" />}

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

            <CandidatoActivitiesTab
              activities={activities}
              activityFilter={activityFilter}
              activityView={activityView}
              periodFilter={periodFilter}
              newNoteContent={newNoteContent}
              newNoteCategory={newNoteCategory}
              isLoadingActivities={isLoadingActivities}
              candidate={candidate}
              setActivityFilter={setActivityFilter}
              setActivityView={setActivityView}
              setPeriodFilter={setPeriodFilter}
              setNewNoteContent={setNewNoteContent}
              setNewNoteCategory={setNewNoteCategory}
              setActivities={setActivities}
              formatRelativeTime={formatRelativeTime}
              toast={toast}
            />

            <CandidatoFilesTab
              candidateFiles={candidateFiles}
              fileCategories={fileCategories}
              isLoadingFiles={isLoadingFiles}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
              isDragging={isDragging}
              selectedCategory={selectedCategory}
              setIsDragging={setIsDragging}
              setSelectedCategory={setSelectedCategory}
              handleFileUpload={handleFileUpload}
              handleDownloadFile={handleDownloadFile}
              handleDeleteFile={handleDeleteFile}
              formatFileSize={formatFileSize}
              formatRelativeTime={formatRelativeTime}
              getCategoryColor={getCategoryColor}
              getCategoryLabel={getCategoryLabel}
              getFileIcon={getFileIcon}
            />

            <CandidatoOpinionsTab
              opinionsSubTab={opinionsSubTab}
              opinionsHistory={opinionsHistory}
              savedAnalyses={savedAnalyses}
              isLoadingOpinions={isLoadingOpinions}
              isLoadingAnalyses={isLoadingAnalyses}
              expandedOpinionId={expandedOpinionId}
              expandedAnalysisId={expandedAnalysisId}
              setOpinionsSubTab={setOpinionsSubTab}
              setExpandedOpinionId={setExpandedOpinionId}
              setExpandedAnalysisId={setExpandedAnalysisId}
              formatDate={formatDate}
              copyToClipboard={copyToClipboard}
              cleanMarkdown={cleanMarkdown}
            />
          </Tabs>
        </div>

        {/* ── MODALS ────────────────────────────────────────────────── */}
        {candidate && (
          <>
            <UnifiedCommunicationModal
              isOpen={showCommunicationModal}
              onClose={() => setShowCommunicationModal(false)}
              candidate={{
                id: candidate.id,
                name: candidate.name,
                role: candidate.current_title || "",
                email: candidate.email || "",
                phone: candidate.phone || candidate.mobile_phone || "",
                location: candidate.location_city,
                avatar: candidate.avatar_url,
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
