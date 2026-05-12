"use client"

import { useState, Suspense, useEffect, useRef } from "react"
import React from "react"
import { useRouter } from "next/navigation"
import { useLocale } from "next-intl"
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
import {
  pathFromLabel,
  isDashboardPageLabel,
  type DashboardPageLabel,
} from "@/lib/navigation/routes"

type CurrentPage = DashboardPageLabel | `upgrade-${string}`

/**
 * Normalize legacy/ad-hoc page labels emitted by older callers
 * ("Painel de Controle", "Chat LIA", "Tarefas", "Visão do Funil") to the
 * canonical `DashboardPageLabel` union. Unknown labels fall back to
 * "Conversar" so we never put `currentPage` in a state the switch can't
 * render.
 */
const LEGACY_LABEL_MAP: Record<string, DashboardPageLabel> = {
  "Painel de Controle": "Decidir",
  "Chat LIA": "Conversar",
  "Tarefas": "Decidir",
  "Visão do Funil": "Recrutar",
}

function normalizePageLabel(raw: string): CurrentPage {
  if (raw.startsWith("upgrade-")) return raw as `upgrade-${string}`
  const mapped = LEGACY_LABEL_MAP[raw] ?? raw
  if (isDashboardPageLabel(mapped)) return mapped
  if (process.env.NODE_ENV !== "production") {
    // Surface accidental label drift early — silent fallback to "Conversar"
    // in prod is intentional, but in dev/test we want the regression visible.
    console.warn(
      `[dashboard-app] normalizePageLabel: unknown page label "${raw}" — falling back to "Conversar". ` +
      `Add it to PAGE_PATHS or SPA_ONLY_PAGE_LABELS in src/lib/navigation/routes.ts.`,
    )
  }
  return "Conversar"
}

interface DashboardAppProps {
  initialPage?: string
  children?: React.ReactNode
}

export function DashboardApp({ initialPage = "Conversar", children }: DashboardAppProps) {
  const [currentPage, setCurrentPage] = useState<CurrentPage>(normalizePageLabel(initialPage))
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
  const locale = useLocale()

  useEffect(() => {
    setContextPage(currentPage)
    if (currentPage !== "Conversar") {
      setPendingChatConversationId(null)
      const stored = localStorage.getItem("lia-chat-mode")
      const currentMode = stored === "floating" ? "floating" : "sidebar"
      window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: currentMode } }))
      openFloat()
    }
  }, [currentPage, setContextPage, openFloat])

  useEffect(() => {
    if (splitView.active && splitView.page) {
      setCurrentPage(normalizePageLabel(splitView.page))
    }
  }, [splitView.active, splitView.page])

  // BUG-09: ao sair do modo fullscreen do chat, voltar para a página onde o
  // usuário estava antes — não mais "Decidir" hardcoded. Guardamos a última
  // página não-"Conversar" em um ref para restaurar ao fechar o fullscreen.
  const previousPageBeforeChatRef = useRef<CurrentPage>("Decidir")
  useEffect(() => {
    if (currentPage !== "Conversar") {
      previousPageBeforeChatRef.current = currentPage
    }
  }, [currentPage])

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ conversationId?: string }>).detail
      setPendingChatConversationId(detail?.conversationId ?? null)
      setCurrentPage("Conversar")
    }
    window.addEventListener("lia:navigate-chat-page", handler)
    return () => window.removeEventListener("lia:navigate-chat-page", handler)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get("page") === "chat-lia") {
      setCurrentPage("Conversar")
      params.delete("page")
      const qs = params.toString()
      window.history.replaceState({}, "", window.location.pathname + (qs ? `?${qs}` : ""))
    }
  }, [])

  useEffect(() => {
    const handler = () => {
      if (currentPage === "Conversar") {
        // Restaura a última página visitada antes de entrar no Conversar fullscreen
        // (BUG-09 — antes ia para "Decidir" independente de onde o usuário estava).
        setCurrentPage(previousPageBeforeChatRef.current || "Decidir")
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
        setCurrentPage(normalizePageLabel(page))
        // Open sidebar if not already open
        openFloat()
      }
    }
    window.addEventListener("lia:navigation-hint", handler)
    return () => window.removeEventListener("lia:navigation-hint", handler)
  }, [openFloat])

  const handleNavigate = (page: string) => {
    if (page === "Sair") {
      logout()
      router.push(`/${locale}/login`)
      return
    }
    const normalized = normalizePageLabel(page)
    setCurrentPage(normalized)

    const route = pathFromLabel(normalized)
    if (route) {
      router.push(`/${locale}${route}`)
    }
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
      setCurrentPage("Conversar")
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
      case "Conversar":
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
      case "Decidir":
        return <TasksPage onNavigate={handleNavigate} />
      case "Estúdio de Agentes":
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
      case "Recrutar":
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
            {children ?? renderCurrentPage()}
          </div>
          {splitView.active && (
            <LiaSplitPanel onNavigate={page => {
              setCurrentPage(normalizePageLabel(page))
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
