"use client"

import { useState, Suspense, useEffect } from "react"
import React from "react"
import { useRouter } from "next/navigation"
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts"

import { TopBar } from "@/components/top-bar"
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
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { hasModuleAccess } from "@/utils/license-manager"
import { useAuth } from "@/contexts/auth-context"
import { useRecentItems, type RecentItem } from "@/hooks/use-recent-items"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSplitPanel } from "@/components/lia-float/LiaSplitPanel"
import { GlobalSearchModal } from "@/components/global-search-modal"

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
  const { isAuthenticated, user, logout } = useAuth()
  const router = useRouter()
  const { recentItems, addRecentItem, removeRecentItem, clearAll: clearRecentItems } = useRecentItems()
  const { open: openFloat, splitView, setContextPage } = useLiaFloat()

  useEffect(() => {
    setContextPage(currentPage)
    if (currentPage !== "Chat LIA") {
      setPendingChatConversationId(null)
    }
  }, [currentPage, setContextPage])

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
      case "Configurações":
        return <SettingsPageEnhanced />
      default:
        return <CandidatesPage />
    }
  }

  return (
    <div data-dashboard-shell className="h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex overflow-hidden">
      <Sidebar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        recentItems={recentItems}
        onRecentItemClick={handleRecentItemClick}
        onRecentItemRemove={removeRecentItem}
        onRecentItemsClear={clearRecentItems}
        onShowSearch={() => setShowGlobalSearch(true)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar 
          onNavigate={handleNavigate} 
          currentPage={currentPage}
        />

        <div className="flex-1 min-h-0 overflow-hidden flex">
          <div className="flex-1 min-w-0 overflow-hidden">
            {renderCurrentPage()}
          </div>
          {splitView.active && (
            <LiaSplitPanel onNavigate={page => {
              setCurrentPage(page)
            }} />
          )}
        </div>
      </div>

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
