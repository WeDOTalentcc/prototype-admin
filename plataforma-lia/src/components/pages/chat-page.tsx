"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LIAIcon } from "@/components/ui/lia-icon"
import {
  Send, Loader2, FileText, MessageSquare, Search, MapPin, X,
  ChevronDown, Play, Mic, AlertTriangle, Cpu
} from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { InterviewSchedulingModal } from "@/components/ui/interview-scheduling-modal"
import { PromptSuggestionsDock } from "@/components/ui/prompt-suggestions-dock"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips } from "@/components/ui/quick-action-chips"
import { CommandPalette } from "@/components/ui/command-palette"
import { FileUploadButton } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { AgentControlCenter } from "@/components/agent-control-center"
import { CandidateDetailSidebar } from "@/components/search/candidate-detail-sidebar"
import { CreditConfirmationDialog } from "@/components/search/credit-confirmation-dialog"
import { SmartSearchInput } from "@/components/search/smart-search-input"
import { AdvancedFiltersModal } from "@/components/search/advanced-filters-modal"
import { SidePanelContainer } from "@/components/ui-actions"
import { EmptyFieldNotificationMessage } from "@/components/chat/empty-field-notification-message"
import { AgentMemoryIndicator } from "@/components/chat/agent-memory-indicator"
import { ChatContextPanel } from "@/components/chat/ChatContextPanel"
import { ChatMessageList } from "@/components/chat/ChatMessageList"
import type { Message } from "./chat-page/types"
import { useChatPageCore } from "./chat-page/useChatPageCore"

