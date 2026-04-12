"use client"

import { useState, Suspense, useEffect } from "react"
import React from "react"
import { useRouter } from "next/navigation"
import { useKeyboardShortcuts } from "@/hooks/shared/use-keyboard-shortcuts"

import { Sidebar } from "@/components/sidebar"
import { CandidatesPage } from "@/components/pages/candidates-page"
import { ChatPage } from "@/components/pages/chat-page"
import { JobsPage } from "@/components/pages/jobs-page"
import { TasksPage } from "@/components/pages/tasks-page"
import { IndicatorsPage } from "@/components/pages/indicators-page"
import { CommunicationHub } from "@/components/settings/CommunicationHub"
import { TemplatesPage } from "@/components/pages/templates-page"
import LiaLibraryPage from "@/components/pages/lia-library-page"
import SettingsPageEnhanced from "@/components/pages/settings-page-enhanced"
import AgentStudioPage from "@/components/pages-agent-studio/AgentStudioPage"
import CalibrationCardModal from "@/components/pages-agent-studio/CalibrationCardModal"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { hasModuleAccess } from "@/utils/license-manager"
import { useAuth } from "@/contexts/auth-context"
import { useRecentItems, type RecentItem } from "@/hooks/shared/use-recent-items"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSplitPanel } from "@/components/lia-float/LiaSplitPanel"
import { DashboardChatPanel } from "@/components/unified-chat"
import { GlobalSearchModal } from "@/components/global-search-modal"
import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"
import { ModulesPage } from "@/components/pages/modules-page"

interface DashboardAppProps {
  initialPage?: string
}

