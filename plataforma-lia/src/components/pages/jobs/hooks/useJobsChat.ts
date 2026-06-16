"use client";

import type { Job } from "@/components/jobs";
import { useLiaFloat } from "@/contexts/lia-float-context";
import {
  useJobInsights,
  useLiaExpandedPrompt,
  useLiaSuggestions,
} from "@/hooks/ai/use-lia-suggestions";
import { useUnhandledUIActionListener } from "@/hooks/chat/useUnhandledUIActionListener";
import { useCompanyId } from "@/hooks/company/useCompanyId";
import { callOrchestratedJobsManagement } from "@/lib/api/kanban-assistant";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useAiPersona } from "@/hooks/company/use-ai-persona"

// ---------------------------------------------------------------------------
// useJobsChat
// Orquestra apenas o pipeline LIA (sugestões, insights, comandos para o
// orquestrador) e a abertura do chat flutuante unificado. Toda a UI de chat
// inline/lateral foi removida — o chat flutuante (LiaFloat) cobre as
// conversas com a LIA.
// ---------------------------------------------------------------------------

interface LiaOrchestratorMessage {
  id: string;
  type: "user" | "response";
  content: string;
  timestamp: number;
  agentUsed?: string;
  suggestedPrompts?: string[];
  action_executed?: boolean;
  action_result?: Record<string, unknown>;
  action_type?: string;
  needs_confirmation?: boolean;
  needs_params?: boolean;
  pending_action_id?: string;
}

interface UseJobsChatOptions {
  filteredJobs: Job[];
  allJobs: Job[];
  selectedJobsForBatch: Set<number>;
  onAddRecentItem?: (item: {
    id: string;
    type: "vaga" | "chat" | "candidato";
    title: string;
    subtitle?: string;
    meta?: Record<string, string | undefined>;
  }) => void;
  onChatOpened?: () => void;
  pendingChatOpen?: { mode: "general" | "job-creation" } | null;
  setActiveFilter?: (filter: string) => void;
  /**
   * Abre o JobCompareModal (ui_action `compare_jobs` do produtor BE
   * jobs_management_assistant_service). Recebe job_ids opcionais; sem ids usa a
   * selecao atual. Sem este callback a acao seria descartada em silencio (ghost).
   */
  openCompareModal?: (jobIds?: number[]) => void;
  loadBackendJobs: () => Promise<void>;
}

interface UseJobsChatReturn {
  state: {
    liaMessages: LiaOrchestratorMessage[];
    isLiaProcessing: boolean;
    jobsConversationId: string | undefined;
    orchestratorSuggestions: string[];
    dynamicSuggestions: ReturnType<typeof useLiaSuggestions>["suggestions"];
    suggestionsLoading: boolean;
    dynamicInsights: ReturnType<typeof useJobInsights>["insights"];
    insightsLoading: boolean;
    liaResponse: ReturnType<typeof useLiaExpandedPrompt>["response"];
    liaPromptLoading: boolean;
    followUpSuggestions: ReturnType<
      typeof useLiaExpandedPrompt
    >["followUpSuggestions"];
  };
  actions: {
    setLiaMessages: React.Dispatch<
      React.SetStateAction<LiaOrchestratorMessage[]>
    >;
    setJobsConversationId: (v: string | undefined) => void;
    setOrchestratorSuggestions: (v: string[]) => void;
    openGeneralChat: (initialMessage?: string) => void;
    openJobCreationChat: (initialMessage?: string) => void;
    handleAICommand: (command: string, action?: string) => Promise<void>;
    getContextualSuggestions: () => string[];
    refreshSuggestions: ReturnType<typeof useLiaSuggestions>["refresh"];
    generateInsights: ReturnType<typeof useJobInsights>["generateInsights"];
    sendLiaPrompt: ReturnType<typeof useLiaExpandedPrompt>["sendPrompt"];
  };
}

