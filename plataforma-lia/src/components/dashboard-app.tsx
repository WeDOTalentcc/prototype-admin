"use client"

import { useState, Suspense, useEffect, useRef } from "react"
import React from "react"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import { useNavGuardStore } from "@/stores/nav-guard-store"
import { useLocale } from "next-intl"
import { useLiaChatContext } from "@/contexts/lia-float-context"
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
import { getPersisted } from "@/lib/lia-persistence"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSplitPanel } from "@/components/lia-float/LiaSplitPanel"
import { DashboardChatPanel } from "@/components/unified-chat"
import { GlobalSearchModal } from "@/components/global-search-modal"
import { useProactiveHintsInChat } from "@/hooks/proactive/use-proactive-hints-in-chat"  // WT-2022 (chat-first)
import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"
import { ModulesPage } from "@/components/pages/modules-page"
import {
  pathFromLabel,
  isDashboardPageLabel,
  pageLabelFromViewParam,
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
  // Lowercase canonical names from backend (CanonicalPage enum) and frontend events
  "vagas": "Vagas",
  "funil": "Funil de Talentos",
  "recrutar": "Recrutar",
  "configuracoes": "Configurações",
  "configurações": "Configurações",
}

/**
 * Task #1165 — PT-BR free-form yes/no classifier for navigation proposals.
 *
 * Returns `"yes"` / `"no"` / `"ambiguous"`. The recruiter reply lives in a
 * regular chat turn, so we keep this purely client-side (no LLM round-trip)
 * — the supervisor classifier is reserved for wizard intent classification
 * (create_new / resume_draft / exit_wizard / ...). The patterns below
 * mirror the colloquial confirmations enumerated in `replit.md > User
 * Preferences > "A LIA deve entender variações naturais de confirmação"`.
 *
 * Exported for unit tests; callers should not depend on the boolean
 * encoding directly.
 */
