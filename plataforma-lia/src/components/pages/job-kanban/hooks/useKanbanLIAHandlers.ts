"use client";

import type { KanbanCandidate } from "@/components/kanban";
import type { CommunicationType } from "@/components/modals/unified-communication-modal";
import { useLiaChatContext } from "@/contexts/lia-float-context";
import { formatMessageTime } from "@/hooks/chat/lia-chat-connection-types";
import { useUnhandledUIActionListener } from "@/hooks/chat/useUnhandledUIActionListener";
import { useCompanyId } from "@/hooks/company/useCompanyId";
import { useOfferReviewFlow } from "@/hooks/offers/useOfferReviewFlow";
import {
  type KanbanAssistantRequest,
  type OrchestratedJobChatRequest,
  type OrchestratedJobChatResponse,
  callKanbanAssistant,
  callOrchestratedJobChat,
} from "@/lib/api/kanban-assistant";
import { isClearChatCommand } from "@/lib/chat-commands";
import { useCallback } from "react";
import type React from "react";
import { toast } from "sonner";

interface KanbanJob {
  id?: string | number;
  title?: string;
  department?: string;
  level?: string;
  requirements?: string[];
  location?: string;
  salary?: string;
  workModel?: string;
  deadline?: string;
  recruiter?: string;
}

interface KanbanTableCandidate {
  id: string | number;
  name: string;
  role?: string;
  currentCompany?: string;
  location?: string;
  score?: number;
  fitScore?: number;
  wsiScore?: number;
  wsiTechnical?: number;
  wsiBehavioral?: number;
  skills?: string[];
  experience?: string;
  stage?: string;
  subStatus?: string;
  daysInStage?: number;
  warnings?: number;
  email?: string;
  phone?: string;
  bigFive?: unknown;
  cvUrl?: string;
}

interface KanbanUser {
  company?: string;
  id?: string;
  name?: string;
  email?: string;
}

export interface KanbanLIAHandlersContext {
  // LIA chat state
  liaMessages: {
    id: string;
    type: "user" | "response";
    content: string;
    timestamp: number;
    metadata?: Record<string, unknown>;
  }[];
  setLiaMessages: React.Dispatch<
    React.SetStateAction<
      {
        id: string;
        type: "user" | "response";
        content: string;
        timestamp: number;
        metadata?: Record<string, unknown>;
      }[]
    >
  >;
  setLiaPromptValue: (value: string) => void;
  setIsLiaLoading: (loading: boolean) => void;
  liaConversationId: string | undefined;
  setLiaConversationId: (id: string | undefined) => void;

  // Job and candidates
  currentJob: KanbanJob;
  allTableCandidates: KanbanTableCandidate[];
  selectedCandidates: Set<string>;
  candidatesData: Record<string, KanbanTableCandidate[]>;

  // User auth
  user: KanbanUser | null;

  // findCandidateById
  findCandidateById: (id: string) => KanbanTableCandidate | undefined;

  // UI action sub-handlers — these open modals
  openUnifiedModal: (
    candidate: KanbanTableCandidate,
    type: CommunicationType,
  ) => void;
  openTransition: (
    candidates: KanbanCandidate[],
    fromStage: string,
    toStage: string,
  ) => void;
  setWsiCandidate: (candidate: KanbanTableCandidate) => void;
  setShowWSIModal: (open: boolean) => void;
  setWsiInviteCandidate: (candidate: KanbanTableCandidate) => void;
  setShowWSIInviteModal: (open: boolean) => void;
  setDataRequestModalCandidate: (candidate: KanbanTableCandidate) => void;
  setShowDataRequestModal: (open: boolean) => void;
  setRubricCandidate: (candidate: KanbanTableCandidate) => void;
  setShowRubricModal: (open: boolean) => void;
}