export function ChatPage() {
  const {
    messages, setMessages,
    input, setInput,
    isLoading,
    contextData, setContextData,
    isPanelOpen, setIsPanelOpen,
    searchTerm, setSearchTerm,
    showSearch, setShowSearch,
    newMessageIndicator,
    currentMessageIndex,
    availableCredits,
    isSchedulingModalOpen, setIsSchedulingModalOpen,
    isCommandPaletteOpen, setIsCommandPaletteOpen,
    selectedCandidateForScheduling,
    isCandidateDetailOpen, setIsCandidateDetailOpen,
    selectedCandidateForDetail, setSelectedCandidateForDetail,
    isCreditDialogOpen, setIsCreditDialogOpen,
    pendingPearchSearch,
    isSmartSearchMode,
    smartSearchQuery, setSmartSearchQuery,
    hasSearchResults,
    searchFlow,
    attachedFiles,
    fileValidationError, setFileValidationError,
    MAX_FILE_SIZE_MB,
    isRecording,
    recordingTime,
    audioBlob, setAudioBlob,
    fileAnalysisContext, setFileAnalysisContext,
    messagesEndRef,
    messagesContainerRef,
    inputRef,
    isEmptyChat,
    chatContainerClass, inputContainerClass, messagesContainerClass,
    chatId,
    chatTitle,
    activeTab, setActiveTab,
    activePendingAction,
    emptyFieldNotifications,
    currentSuggestion,
    isLoadingSuggestion,
    isFiltersModalOpen, setIsFiltersModalOpen,
    activeSearchFilters,
    handleSendMessage,
    handleKeyPress,
    handleSmartSearchSubmit,
    handleSmartSearchCancel,
    handleApplyFilters,
    handleRemoveFile,
    handleFilesSelected,
    handleFileAnalyzed,
    handleAudioTranscription,
    handleAudioRecordingStart,
    handleAudioRecordingEnd,
    stopRecording,
    handleEmptyFieldAction,
    handleSuggestionAccepted,
    handleSuggestionRejected,
    handleScheduleInterview,
    handlePipelineAction,
    handleAddCandidateToJob,
    handleSaveToBase,
    handleConfirmPearchSearch,
    activateSmartSearch,
    scrollToBottom,
    checkNewMessageIndicator,
    getRelativeTime,
    getQuickSuggestions,
    getActiveFiltersCount,
    highlightSearchTerm,
    renderChatCard,
    commandItems,
    getQuickActions,
    getPlaceholderText,
    handleLoadMoreCandidates,
    uiActions,
  } = useChatPageCore()

  return (
    <div className="flex overflow-hidden flex-1" style={{backgroundColor: 'var(--gray-50)'}}>
      {/* Main Chat Area */}
      <div className={`flex flex-col transition-all duration-300 overflow-hidden ${isPanelOpen ? 'w-3/5' : 'w-full'}`}>
        {/* Header */}
        <div className="py-3 px-6 flex-shrink-0" style={{backgroundColor: 'var(--gray-50)', borderBottom: '1px solid var(--gray-200)'}}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <LIAIcon size="lg" />
              <div>
                <h1 className="text-base font-semibold " style={{color: 'var(--gray-800)'}}>
                  Chat {chatId} - {chatTitle}
                </h1>
                <p className="text-xs font-open-sans text-gray-500">
                  Lia - Assistente de Recrutamento
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSearch(!showSearch)}
                className="transition-all duration-200 hover:scale-105"
                title="Buscar na conversa (Ctrl+F)"
              >
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Barra de Busca */}
          {showSearch && (
            <div className="mt-4 flex items-center space-x-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar na conversa..."
                  className="w-full px-3 py-2 rounded-md text-sm focus:outline-none"
                  style={{border: '1px solid var(--gray-200)',
                    backgroundColor: 'var(--white)',
                    color: 'var(--gray-800)'}}
                  autoFocus
                />
                <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-600" />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSearch(false)}
                className="hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Tabs de Navegação */}
          <div className="mt-2">
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "conversa" | "controle")}>
              <TabsList className="bg-transparent p-0 h-auto gap-4" style={{borderBottom: '1px solid var(--gray-200)'}}>
                <TabsTrigger 
                  value="conversa" 
                  className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 dark:border-gray-50 transition-all"
                  style={{color: activeTab === 'conversa' ? 'var(--gray-950)' : 'var(--gray-500)'}}
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Conversa
                </TabsTrigger>
                <TabsTrigger 
                  value="controle" 
                  className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 dark:border-gray-50 transition-all"
                  style={{color: activeTab === 'controle' ? 'var(--gray-950)' : 'var(--gray-500)'}}
                >
                  <Cpu className="w-4 h-4 mr-2" />
                  Centro de Controle
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <AgentMemoryIndicator 
            sessionId={chatId.replace('#', '')} 
            domain="wizard" 
          />
        </div>

        {/* Tab Content: Conversa */}
        {activeTab === "conversa" && (
        <>
        {/* Messages com altura flexível e scroll */}
        <div
          ref={messagesContainerRef}
          className={`flex-1 min-h-0 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500 relative transition-all duration-300 ${chatContainerClass} ${
            !isEmptyChat ? 'p-4' : ''
          }`}
          style={{scrollBehavior: 'smooth'}}
          onScroll={checkNewMessageIndicator}
        >
          {/* Empty state with PromptSuggestionsDock */}
          {isEmptyChat && (
            <div className={`text-left pt-8 ${messagesContainerClass}`}>
              <div className="mb-8">
                <LIAIcon size="xl" className="mb-4" />
                <h2 className="text-3xl font-semibold mb-3" style={{color: 'var(--gray-800)'}}>
                  Oi, eu sou a <span className="text-gray-700">LIA</span>.
                </h2>
                <p className="text-base mb-8" style={{color: 'var(--gray-500)'}}>
                  Sua assistente de recrutamento inteligente. Qual das tarefas abaixo quer que eu execute para você?
                </p>
                
                <PromptSuggestionsDock
                  onSelect={(command) => setInput(command)}
                  isEmpty={true}
                />
              </div>
            </div>
          )}
          
          {/* Container de mensagens */}
          {!isEmptyChat && (
            <>
              {/* Notificação de campos vazios */}
              {emptyFieldNotifications.hasPendingNotifications && emptyFieldNotifications.currentNotification && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-1 max-w-4xl">
                    <div className="flex-shrink-0 pt-4">
                      <LIAIcon size="md" />
                    </div>
                    <div className="rounded-md p-5 flex-1" style={{backgroundColor: 'var(--gray-100)'}}>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium lia-name -ml-1" style={{color: 'var(--gray-800)'}}>
                          Lia
                        </span>
                        <Badge variant="secondary" className="text-xs border-0">
                          Pendência
                        </Badge>
                      </div>
                      <EmptyFieldNotificationMessage
                        notification={emptyFieldNotifications.currentNotification}
                        onAction={handleEmptyFieldAction}
                        onSuggestionAccepted={handleSuggestionAccepted}
                        onSuggestionRejected={handleSuggestionRejected}
                        suggestion={currentSuggestion}
                        isLoadingSuggestion={isLoadingSuggestion}
                      />
                    </div>
                  </div>
                </div>
              )}

              <ChatMessageList
                messages={messages}
                isLoading={isLoading}
                searchTerm={searchTerm}
                currentMessageIndex={currentMessageIndex}
                messagesContainerClass={messagesContainerClass}
                availableCredits={availableCredits}
                onRenderChatCard={renderChatCard}
                onHighlightSearchTerm={highlightSearchTerm}
                getRelativeTime={getRelativeTime}
                onLoadMoreCandidates={handleLoadMoreCandidates}
                onSendMessage={handleSendMessage}
              />
            </>
          )}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start gap-1 max-w-4xl">
                <div className="flex-shrink-0 pt-4">
                  <LIAIcon size="md" />
                </div>
                <div className="rounded-md p-5 flex-1" style={{backgroundColor: 'var(--gray-100)'}}>
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm" style={{color: 'var(--gray-500)'}}>
                      LIA está digitando...
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />

          {/* Indicador de Nova Mensagem */}
          {newMessageIndicator && (
            <div className="absolute bottom-4 right-4">
              <Button
                onClick={scrollToBottom}
                className="rounded-full"
                size="sm"
                style={{backgroundColor: 'var(--gray-800)',
                  color: 'var(--white)'}}
              >
                <ChevronDown className="w-4 h-4 mr-1" />
                Nova mensagem
              </Button>
            </div>
          )}
        </div>

        {/* Input Card */}
        <div className="p-6 flex-shrink-0" style={{backgroundColor: 'var(--gray-50)'}}>
          <div className={inputContainerClass}>
            {/* Context Pills */}
            {contextData && contextData.data?.totalCount > 0 && (
              <div className="mb-4">
                <ContextPill
                  icon={<MapPin className="w-3.5 h-3.5" />}
                  primaryText={contextData.title}
                  secondaryText={
                    contextData.type === 'candidate-suggestions'
                      ? `${contextData.data.totalCount} candidatos`
                      : contextData.type
                  }
                  onDismiss={() => {
                    setContextData(null)
                    setIsPanelOpen(false)
                  }}
                />
              </div>
            )}

            {/* Smart Search Input */}
            {isSmartSearchMode ? (
              <SmartSearchInput
                value={smartSearchQuery}
                onChange={setSmartSearchQuery}
                onSubmit={handleSmartSearchSubmit}
                onCancel={handleSmartSearchCancel}
                onOpenFilters={() => setIsFiltersModalOpen(true)}
                isLoading={isLoading}
                placeholder="Desenvolvedores Python com 5+ anos em São Paulo..."
                activeFiltersCount={getActiveFiltersCount()}
              />
            ) : (
              <div className="rounded-md p-5 space-y-4" style={{backgroundColor: 'var(--white)'}}>
                
                {/* Sugestões Rápidas */}
                {(getQuickSuggestions().length > 0 || (hasSearchResults && contextData && getQuickActions().length > 0)) && !isLoading && searchFlow.flowState !== "collecting_profile" && (
                  <div className="space-y-3">
                    {getQuickSuggestions().length > 0 && searchFlow.flowState !== "collecting_profile" && (
                      <div className="flex flex-wrap gap-2">
                        {getQuickSuggestions().map((suggestion, index) => (
                          <Button
                            key={index}
                            size="sm"
                            onClick={() => setInput(suggestion)}
                            className="text-xs h-7 px-3 transition-all duration-200 hover:scale-105 text-gray-950 dark:text-gray-50 border border-gray-200" style={{backgroundColor: 'var(--gray-50)'}}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    )}
                    
                    {hasSearchResults && contextData && contextData.data?.totalCount > 0 && getQuickActions().length > 0 && (
                      <QuickActionChips actions={getQuickActions()} />
                    )}
                  </div>
                )}

                {/* File Validation Error Toast */}
                {fileValidationError && (
                  <div className="flex items-start gap-2 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-top-2 duration-300 bg-status-error/10 border border-status-error/30"
                  >
                    <AlertTriangle className="w-4 h-4 text-status-error mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-status-error">Arquivo inválido</p>
                      <p className="text-xs text-status-error whitespace-pre-line mt-0.5">{fileValidationError}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Formatos aceitos: PDF, DOC, DOCX, TXT, CSV, XLSX, PNG, JPG (máx. {MAX_FILE_SIZE_MB}MB)
                      </p>
                    </div>
                    <button
                      onClick={() => setFileValidationError(null)}
                      className="p-1 rounded-full hover:bg-status-error/15 transition-colors"
                    >
                      <X className="w-3.5 h-3.5 text-status-error" />
                    </button>
                  </div>
                )}

                {/* Attached Files Preview */}
                {attachedFiles.length > 0 && (
                  <div className="flex flex-wrap gap-2 p-2 rounded-md mb-2" style={{backgroundColor: 'var(--gray-100)'}}>
                    {attachedFiles.map((file, index) => {
                      const fileSizeKB = (file.size / 1024).toFixed(0)
                      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1)
                      const sizeDisplay = file.size > 1024 * 1024 ? `${fileSizeMB}MB` : `${fileSizeKB}KB`
                      
                      return (
                        <div 
                          key={index}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
                          style={{backgroundColor: 'var(--white)',
                            border: '1px solid var(--gray-300)'}}
                        >
                          <FileText className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                          <span className="max-w-[150px] truncate" style={{color: 'var(--gray-800)'}}>
                            {file.name}
                          </span>
                          <span className="text-xs" style={{color: 'var(--gray-400)'}}>
                            ({sizeDisplay})
                          </span>
                          <button
                            onClick={() => handleRemoveFile(index)}
                            className="p-0.5 rounded-full hover:bg-gray-200 transition-colors"
                          >
                            <X className="w-3 h-3" style={{color: 'var(--gray-500)'}} />
                          </button>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Recording Indicator */}
                {isRecording && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-pulse bg-status-error/10 border border-status-error/30">
                    <div className="w-3 h-3 bg-status-error rounded-full animate-ping" />
                    <span className="text-sm font-medium text-status-error">
                      Gravando... {recordingTime}s
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={stopRecording}
                      className="ml-auto text-xs h-7 border-red-500/50 text-status-error"
                    >
                      <X className="w-3 h-3 mr-1" />
                      Cancelar
                    </Button>
                  </div>
                )}

                {/* Audio Ready Indicator */}
                {audioBlob && !isRecording && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300 bg-gray-200/30 border border-wedo-cyan/30"
                  >
                    <div className="flex items-center gap-2">
                      <Mic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-gray-700">
                          Áudio gravado ({recordingTime}s)
                        </span>
                        <span className="text-xs" style={{color: 'var(--gray-500)'}}>
                          Pronto para enviar junto com sua mensagem
                        </span>
                      </div>
                    </div>
                    <div className="ml-auto flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const url = URL.createObjectURL(audioBlob)
                          const audio = new Audio(url)
                          audio.play()
                        }}
                        className="text-xs h-7 border-wedo-cyan/50"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Ouvir
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setAudioBlob(null)}
                        className="text-xs h-7 border-status-error/50 text-status-error"
                      >
                        <X className="w-3 h-3 mr-1" />
                        Remover
                      </Button>
                    </div>
                  </div>
                )}

                {/* File Analysis Context Indicator */}
                {fileAnalysisContext && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300 bg-status-success/10 border border-status-success/30"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-status-success" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-status-success">
                          Arquivo analisado: {fileAnalysisContext.filename}
                        </span>
                        <span className="text-xs" style={{color: 'var(--gray-500)'}}>
                          A análise será enviada junto com sua próxima mensagem
                        </span>
                      </div>
                    </div>
                    <div className="ml-auto">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setFileAnalysisContext(null)}
                        className="text-xs h-7 border-status-error/50 text-status-error"
                      >
                        <X className="w-3 h-3 mr-1" />
                        Remover
                      </Button>
                    </div>
                  </div>
                )}

                {/* Indicador de ação pendente */}
                {activePendingAction && (
                  <div className="flex items-center gap-2 px-3 py-1.5 mb-2 rounded-md border text-xs bg-wedo-cyan/[0.08] border-wedo-cyan/[0.35]"
                    style={{color: 'var(--gray-500)'}}
                  >
                    <span className="w-2 h-2 rounded-full bg-wedo-cyan animate-pulse shrink-0" />
                    <span>
                      Ação em andamento: <strong style={{color: 'var(--gray-800)'}}>{activePendingAction.intent.replace(/_/g, " ")}</strong>
                    </span>
                    <button
                      className="ml-auto text-xs hover:opacity-80 transition-opacity"
                      style={{color: 'var(--gray-400)'}}
                      onClick={() => handleSendMessage("cancelar")}
                      type="button"
                    >
                      × cancelar
                    </button>
                  </div>
                )}

                {/* Input com botões */}
                <div className="flex items-center space-x-2">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyPress}
                      placeholder={getPlaceholderText()}
                      className="w-full resize-none rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200" style={{backgroundColor: 'var(--gray-50)', color: 'var(--gray-800)'}}
                      rows={1}
                    />
                  </div>

                  <div className="flex items-center space-x-1">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={activateSmartSearch}
                      className="transition-all duration-200 hover:scale-105"
                      style={{color: 'var(--gray-500)'}}
                      title="Busca avançada de candidatos"
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                    
                    <FileUploadButton
                      onFilesSelected={handleFilesSelected}
                      onFileAnalyzed={handleFileAnalyzed}
                      disabled={isLoading}
                      maxFiles={3}
                      showPreview={false}
                      autoAnalyze={true}
                    />
                    
                    <AudioRecordButton
                      onTranscription={handleAudioTranscription}
                      onRecordingStart={handleAudioRecordingStart}
                      onRecordingEnd={handleAudioRecordingEnd}
                      disabled={isLoading}
                      maxDuration={60}
                    />
                    
                    <Button
                      onClick={() => handleSendMessage()}
                      disabled={!input.trim() || isLoading || emptyFieldNotifications.hasPendingNotifications}
                      size="sm"
                      className="transition-all duration-200 hover:scale-105 disabled:hover:scale-100 disabled:opacity-50"
                      style={{backgroundColor: 'var(--gray-800)',
                        color: 'var(--white)'}}
                      title={emptyFieldNotifications.hasPendingNotifications ? "Resolva as pendências acima para continuar" : undefined}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
        </>
        )}

        {/* Tab Content: Centro de Controle */}
        {activeTab === "controle" && (
          <AgentControlCenter />
        )}
      </div>

      {/* Context Panel */}
      <ChatContextPanel
        contextData={contextData}
        isPanelOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        onPipelineAction={handlePipelineAction}
      />

      {/* Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        commands={commandItems}
        placeholder="Buscar ação ou digitar comando..."
      />

      {/* Interview Scheduling Modal */}
      {selectedCandidateForScheduling && (
        <InterviewSchedulingModal
          open={isSchedulingModalOpen}
          onOpenChange={setIsSchedulingModalOpen}
          candidateName={selectedCandidateForScheduling.name}
          candidateEmail={selectedCandidateForScheduling.email}
          candidateId={selectedCandidateForScheduling.id}
          jobTitle={selectedCandidateForScheduling.job_title}
          jobVacancyId={selectedCandidateForScheduling.job_vacancy_id}
          userName="Ana Silva"
          userEmail="ana.silva@wedotalent.com"
        />
      )}

      {/* Candidate Detail Sidebar */}
      <CandidateDetailSidebar
        candidate={selectedCandidateForDetail}
        open={isCandidateDetailOpen}
        onClose={() => {
          setIsCandidateDetailOpen(false)
          setSelectedCandidateForDetail(null)
        }}
        onAddToJob={handleAddCandidateToJob}
        onScheduleInterview={(candidateId) => {
          if (selectedCandidateForDetail) {
            handleSendMessage(`Agendar entrevista com ${selectedCandidateForDetail.name}`)
            setIsCandidateDetailOpen(false)
          }
        }}
        onFavorite={(candidateId) => {
          handleSendMessage(`Adicionar candidato ${selectedCandidateForDetail?.name || candidateId} aos favoritos`)
        }}
        onSaveToBase={handleSaveToBase}
      />

      {/* Credit Confirmation Dialog */}
      <CreditConfirmationDialog
        open={isCreditDialogOpen}
        onClose={() => {
          setIsCreditDialogOpen(false)
        }}
        onConfirm={handleConfirmPearchSearch}
        query={pendingPearchSearch?.query || ""}
        pearchType="pro"
        limit={10}
        costPerCandidate={5}
        totalEstimated={50}
        breakdown={{
          base: 5,
          insights: 0,
          emails: 2,
          phones: 14,
          freshness: 0
        }}
        creditsRemaining={availableCredits}
      />

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={isFiltersModalOpen}
        onClose={() => setIsFiltersModalOpen(false)}
        onApply={handleApplyFilters}
        initialFilters={activeSearchFilters}
        estimatedMatches={1000000}
      />

      {/* Floating Prompt Suggestions Dock */}
      {!isEmptyChat && (
        <PromptSuggestionsDock
          onSelect={(command) => setInput(command)}
          isEmpty={false}
        />
      )}

      {/* UI Actions Side Panel Container */}
      <SidePanelContainer
        isOpen={uiActions.isPanelOpen}
        panelType={uiActions.activePanelType}
        title={uiActions.activePanelTitle}
        initialData={uiActions.activePanelData}
        isLoading={uiActions.isLoading}
        onClose={uiActions.closePanel}
        onSubmit={uiActions.submitPanel}
      />

      {/* Debug Buttons for Testing UI Actions Panels */}
      {process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_UI_ACTIONS_DEBUG === 'true' && (
        <div className="fixed bottom-24 right-4 z-50 flex flex-col gap-2">
          <div className="bg-gray-900/90 backdrop-blur-sm rounded-md p-2 border border-gray-700">
            <div className="text-xs text-gray-600 mb-2 px-2">Debug: UI Actions</div>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => uiActions.openPanel("compensation_benefits", {
                  salary_min: 15000,
                  salary_max: 25000,
                  benefits: []
                }, "Remuneração e Benefícios")}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-md transition-colors"
              >
                Debug Panel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