export function classifyNavConfirmation(raw: string): "yes" | "no" | "ambiguous" {
  if (!raw) return "ambiguous"
  const t = raw.trim().toLowerCase()
  if (!t) return "ambiguous"
  // Negatives are matched FIRST so "agora não", "pode esperar", "deixa pra
  // lá" don't get swept up by the positive token "pode".
  if (/\b(n[aã]o|nao|nope|agora\s+n[aã]o|depois|mais\s+tarde|deixa(?:\s+pra\s+l[aá])?|cancela|esquece|pode\s+esperar)\b/.test(t)) {
    return "no"
  }
  if (/^(sim|s|yes|y|ok|okay)\b/.test(t)) return "yes"
  if (/\b(vamos|bora|claro|com\s+certeza|pode|pode\s+ir|me\s+leva|leva|manda|fechou|certo|positivo|isso|isso\s+a[ií])\b/.test(t)) {
    return "yes"
  }
  return "ambiguous"
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
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { recentItems, addRecentItem, removeRecentItem, clearAll: clearRecentItems } = useRecentItems()
  const { open: openFloat, splitView, setContextPage } = useLiaFloat()
  const { chatMessages, setChatMessages } = useLiaChatContext()

  // WT-2022 — sugestões proativas scheduler-driven entram como mensagem
  // conversacional + cards no chat unificado (aposenta o dropdown da lâmpada).
  useProactiveHintsInChat()
  const locale = useLocale()

  // Task #1165 — pending navigation proposal. Set when a `lia:navigation-hint`
  // arrives with `mode === "ask"` and the user is NOT already on the target
  // route. We post a LIA message asking for confirmation; the next user
  // message in chat is parsed as a free-form PT-BR yes/no (the supervisor
  // classifier is intentionally bypassed for this trivial UX confirm so we
  // don't pay an LLM call per chat turn). On `yes` we `router.push`; on
  // `no` we acknowledge and forget.
  const [pendingNavProposal, setPendingNavProposal] = useState<{
    page: string
    proposalMessageId: string
    /** id of the last user message present when the proposal was posted */
    seenLastUserMsgId: string | null
  } | null>(null)

  // Harness fix (2026-05-19) — track wizard activity to suppress navigation
  // proposals during an active wizard flow. Regression observed: while the
  // user was in the job-creation wizard chat, a NavigationProposal "Posso te
  // levar para o ambiente de vagas?" was injected — redundant (user already
  // creating a job) and triggered a false `exit_wizard` from the supervisor
  // classifier when the user answered "agora não" (canonical regression
  // 2026-05-19 — see wizard_supervisor_classifier.py REGRA CRÍTICA 2).
  const wizardLastActivityRef = useRef<number>(0)
  const WIZARD_ACTIVITY_TTL_MS = 5 * 60 * 1000
  useEffect(() => {
    const onWizardStage = () => {
      wizardLastActivityRef.current = Date.now()
    }
    window.addEventListener("lia:wizard-stage-payload", onWizardStage)
    return () => window.removeEventListener("lia:wizard-stage-payload", onWizardStage)
  }, [])
  const isWizardCurrentlyActive = (): boolean => {
    if (!wizardLastActivityRef.current) return false
    return Date.now() - wizardLastActivityRef.current < WIZARD_ACTIVITY_TTL_MS
  }

  useEffect(() => {
    setContextPage(currentPage)
    if (currentPage !== "Conversar") {
      setPendingChatConversationId(null)
      const stored = getPersisted<string>("lia-chat-mode", "sidebar")
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
    const handler = () => {
      setCurrentPage("Conversar")
    }
    window.addEventListener("lia:open-onboarding-chat", handler)
    return () => window.removeEventListener("lia:open-onboarding-chat", handler)
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

  // Fase A.2 (2026-06-06): deep-link in-shell da LIA. canonicalPageToUrl
  // emite `/?view=<label>` p/ abas SEM rota própria (Indicadores,
  // Templates, Módulos). Lemos o param e trocamos a aba diretamente —
  // depois limpamos o param p/ não re-disparar em refresh/navegação.
  useEffect(() => {
    const viewLabel = pageLabelFromViewParam(searchParams.get("view"))
    if (!viewLabel) return
    setCurrentPage(viewLabel)
    const params = new URLSearchParams(window.location.search)
    params.delete("view")
    const qs = params.toString()
    window.history.replaceState(
      {},
      "",
      window.location.pathname + (qs ? `?${qs}` : ""),
    )
  }, [searchParams])

  // Handle navigation hints from UnifiedChat / proactive router / wizard.
  //
  // Task #1165 — two modes:
  //   - `mode === "ask"`: the LIA proposes the transition in chat and waits
  //     for the recruiter's free-form PT-BR confirmation. We never push the
  //     router until the user agrees. If the user is already on the target
  //     route, the proposal is suppressed entirely (silent no-op).
  //   - default ("navigate"): legacy behaviour, kept for callers like
  //     `useProactiveActionRouter`, `TourController`, `DonePanel`,
  //     `BibliotecaLiaRouteClient` and `NavigationHintCard` that issued the
  //     event directly without the `ask` semantic.
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ page: string; hint?: string; mode?: "ask" | "navigate" }>).detail
      const { page, hint, mode } = detail || ({} as { page?: string })
      if (!page) return

      if (mode === "ask") {
        // Harness fix (2026-05-19) — silent drop when a wizard flow is
        // currently active. NavigationProposals during an active wizard
        // (e.g. "vamos te levar para Vagas?" while the user is creating
        // a job via chat wizard) are redundant and trigger false
        // exit_wizard classifications when the user answers "agora não".
        // See wizard_supervisor_classifier.py REGRA CRÍTICA 2 +
        // wizard_session_service.py _generate_fallback_reply guard.
        if (isWizardCurrentlyActive()) {
          return
        }
        const targetPath = pathFromLabel(normalizePageLabel(page))
        if (targetPath && pathname?.endsWith(targetPath)) {
          // Already on the target route — silently drop the proposal.
          return
        }
        const proposalText =
          page === "Vagas"
            ? `Posso te levar para o ambiente de vagas para continuar por lá? (responda "sim" ou "agora não")`
            : `Posso te levar para ${page}? (responda "sim" ou "agora não")`
        const proposalId = `lia-${Date.now()}-nav-proposal`
        const lastUser = [...chatMessages].reverse().find((m) => m.sender === "user")
        setChatMessages((prev) => [
          ...prev,
          {
            id: proposalId,
            sender: "lia" as const,
            content: proposalText,
            timestamp: new Date().toISOString(),
          },
        ])
        setPendingNavProposal({
          page,
          proposalMessageId: proposalId,
          seenLastUserMsgId: lastUser?.id ?? null,
        })
        openFloat()
        return
      }

      // Legacy mode — direct navigation as before.
      setCurrentPage(normalizePageLabel(page))
      openFloat()
      void hint
    }
    window.addEventListener("lia:navigation-hint", handler)
    return () => window.removeEventListener("lia:navigation-hint", handler)
  }, [openFloat, pathname, chatMessages, setChatMessages])

  // Task #1165 — observe the chat for the recruiter's reply to a pending
  // navigation proposal. The first user message posted AFTER the proposal
  // is parsed for a positive ("sim", "vamos", "pode", "bora", "claro",
  // "ok") or negative ("não", "agora não", "depois", "deixa pra lá")
  // confirmation. On positive we push the router and open the float; on
  // negative we just acknowledge. Anything else (e.g. the user keeps
  // talking about the JD) is ignored — the proposal expires silently on
  // the next hint.
  useEffect(() => {
    if (!pendingNavProposal) return
    const lastUser = [...chatMessages].reverse().find((m) => m.sender === "user")
    if (!lastUser) return
    if (lastUser.id === pendingNavProposal.seenLastUserMsgId) return
    const verdict = classifyNavConfirmation(lastUser.content)
    if (verdict === "yes") {
      const route = pathFromLabel(normalizePageLabel(pendingNavProposal.page))
      if (route) {
        router.push(`/${locale}${route}`)
      }
      setCurrentPage(normalizePageLabel(pendingNavProposal.page))
      setPendingNavProposal(null)
    } else if (verdict === "no") {
      setChatMessages((prev) => [
        ...prev,
        {
          id: `lia-${Date.now()}-nav-ack`,
          sender: "lia" as const,
          content: "Combinado — seguimos por aqui.",
          timestamp: new Date().toISOString(),
        },
      ])
      setPendingNavProposal(null)
    }
    // Ambiguous reply: leave proposal pending until next user message.
  }, [chatMessages, pendingNavProposal, router, locale, setChatMessages])

  const handleNavigate = (page: string) => {
    if (page === "Sair") {
      logout()
      router.push(`/${locale}/login`)
      return
    }
    const normalized = normalizePageLabel(page)
    const proceed = () => {
      setCurrentPage(normalized)
      const route = pathFromLabel(normalized)
      if (route) {
        router.push(`/${locale}${route}`)
      }
    }
    // #6 guard: pagina ativa (ex.: funil com candidatos globais nao salvos)
    // registra um guard; se ativo, adiamos a navegacao ate o usuario confirmar.
    const navGuard = useNavGuardStore.getState()
    if (navGuard.active) {
      navGuard.requestLeave(proceed)
      return
    }
    proceed()
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

      <main id="main-content" className="flex-1 flex flex-col overflow-hidden relative" aria-label={currentPage}>
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