export function useKanbanLIAHandlers(ctx: KanbanLIAHandlersContext) {
  const { companyId: resolvedCompanyId } = useCompanyId();

  // Acesso ao store unificado — sincroniza conversation_id e mensagens entre todos os contextos
  const { switchChatContext, sendOrchestratedMessage, addChatMessage } =
    useLiaChatContext();

  const {
    liaMessages,
    setLiaMessages,
    setLiaPromptValue,
    setIsLiaLoading,
    liaConversationId: localLiaConversationId,
    setLiaConversationId,
    currentJob,
    allTableCandidates,
    selectedCandidates,
    candidatesData,
    user,
    findCandidateById,
    openUnifiedModal,
    openTransition,
    setWsiCandidate,
    setShowWSIModal,
    setWsiInviteCandidate,
    setShowWSIInviteModal,
    setDataRequestModalCandidate,
    setShowDataRequestModal,
    setRubricCandidate,
    setShowRubricModal,
  } = ctx;

  const liaConversationId = localLiaConversationId;

  const getFallbackResponse = (command: string): string => {
    const cmd = command.toLowerCase().trim();

    if (
      cmd.includes("quantos candidatos") ||
      cmd.includes("total de candidatos") ||
      cmd.includes("quantos no funil")
    ) {
      const total = allTableCandidates.length;
      const stages = {
        sourcing: candidatesData.sourcing?.length || 0,
        screening: candidatesData.screening?.length || 0,
        interview_hr: candidatesData.interview_hr?.length || 0,
        interview_technical: candidatesData.interview_technical?.length || 0,
        interview_manager: candidatesData.interview_manager?.length || 0,
        offer: candidatesData.offer?.length || 0,
        hired: candidatesData.hired?.length || 0,
        rejected: candidatesData.rejected?.length || 0,
      };
      return (
        `📊 **Total no Kanban: ${total} candidatos**\n\n` +
        `• Funil: ${stages.sourcing}\n` +
        `• Triagem: ${stages.screening}\n` +
        `• Entrevista RH: ${stages.interview_hr}\n` +
        `• Entrevista Técnica: ${stages.interview_technical}\n` +
        `• Entrevista Gestor: ${stages.interview_manager}\n` +
        `• Proposta: ${stages.offer}\n` +
        `• Contratado: ${stages.hired}\n` +
        `• Reprovado: ${stages.rejected}`
      );
    }

    if (
      cmd.includes("candidatos por etapa") ||
      cmd.includes("distribuição") ||
      cmd.includes("distribuicao")
    ) {
      const stages = {
        Funil: candidatesData.sourcing?.length || 0,
        Triagem: candidatesData.screening?.length || 0,
        "Entrevista RH": candidatesData.interview_hr?.length || 0,
        "Entrevista Técnica": candidatesData.interview_technical?.length || 0,
        "Entrevista Gestor": candidatesData.interview_manager?.length || 0,
        Proposta: candidatesData.offer?.length || 0,
        Contratado: candidatesData.hired?.length || 0,
        Reprovado: candidatesData.rejected?.length || 0,
      };
      const total = Object.values(stages).reduce((a, b) => a + b, 0);
      return (
        `📈 **Distribuição por Etapa**\n\n` +
        Object.entries(stages)
          .map(([stage, count]) => {
            const percent = total > 0 ? Math.round((count / total) * 100) : 0;
            return `• ${stage}: ${count} (${percent}%)`;
          })
          .join("\n")
      );
    }

    if (
      cmd.includes("top 5") ||
      cmd.includes("top5") ||
      cmd.includes("melhores candidatos") ||
      cmd.includes("top candidatos")
    ) {
      const sorted = [...allTableCandidates]
        .sort((a, b) => {
          const scoreA = a.score || a.fitScore || 0;
          const scoreB = b.score || b.fitScore || 0;
          return scoreB - scoreA;
        })
        .slice(0, 5);

      return (
        `🏆 **Top 5 Candidatos**\n\n` +
        sorted
          .map((c, i) => {
            const score = c.score
              ? `Score LIA: ${c.score}`
              : `FitNota: ${c.fitScore || "N/A"}%`;
            return `${i + 1}. **${c.name}**\n   ${c.role || "N/A"} | ${c.currentCompany || ""}\n   ${score}`;
          })
          .join("\n\n")
      );
    }

    if (
      cmd.includes("comparar") ||
      cmd.includes("comparação") ||
      cmd.includes("comparacao")
    ) {
      if (selectedCandidates.size === 0) {
        return `⚖️ **Comparar Candidatos**\n\nSelecione 2 ou mais candidatos no Kanban para compará-los.\n\n💡 Dica: Clique no checkbox de cada candidato que deseja comparar.`;
      } else if (selectedCandidates.size === 1) {
        return `⚖️ **Comparar Candidatos**\n\nVocê selecionou apenas 1 candidato. Selecione mais candidatos para fazer uma comparação.`;
      } else {
        const selectedList = allTableCandidates.filter((c) =>
          selectedCandidates.has(String(c.id)),
        );
        return (
          `⚖️ **Comparação - ${selectedList.length} Candidatos**\n\n` +
          selectedList
            .map((c) => {
              const score = c.score
                ? `Nota: ${c.score}`
                : `Fit: ${c.fitScore || "N/A"}%`;
              return (
                `**${c.name}**\n` +
                `• ${c.role || "N/A"} @ ${c.currentCompany || "N/A"}\n` +
                `• ${score} | Warnings: ${c.warnings || 0}\n` +
                `• Skills: ${(c.skills || []).slice(0, 3).join(", ") || "N/A"}`
              );
            })
            .join("\n\n")
        );
      }
    }

    if (
      cmd.includes("gargalo") ||
      cmd.includes("bottleneck") ||
      cmd.includes("acumulados")
    ) {
      const stages = [
        { name: "Funil", count: candidatesData.sourcing?.length || 0 },
        { name: "Triagem", count: candidatesData.screening?.length || 0 },
        {
          name: "Entrevista RH",
          count: candidatesData.interview_hr?.length || 0,
        },
        {
          name: "Entrevista Técnica",
          count: candidatesData.interview_technical?.length || 0,
        },
        {
          name: "Entrevista Gestor",
          count: candidatesData.interview_manager?.length || 0,
        },
        { name: "Proposta", count: candidatesData.offer?.length || 0 },
      ].sort((a, b) => b.count - a.count);

      const maxCount = stages[0].count;
      const gargalos = stages.filter((s) => s.count === maxCount);

      return (
        `🚧 **Análise de Gargalos**\n\n` +
        `**Maior acúmulo:** ${gargalos.map((g) => g.name).join(", ")} (${maxCount} candidatos)\n\n` +
        `**Ranking por volume:**\n` +
        stages
          .map((s, i) => `${i + 1}. ${s.name}: ${s.count} candidatos`)
          .join("\n") +
        `\n\n💡 **Sugestão:** Priorize ações na etapa com maior acúmulo para melhorar o fluxo do processo.`
      );
    }

    const recruiterName = currentJob.recruiter?.split(" ")[0] || "Recrutador";
    return `💬 **Olá, ${recruiterName}!**\n\nEu ainda estou evoluindo e em breve estarei pronta para atender a todas as suas solicitações e esclarecer todas as suas dúvidas. 🚀\n\nPeço desculpas por não conseguir te ajudar com essa pergunta específica agora.\n\nNeste momento, posso te ajudar com **análises e informações do funil de recrutamento**, como:\n\n• "Quantos candidatos temos no processo?"\n• "Quem são os top 5 candidatos?"\n• "Como está a distribuição por etapa?"\n• "Comparar candidatos selecionados"\n• "Identificar gargalos no processo"\n\n✨ Vamos conversar muito em breve! Use as sugestões acima ou me pergunte sobre seus candidatos.`;
  };

  const handleLiaUiAction = useCallback(
    (action: string, params: Record<string, unknown>) => {
      if (action === "start_job_wizard") return;

      const candidateIds: string[] = (params.candidate_ids as string[]) || [];
      const matchedCandidates = candidateIds
        .map((id) => findCandidateById(id))
        .filter(Boolean);
      const firstCandidate =
        matchedCandidates.length > 0 ? matchedCandidates[0] : null;

      if (!firstCandidate) {
        return;
      }

      setTimeout(() => {
        switch (action) {
          case "move_candidate":
          case "approve_candidate":
            {
              const fromStage = firstCandidate.stage || "";
              const toStage =
                (params.target_stage as string) ||
                (params.to_stage as string) ||
                "";
              const kanbanCandidate: KanbanCandidate = {
                id: String(firstCandidate.id),
                name: firstCandidate.name || "",
                role: firstCandidate.role || "",
                score: firstCandidate.score || 0,
                email: firstCandidate.email,
                phone: firstCandidate.phone,
              };
              openTransition([kanbanCandidate], fromStage, toStage);
            }
            break;

          case "send_email":
            openUnifiedModal(firstCandidate, "email");
            break;

          case "start_screening":
            if (params.screening_type === "wsi_text") {
              setWsiCandidate(firstCandidate);
              setShowWSIModal(true);
            } else {
              setWsiInviteCandidate(firstCandidate);
              setShowWSIInviteModal(true);
            }
            break;

          case "schedule_interview":
            openUnifiedModal(firstCandidate, "agendamento");
            break;

          case "request_data":
            setDataRequestModalCandidate(firstCandidate);
            setShowDataRequestModal(true);
            break;

          case "analyze_profile":
            setRubricCandidate(firstCandidate);
            setShowRubricModal(true);
            break;

          default:
            break;
        }
      }, 600);
    },
    [
      findCandidateById,
      openUnifiedModal,
      openTransition,
      setWsiCandidate,
      setShowWSIModal,
      setWsiInviteCandidate,
      setShowWSIInviteModal,
      setDataRequestModalCandidate,
      setShowDataRequestModal,
      setRubricCandidate,
      setShowRubricModal,
    ],
  );

  const handleAICommand = async (command: string) => {
    // Ensure unified context is set to kanban before any send
    switchChatContext("kanban_chat");

    if (isClearChatCommand(command)) {
      setLiaMessages([]);
      setLiaPromptValue("");
      return;
    }

    const timestamp = Date.now();

    setLiaPromptValue("");
    setIsLiaLoading(true);

    try {
      const jobContext = {
        id: (currentJob as { backendId?: unknown }).backendId || currentJob.id,
        title: currentJob.title,
        department: currentJob.department,
        level: currentJob.level,
        requirements: currentJob.requirements,
        skills: currentJob.requirements,
        location: currentJob.location,
        salary: currentJob.salary,
        workModel: currentJob.workModel,
        deadline: currentJob.deadline,
      };

      const candidatesForApi = allTableCandidates.map((c) => ({
        id: c.id,
        name: c.name,
        role: c.role,
        currentCompany: c.currentCompany,
        location: c.location,
        score: c.score,
        wsiScore: c.wsiScore || c.score,
        wsiTechnical: c.wsiTechnical,
        wsiBehavioral: c.wsiBehavioral,
        fitScore: c.fitScore,
        skills: c.skills,
        experience: c.experience,
        stage: c.stage,
        subStatus: c.subStatus,
        daysInStage: c.daysInStage,
        warnings: c.warnings,
        email: c.email,
        phone: c.phone,
        bigFive: c.bigFive,
        hasCV: !!c.cvUrl,
      }));

      const selectedIds =
        selectedCandidates.size > 0
          ? Array.from(selectedCandidates)
          : undefined;

      const extractMetadata = (
        raw: Record<string, unknown>,
      ): Record<string, unknown> => {
        const r = raw as unknown as OrchestratedJobChatResponse;
        return {
          intent: r.intent_detected,
          confidence: r.confidence,
          agent: r.agent_used,
          suggested_prompts: r.suggested_prompts,
          actions: r.actions,
          action_executed: r.action_executed,
          action_result: r.action_result,
          action_type: r.action_type,
          needs_confirmation: r.needs_confirmation,
          needs_params: r.needs_params,
          pending_action_id: r.pending_action_id,
        };
      };

      const rawResponse = await sendOrchestratedMessage(
        command,
        async (convId) => {
          const result = await callOrchestratedJobChat({
            message: command,
            job_context:
              jobContext as OrchestratedJobChatRequest["job_context"],
            candidates:
              candidatesForApi as OrchestratedJobChatRequest["candidates"],
            selected_candidate_ids: selectedIds,
            conversation_id: convId ?? undefined,
            company_id: resolvedCompanyId || "",
          });
          return result as unknown as {
            content: string;
            conversation_id?: string | null;
            [key: string]: unknown;
          };
        },
        { extractResponseMetadata: extractMetadata },
      );
      const response = rawResponse as unknown as OrchestratedJobChatResponse;

      if (response.success) {
        if (response.conversation_id) {
          setLiaConversationId(response.conversation_id);
        }

        if (
          !response.action_executed &&
          response.action_type &&
          response.ui_action
        ) {
          addChatMessage({
            id: `fallback-${timestamp}`,
            sender: "lia",
            content:
              "⚠️ Não consegui executar automaticamente. Deseja tentar manualmente?",
            timestamp: formatMessageTime(),
            metadata: {
              is_fallback: true,
              action_type: response.action_type,
              ui_action: response.ui_action,
              ui_action_params: response.ui_action_params,
            },
          });
        }

        if (
          !response.action_executed &&
          response.ui_action &&
          response.ui_action !== "start_job_wizard"
        ) {
          const enrichedParams = { ...(response.ui_action_params || {}) };
          if (!enrichedParams.candidate_ids && response.actions?.length > 0) {
            const actionWithIds = response.actions.find(
              (a: { candidate_ids?: string[] }) =>
                a.candidate_ids && a.candidate_ids.length > 0,
            );
            if (actionWithIds) {
              enrichedParams.candidate_ids = actionWithIds.candidate_ids;
            }
          }
          handleLiaUiAction(response.ui_action, enrichedParams);
        }
      } else if (
        (response as unknown as Record<string, unknown>).error === "auth_error"
      ) {
        addChatMessage({
          id: `auth-error-${timestamp}`,
          sender: "lia",
          content:
            ((response as unknown as Record<string, unknown>)
              .content as string) ||
            "Sessao expirada. Recarregue a pagina para continuar.",
          timestamp: formatMessageTime(),
        });
      } else {
        throw new Error("API returned unsuccessful response");
      }
    } catch (_error) {
      try {
        const jobContext = {
          title: currentJob.title,
          department: currentJob.department,
          level: currentJob.level,
          requirements: currentJob.requirements,
          skills: currentJob.requirements,
          location: currentJob.location,
          salary: currentJob.salary,
          workModel: currentJob.workModel,
          deadline: currentJob.deadline,
        };
        const candidatesForApi = allTableCandidates.map((c) => ({
          id: c.id,
          name: c.name,
          role: c.role,
          currentCompany: c.currentCompany,
          location: c.location,
          score: c.score,
          fitScore: c.fitScore,
          skills: c.skills,
          experience: c.experience,
          stage: c.stage,
          warnings: c.warnings,
          email: c.email,
          phone: c.phone,
          bigFive: c.bigFive,
        }));
        const selectedIds =
          selectedCandidates.size > 0
            ? Array.from(selectedCandidates)
            : undefined;
        const fallbackResponse = await callKanbanAssistant({
          command,
          job_context: jobContext as KanbanAssistantRequest["job_context"],
          candidates: candidatesForApi as KanbanAssistantRequest["candidates"],
          selected_candidate_ids: selectedIds,
        });
        if (fallbackResponse.success) {
          addChatMessage({
            id: `response-${timestamp}`,
            sender: "lia",
            content: fallbackResponse.content,
            timestamp: formatMessageTime(),
          });

          if (fallbackResponse.ui_action) {
            handleLiaUiAction(
              fallbackResponse.ui_action,
              fallbackResponse.ui_action_params || {},
            );
          }
        } else {
          throw new Error("Fallback also failed");
        }
      } catch (_fallbackError) {
        const fallbackContent = getFallbackResponse(command);
        addChatMessage({
          id: `response-${timestamp}`,
          sender: "lia",
          content: fallbackContent,
          timestamp: formatMessageTime(),
        });
      }
    } finally {
      setIsLiaLoading(false);
    }
  };

  const handleOrchestratedMessage = async (
    message: string,
  ): Promise<{
    content: string;
    ui_action?: string | null;
    ui_action_params?: Record<string, unknown>;
  }> => {
    // Ensure unified context is set to kanban before orchestrated send
    switchChatContext("kanban_chat");

    const jobContext = {
      id: (currentJob as { backendId?: unknown }).backendId || currentJob.id,
      title: currentJob.title,
      department: currentJob.department,
      level: currentJob.level,
      requirements: currentJob.requirements,
      skills: currentJob.requirements,
      location: currentJob.location,
      salary: currentJob.salary,
      workModel: currentJob.workModel,
      deadline: currentJob.deadline,
    };

    const candidatesForApi = allTableCandidates.map((c) => ({
      id: c.id,
      name: c.name,
      role: c.role,
      currentCompany: c.currentCompany,
      location: c.location,
      score: c.score,
      wsiScore: c.wsiScore || c.score,
      wsiTechnical: c.wsiTechnical,
      wsiBehavioral: c.wsiBehavioral,
      fitScore: c.fitScore,
      skills: c.skills,
      experience: c.experience,
      stage: c.stage,
      subStatus: c.subStatus,
      daysInStage: c.daysInStage,
      warnings: c.warnings,
      email: c.email,
      phone: c.phone,
      bigFive: c.bigFive,
      hasCV: !!c.cvUrl,
    }));

    const selectedIds =
      selectedCandidates.size > 0 ? Array.from(selectedCandidates) : undefined;

    try {
      const rawResponse = await sendOrchestratedMessage(
        message,
        async (convId) => {
          const result = await callOrchestratedJobChat({
            message,
            job_context:
              jobContext as OrchestratedJobChatRequest["job_context"],
            candidates:
              candidatesForApi as OrchestratedJobChatRequest["candidates"],
            selected_candidate_ids: selectedIds,
            conversation_id: convId ?? undefined,
            company_id: resolvedCompanyId || "",
          });
          return result as unknown as {
            content: string;
            conversation_id?: string | null;
            [key: string]: unknown;
          };
        },
      );
      const response = rawResponse as unknown as OrchestratedJobChatResponse;

      if ((rawResponse as Record<string, unknown>).error === "auth_error") {
        return {
          content:
            response.content ||
            "Sessao expirada. Recarregue a pagina para continuar.",
          ui_action: null,
        };
      }

      if (response.conversation_id) {
        setLiaConversationId(response.conversation_id);
      }

      return {
        content: response.content,
        ui_action: response.ui_action,
        ui_action_params: response.ui_action_params,
      };
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
      }
      return {
        content: getFallbackResponse(message),
        ui_action: null,
      };
    }
  };

  // PR-D — escuta lia:unhandled_ui_action para tratar UIActions kanban-specific
  // (move_candidate, send_email, schedule_interview etc.) emitidas pelo
  // UnifiedChat lateral quando user está na página kanban.
  useUnhandledUIActionListener(handleLiaUiAction);

  // PR-B: Trigger C — UIAction open_offer_review vinda do UnifiedChat
  const { openOfferReview } = useOfferReviewFlow()

  const handleKanbanUIAction = useCallback((action: string, params: Record<string, unknown>) => {
    if (action === "open_offer_review") {
      const candidateId = params?.candidate_id ?? params?.candidateId
      const jobId = params?.job_id ?? params?.jobId
      if (typeof candidateId === "string" && typeof jobId === "string") {
        openOfferReview({ candidateId, jobId, draftId: params?.draft_id as string | undefined })
      }
    }
  }, [openOfferReview])

  useUnhandledUIActionListener(handleKanbanUIAction)

  return { handleLiaUiAction, handleAICommand, handleOrchestratedMessage };
}