export function DashboardApp({ initialPage = "Chat LIA" }: DashboardAppProps) {
  const [currentPage, setCurrentPage] = useState(initialPage === "Painel de Controle" ? "Tarefas" : initialPage)
  const [showGlobalSearch, setShowGlobalSearch] = useState(false)
  const [pendingChatOpen, setPendingChatOpen] = useState<{ mode: 'general' | 'job-creation' } | null>(null)
  const [pendingChatConversationId, setPendingChatConversationId] = useState<string | null>(null)
  const [pendingJobOpen, setPendingJobOpen] = useState<{ jobId: string; jobTitle: string } | null>(null)
  const [pendingCandidateOpen, setPendingCandidateOpen] = useState<{ candidateId: string; candidateName: string } | null>(null)
  const [calibratingAgentId, setCalibratingAgentId] = useState<string | null>(null)
  const [agentStudioRefreshKey, setAgentStudioRefreshKey] = useState(0)
  const { isAuthenticated, user, logout } = useAuth()
  const router = useRouter()
  const { recentItems, addRecentItem, removeRecentItem, clearAll: clearRecentItems } = useRecentItems()
  const { open: openFloat, splitView, setContextPage } = useLiaFloat()

  useEffect(() => {
    setContextPage(currentPage)
    if (currentPage !== "Chat LIA") {
      setPendingChatConversationId(null)
      const stored = localStorage.getItem("lia-chat-mode")
      const currentMode = stored === "floating" ? "floating" : "sidebar"
      window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: currentMode } }))
      openFloat()
    }
  }, [currentPage, setContextPage, openFloat])

  useEffect(() => {
    if (splitView.active && splitView.page) {
      const normalized = splitView.page === "Painel de Controle" ? "Tarefas" : splitView.page
      setCurrentPage(normalized)
    }
  }, [splitView.active, splitView.page])

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ conversationId?: string }>).detail
      setPendingChatConversationId(detail?.conversationId ?? null)
      setCurrentPage("Chat LIA")
    }
    window.addEventListener("lia:navigate-chat-page", handler)
    return () => window.removeEventListener("lia:navigate-chat-page", handler)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get("page") === "chat-lia") {
      setCurrentPage("Chat LIA")
      params.delete("page")
      const qs = params.toString()
      window.history.replaceState({}, "", window.location.pathname + (qs ? `?${qs}` : ""))
    }
  }, [])

  useEffect(() => {
    const handler = () => {
      if (currentPage === "Chat LIA") {
        setCurrentPage("Tarefas")
      }
    }
    window.addEventListener("lia:leave-fullscreen-chat", handler)
    return () => window.removeEventListener("lia:leave-fullscreen-chat", handler)
  }, [currentPage])

  // Handle navigation hints from UnifiedChat (auto-navigate when LIA detects intent)
  useEffect(() => {
    const handler = (e: Event) => {
      const { page } = (e as CustomEvent<{ page: string; hint: string }>).detail
      if (page) {
        const normalized = page === "Painel de Controle" ? "Tarefas" : page
        setCurrentPage(normalized)
        // Open sidebar if not already open
        openFloat()
      }
    }
    window.addEventListener("lia:navigation-hint", handler)
    return () => window.removeEventListener("lia:navigation-hint", handler)
  }, [openFloat])

  const handleNavigate = (page: string) => {
    if (page === "Ajuda") {
      router.push("/ajuda")
      return
    }
    if (page === "Sair") {
      logout()
      router.push("/login")
      return
    }
    const normalized = page === "Painel de Controle" ? "Tarefas" : page
    setCurrentPage(normalized)
  }

  const handleRecentItemClick = (item: RecentItem) => {
    if (item.type === 'vaga' && item.meta?.jobId) {
      setPendingJobOpen(null)
      setTimeout(() => {
        setPendingJobOpen({ jobId: item.meta!.jobId!, jobTitle: item.title })
        setCurrentPage("Vagas")
      }, 0)
    } else if (item.type === 'candidato' && item.meta?.candidateId) {
      setPendingCandidateOpen(null)
      setTimeout(() => {
        setPendingCandidateOpen({ candidateId: item.meta!.candidateId!, candidateName: item.title })
        setCurrentPage("Funil de Talentos")
      }, 0)
    } else if (item.type === 'chat') {
      const convId = item.meta?.conversationId as string | undefined
      openFloat(convId)
    }
  }

  useKeyboardShortcuts({
    onAIActivate: () => {
    },
    onVoiceActivate: () => {
    },
    onLibraryOpen: () => {
      setCurrentPage("Biblioteca LIA")
    },
    onChatOpen: () => {
      setCurrentPage("Chat LIA")
    }
  })

  
  const renderCurrentPage = () => {
    if (currentPage.startsWith('upgrade-')) {
      const moduleId = currentPage.replace('upgrade-', '')
      return (
        <ModuleUpsell
          moduleId={moduleId}
          title="Módulo Premium"
          description="Esta funcionalidade requer um módulo premium"
          onUpgrade={() => {
            alert('Redirecionando para processo de upgrade...')
          }}
        />
      )
    }

    switch (currentPage) {
      case "Chat LIA":
        return <ChatPage initialConversationId={pendingChatConversationId} />
      case "Funil de Talentos":
        return <CandidatesPage onAddRecentItem={addRecentItem} pendingCandidateOpen={pendingCandidateOpen} onCandidateOpened={() => setPendingCandidateOpen(null)} />
      case "Vagas":
        return <JobsPage onNavigate={handleNavigate} onAddRecentItem={addRecentItem} pendingChatOpen={pendingChatOpen as any} onChatOpened={() => setPendingChatOpen(null)} pendingJobOpen={pendingJobOpen} onJobOpened={() => setPendingJobOpen(null)} />
      case "Indicadores":
        return <IndicatorsPage />
      case "Central Comunicação":
        if (!hasModuleAccess('communication_center')) {
          return (
            <ModuleUpsell
              moduleId="communication_center"
              title="Central de Comunicação Omnichannel"
              description="Sistema unificado de comunicação multi-canal"
            />
          )
        }
        return <CommunicationHub />
      case "Biblioteca LIA":
        return <LiaLibraryPage onNavigate={handleNavigate} />
      case "Templates":
        return <TemplatesPage />
      case "Tarefas":
        return <TasksPage onNavigate={handleNavigate} />
      case "Agent Studio":
        return (
          <>
            <AgentStudioPage
              key={agentStudioRefreshKey}
              onStartCalibration={(agentId) => setCalibratingAgentId(agentId)}
              onNavigateToJob={(jobId) => {
                setPendingJobOpen({ jobId, jobTitle: "" })
                setCurrentPage("Vagas")
              }}
              onNavigateToPool={() => {
                setCurrentPage("Funil de Talentos")
              }}
            />
            {calibratingAgentId && (
              <CalibrationCardModal
                agentId={calibratingAgentId}
                isOpen={!!calibratingAgentId}
                onClose={() => setCalibratingAgentId(null)}
                onCalibrationComplete={() => {
                  setCalibratingAgentId(null)
                  setAgentStudioRefreshKey(k => k + 1)
                }}
              />
            )}
          </>
        )
      case "Visão do Pipeline":
        return <PipelineOverviewPage />
      case "Configurações":
        return <SettingsPageEnhanced />
      case "Módulos":
        return <ModulesPage />
      default:
        return <CandidatesPage />
    }
  }

  return (
    <div data-dashboard-shell className="h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex overflow-hidden">
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {currentPage}
      </div>
      <Sidebar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        recentItems={recentItems}
        onRecentItemClick={handleRecentItemClick}
        onRecentItemRemove={removeRecentItem}
        onRecentItemsClear={clearRecentItems}
        onShowSearch={() => setShowGlobalSearch(true)}
      />

      <main id="main-content" className="flex-1 flex flex-col overflow-hidden" aria-label={currentPage}>
        <div className="flex-1 min-h-0 overflow-hidden flex">
          <div className="flex-1 min-w-0 overflow-hidden">
            {renderCurrentPage()}
          </div>
          {splitView.active && (
            <LiaSplitPanel onNavigate={page => {
              setCurrentPage(page)
            }} />
          )}
          {/* UnifiedChat sidebar — inline flex child, pushes content (Replit-style) */}
          <DashboardChatPanel />
        </div>
      </main>

      <GlobalSearchModal
        isOpen={showGlobalSearch}
        onClose={() => setShowGlobalSearch(false)}
        onNavigate={(page: string) => {
          handleNavigate(page)
          setShowGlobalSearch(false)
        }}
      />
    </div>
  )
}