export function useJobsChat({
  filteredJobs,
  selectedJobsForBatch,
  onAddRecentItem,
  onChatOpened,
  pendingChatOpen,
  setActiveFilter,
  openCompareModal,
  loadBackendJobs,
}: UseJobsChatOptions): UseJobsChatReturn {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const { companyId: resolvedCompanyId } = useCompanyId();
  const { open: openGlobalChat } = useLiaFloat();

  const [liaMessages, setLiaMessages] = useState<LiaOrchestratorMessage[]>([]);
  const [isLiaProcessing, setIsLiaProcessing] = useState(false);
  const [jobsConversationId, setJobsConversationId] = useState<
    string | undefined
  >(undefined);
  const [orchestratorSuggestions, setOrchestratorSuggestions] = useState<
    string[]
  >([]);

  const {
    suggestions: dynamicSuggestions,
    loading: suggestionsLoading,
    refresh: refreshSuggestions,
  } = useLiaSuggestions("default", 6);
  const {
    insights: dynamicInsights,
    generateInsights,
    loading: insightsLoading,
  } = useJobInsights();
  const {
    sendPrompt: sendLiaPrompt,
    response: liaResponse,
    loading: liaPromptLoading,
    followUpSuggestions,
  } = useLiaExpandedPrompt();

  // Handle pendingChatOpen prop
  useEffect(() => {
    if (pendingChatOpen) {
      openGlobalChat();
      onChatOpened?.();
    }
  }, [pendingChatOpen, onChatOpened, openGlobalChat]);

  // ?action=create query-param handling is wired below, after openJobCreationChat
  // is defined, to avoid mount-order issues (effect referencing an undefined ref).
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // -------------------------------------------------------------------------
  // Floating chat openers (delegate to LiaFloat unified chat)
  // -------------------------------------------------------------------------
  const openGeneralChat = useCallback(
    (initialMessage?: string) => {
      const id = `chat-inline-${Date.now()}`;
      openGlobalChat();
      onAddRecentItem?.({
        id,
        type: "chat",
        title: initialMessage
          ? `Chat: ${initialMessage.slice(0, 40)}${initialMessage.length > 40 ? "..." : ""}`
          : `Chat com ${personaName}`,
        meta: { conversationId: id },
      });
    },
    [onAddRecentItem, openGlobalChat],
  );

  const openJobCreationChat = useCallback(
    (initialMessage?: string) => {
      const wizardId = `chat-wizard-${Date.now()}`;
      openGlobalChat();
      onAddRecentItem?.({
        id: wizardId,
        type: "chat",
        title: initialMessage
          ? `Criação: ${initialMessage.slice(0, 35)}${initialMessage.length > 35 ? "..." : ""}`
          : "Criação de Vaga",
        meta: { conversationId: wizardId },
      });
    },
    [onAddRecentItem, openGlobalChat],
  );

  // Handle ?action=create query param to open the job-creation chat.
  // Strips the param via router.replace after firing so a refresh does not
  // re-trigger and a subsequent click can re-fire by re-emitting the param.
  useEffect(() => {
    if (!searchParams) return;
    if (searchParams.get("action") !== "create") return;

    openJobCreationChat("Criar nova vaga");

    const params = new URLSearchParams(searchParams.toString());
    params.delete("action");
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname || "/");
  }, [searchParams, pathname, router, openJobCreationChat]);

  // -------------------------------------------------------------------------
  // handleAICommand (multi-agent orchestrator)
  // -------------------------------------------------------------------------
  const processLocalJobCommand = (command: string, jobs: Job[]): string => {
    const trimmed = command.trim().toLowerCase();
    const activeJobs = jobs.filter((j) => j.status === "Ativa");

    if (
      trimmed.includes("quantas vagas") ||
      trimmed.includes("vagas abertas") ||
      trimmed.includes("total de vagas")
    ) {
      return `📊 **Resumo de Vagas**\n\n• **Total:** ${jobs.length}\n• **Ativas:** ${activeJobs.length}\n• **Paralisadas:** ${jobs.filter((j) => j.status === "Paralisada").length}\n• **Concluídas:** ${jobs.filter((j) => j.status === "Concluída").length}`;
    }
    if (
      trimmed.includes("vagas urgentes") ||
      trimmed.includes("urgente") ||
      trimmed.includes("prioridade alta")
    ) {
      const urgentes = jobs.filter(
        (j) => j.priority === "alta" || j.urgencyLevel >= 4,
      );
      if (urgentes.length === 0)
        return `✅ **Nenhuma vaga urgente no momento**`;
      return `🚨 **${urgentes.length} Vaga(s) Urgente(s)**\n\n${urgentes
        .slice(0, 10)
        .map((j, i) => `${i + 1}. **${j.title}** - ${j.department}`)
        .join("\n")}`;
    }
    if (trimmed.includes("sem candidatos") || trimmed.includes("funil vazio")) {
      const empty = jobs.filter((j) => j.funnel.total === 0);
      if (empty.length === 0) return `✅ **Todas as vagas têm candidatos!**`;
      return `⚠️ **${empty.length} Vaga(s) sem Candidatos**\n\n${empty
        .slice(0, 10)
        .map((j, i) => `${i + 1}. **${j.title}**`)
        .join("\n")}`;
    }
    return `🤔 **Modo offline** — Para análises detalhadas tente novamente em instantes.\n\n💡 Comandos locais: "quantas vagas abertas", "vagas urgentes", "sem candidatos"`;
  };

  const handleAICommand = useCallback(
    async (command: string, action?: string) => {
      setLiaMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          type: "user",
          content: command,
          timestamp: Date.now(),
        },
      ]);
      setIsLiaProcessing(true);

      const jobs = filteredJobs;
      const jobsContext = {
        total: jobs.length,
        active: jobs.filter((j) => j.status === "Ativa").length,
        paused: jobs.filter((j) => j.status === "Paralisada").length,
        completed: jobs.filter((j) => j.status === "Concluída").length,
        urgent: jobs.filter((j) => j.priority === "alta" || j.urgencyLevel >= 4)
          .length,
        withoutCandidates: jobs.filter((j) => j.funnel.total === 0).length,
        totalCandidates: jobs.reduce((sum, j) => sum + j.funnel.total, 0),
        selectedJobs: Array.from(selectedJobsForBatch)
          .map((id) => {
            const job = jobs.find((j) => j.id === id);
            return job
              ? {
                  id: job.id,
                  title: job.title,
                  department: job.department,
                  status: job.status,
                }
              : null;
          })
          .filter(Boolean),
        topJobs: jobs.slice(0, 10).map((j) => ({
          id: j.id,
          title: j.title,
          department: j.department,
          status: j.status,
          priority: j.priority,
          candidatesTotal: j.funnel.total,
          candidatesInterview: j.funnel.interview,
          hired: j.funnel.hired,
          daysOpen: Math.floor(
            (Date.now() - new Date(j.openDate).getTime()) /
              (1000 * 60 * 60 * 24),
          ),
        })),
      };

      try {
        const selectedJobsArray = Array.from(selectedJobsForBatch)
          .map((id) => {
            const job = jobs.find((j) => j.id === id);
            return job
              ? {
                  id: job.id,
                  title: job.title,
                  department: job.department,
                  status: job.status,
                }
              : null;
          })
          .filter((j) => j !== null) as {
          id: number;
          title: string;
          department: string;
          status: string;
        }[];

        const response = await callOrchestratedJobsManagement({
          message: command,
          jobs_context: jobsContext,
          selected_jobs:
            selectedJobsArray.length > 0 ? selectedJobsArray : undefined,
          top_jobs: jobsContext.topJobs,
          conversation_history: liaMessages.slice(-10).map((m) => ({
            role: m.type === "user" ? "user" : "assistant",
            content: m.content,
          })),
          action: action || "general_query",
          conversation_id: jobsConversationId,
          company_id: resolvedCompanyId ?? "",
        });

        if (response.conversation_id)
          setJobsConversationId(response.conversation_id);

        setLiaMessages((prev) => [
          ...prev,
          {
            id: `response-${Date.now()}`,
            type: "response",
            content: response.content,
            timestamp: Date.now(),
            agentUsed: response.agent_used,
            suggestedPrompts: response.suggested_prompts,
            action_executed: response.action_executed,
            action_result: response.action_result,
            action_type: response.action_type,
            needs_confirmation: response.needs_confirmation,
            needs_params: response.needs_params,
            pending_action_id: response.pending_action_id,
          },
        ]);

        if (response.action_executed && response.action_result) {
          setTimeout(() => loadBackendJobs(), 500);
        }
        if (response.suggested_prompts?.length)
          setOrchestratorSuggestions(response.suggested_prompts);
        if (response.ui_action === "start_job_wizard") {
          openJobCreationChat(response.ui_action_params?.initial_message || "");
        } else if (
          response.ui_action === "filter_jobs" &&
          response.ui_action_params?.filter
        ) {
          setActiveFilter?.(response.ui_action_params.filter);
        } else if (response.ui_action === "compare_jobs") {
          const ids = response.ui_action_params?.job_ids;
          openCompareModal?.(Array.isArray(ids) ? ids : undefined);
        }
      } catch {
        const responseContent = processLocalJobCommand(command, jobs);
        setLiaMessages((prev) => [
          ...prev,
          {
            id: `response-${Date.now()}`,
            type: "response",
            content: responseContent,
            timestamp: Date.now(),
          },
        ]);
      } finally {
        setIsLiaProcessing(false);
      }
    },
    [
      filteredJobs,
      selectedJobsForBatch,
      liaMessages,
      jobsConversationId,
      loadBackendJobs,
      openJobCreationChat,
      setActiveFilter,
      openCompareModal,
      resolvedCompanyId,
    ],
  );

  // -------------------------------------------------------------------------
  // PR-D — handler isolado para reuso no listener cross-surface (UnifiedChat)
  // -------------------------------------------------------------------------
  const handleJobsUIAction = useCallback(
    (action: string, params: Record<string, unknown>) => {
      if (action === "start_job_wizard") {
        const initial = params?.initial_message;
        openJobCreationChat(typeof initial === "string" ? initial : "");
      } else if (
        action === "filter_jobs" &&
        typeof params?.filter === "string"
      ) {
        setActiveFilter?.(params.filter);
      } else if (action === "compare_jobs") {
        const ids = params?.job_ids;
        openCompareModal?.(Array.isArray(ids) ? (ids as number[]) : undefined);
      }
    },
    [openJobCreationChat, setActiveFilter, openCompareModal],
  );

  useUnhandledUIActionListener(handleJobsUIAction);

  // -------------------------------------------------------------------------
  // getContextualSuggestions
  // -------------------------------------------------------------------------
  const getContextualSuggestions = useCallback((): string[] => {
    const jobs = filteredJobs;
    const suggestions: string[] = [];
    const urgentCount = jobs.filter(
      (j) => j.priority === "alta" || j.urgencyLevel >= 4,
    ).length;
    if (urgentCount > 0)
      suggestions.push(
        `Analisar ${urgentCount} vaga${urgentCount > 1 ? "s" : ""} urgente${urgentCount > 1 ? "s" : ""}`,
      );
    const emptyPipeline = jobs.filter((j) => j.funnel.total === 0).length;
    if (emptyPipeline > 0)
      suggestions.push(
        `${emptyPipeline} vaga${emptyPipeline > 1 ? "s" : ""} sem candidatos`,
      );
    const now = Date.now();
    const upcomingDeadlines = jobs.filter((j) => {
      if (!j.deadline) return false;
      const days = Math.floor(
        (new Date(j.deadline).getTime() - now) / (1000 * 60 * 60 * 24),
      );
      return days >= 0 && days <= 7;
    }).length;
    if (upcomingDeadlines > 0) suggestions.push(`Vagas com deadline em 7 dias`);
    const pausedCount = jobs.filter((j) => j.status === "Paralisada").length;
    if (pausedCount > 0)
      suggestions.push(
        `Revisar ${pausedCount} vaga${pausedCount > 1 ? "s" : ""} paralisada${pausedCount > 1 ? "s" : ""}`,
      );
    if (suggestions.length === 0) {
      suggestions.push("Resumo das minhas vagas");
      suggestions.push("Performance dos últimos 30 dias");
    }
    if (
      suggestions.length < 4 &&
      !suggestions.some((s) => s.includes("Performance"))
    )
      suggestions.push("Performance das vagas ativas");
    if (suggestions.length < 4)
      suggestions.push("Top 5 vagas com mais candidatos");
    return suggestions.slice(0, 4);
  }, [filteredJobs]);

  return {
    state: {
      liaMessages,
      isLiaProcessing,
      jobsConversationId,
      orchestratorSuggestions,
      dynamicSuggestions,
      suggestionsLoading,
      dynamicInsights,
      insightsLoading,
      liaResponse,
      liaPromptLoading,
      followUpSuggestions,
    },
    actions: {
      setLiaMessages,
      setJobsConversationId,
      setOrchestratorSuggestions,
      openGeneralChat,
      openJobCreationChat,
      handleAICommand,
      getContextualSuggestions,
      refreshSuggestions,
      generateInsights,
      sendLiaPrompt,
    },
  };
}
