"use client";

import type { CommunicationType } from "@/components/modals/unified-communication-modal";
import { useUnhandledUIActionListener } from "@/hooks/chat/useUnhandledUIActionListener";
import React from "react";
import { toast } from "sonner";
import type {
  CandidatesLIAHandlersContext,
  LIAChatMessage,
} from "./useCandidatesLIAHandlers";

export function useLIAQuickActions(ctx: CandidatesLIAHandlersContext) {
  const {
    candidates,
    setChatMessages,
    setLiaPromptValue,
    setSelectedCandidatesForBatch,
    setShowScheduleModal,
    talentFunnel,
  } = ctx;

  const handleQuickAction = async (actionId: string, actionType: string) => {
    const liaMessage: LIAChatMessage = {
      id: `lia-action-${Date.now()}`,
      type: "lia",
      content: "",
      timestamp: new Date(),
    };

    switch (actionType) {
      case "screening":
        liaMessage.content =
          "🎯 **Iniciando triagem em lote**\n\nPreparando triagem WSI para os candidatos selecionados...";
        setChatMessages((prev) => [...prev, liaMessage]);
        toast.success("Triagem WSI", {
          description:
            "Funcionalidade de triagem em lote será implementada em breve.",
        });
        break;

      case "assign":
        liaMessage.content =
          "📋 **Atribuir candidatos a vaga**\n\nSelecione os candidatos e escolha a vaga para atribuição.";
        setChatMessages((prev) => [...prev, liaMessage]);
        if (candidates.length > 0) {
          setSelectedCandidatesForBatch(
            new Set(candidates.slice(0, 10).map((c) => c.id)),
          );
        }
        break;

      case "favorite":
        const candidateIds = candidates.slice(0, 10).map((c) => c.id);
        candidateIds.forEach((id) => talentFunnel.toggleFavoriteCandidate(id));
        liaMessage.content = `⭐ **${candidateIds.length} candidatos adicionados aos favoritos**\n\nVocê pode acessá-los na aba "Favoritos".`;
        setChatMessages((prev) => [...prev, liaMessage]);
        toast.success("Favoritos atualizados", {
          description: `${candidateIds.length} candidatos adicionados aos favoritos`,
        });
        break;

      case "whatsapp":
        liaMessage.content =
          "📱 **Contato via WhatsApp**\n\nPreparando mensagens personalizadas para contato...";
        setChatMessages((prev) => [...prev, liaMessage]);
        break;

      case "schedule":
        liaMessage.content =
          "📅 **Agendamento de entrevistas**\n\nAbrindo modal de agendamento em lote...";
        setChatMessages((prev) => [...prev, liaMessage]);
        setShowScheduleModal(true);
        break;

      case "refine":
        liaMessage.content =
          "🔍 **Refinar busca**\n\nDigite novos critérios para refinar sua busca.";
        setChatMessages((prev) => [...prev, liaMessage]);
        setLiaPromptValue("");
        break;

      case "export":
        liaMessage.content =
          "📊 **Exportando candidatos**\n\nPreparando arquivo para download...";
        setChatMessages((prev) => [...prev, liaMessage]);
        try {
          const exportData = candidates.map((c) => ({
            nome: c.name,
            cargo: c.current_title || c.position,
            empresa: c.current_company,
            email: c.email,
            telefone: c.phone || c.mobile_phone,
            linkedin: c.linkedin_url,
            cidade: c.location_city || c.location,
            score: c.liaAnalysis?.score || c.score,
          }));
          const csvContent = [
            Object.keys(exportData[0]).join(","),
            ...exportData.map((row) =>
              Object.values(row)
                .map((v) => `"${v || ""}"`)
                .join(","),
            ),
          ].join("\n");
          const blob = new Blob([csvContent], {
            type: "text/csv;charset=utf-8;",
          });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = `candidatos_${new Date().toISOString().split("T")[0]}.csv`;
          link.click();

          const successMessage: LIAChatMessage = {
            id: `lia-export-success-${Date.now()}`,
            type: "lia",
            content: `✅ **Exportação concluída!**\n\n${exportData.length} candidatos exportados para CSV.`,
            timestamp: new Date(),
          };
          setChatMessages((prev) => [...prev, successMessage]);
        } catch (error) {}
        break;

      default:
        liaMessage.content = `Ação "${actionId}" será implementada em breve.`;
        setChatMessages((prev) => [...prev, liaMessage]);
    }
  };

  const handleTalentUIAction = (
    action: string,
    params?: Record<string, unknown>,
  ) => {
    const {
      setActiveSearchTab,
      selectedCandidatesForBatch,
      setUnifiedModalCandidate,
      setUnifiedModalType,
      setUnifiedModalOpen,
      setShowAddToListModal,
    } = ctx;

    switch (action) {
      case "start_job_wizard":
        toast.success("Criar Nova Vaga", {
          description: "Abrindo wizard de criação de vaga...",
        });
        break;
      case "switch_search_mode":
        if (params?.mode && typeof params.mode === "string") {
          setActiveSearchTab(
            params.mode as Parameters<typeof setActiveSearchTab>[0],
          );
        }
        break;
      case "open_communication_modal":
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0];
          const candidate = candidates.find((c) => c.id === firstId);
          if (candidate) {
            setUnifiedModalCandidate(candidate);
            setUnifiedModalType("email" as CommunicationType);
            setUnifiedModalOpen(true);
          }
        }
        break;
      case "open_schedule_modal":
        setShowScheduleModal(true);
        break;
      case "open_screening_modal":
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0];
          const candidate = candidates.find((c) => c.id === firstId);
          if (candidate) {
            setUnifiedModalCandidate(candidate);
            setUnifiedModalType("triagem" as CommunicationType);
            setUnifiedModalOpen(true);
          }
        }
        break;
      case "trigger_export":
        handleQuickAction("export", "export");
        break;
      case "open_add_to_list_modal":
        if (selectedCandidatesForBatch.size > 0) {
          setShowAddToListModal(true);
        }
        break;
    }
  };

  const handleCalibrationLike = async (candidateId: string) => {
    try {
      await fetch("/api/backend-proxy/search/calibration/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: "like",
          context: { source: "chat_calibration" },
        }),
      });
      toast.success("Feedback registrado", {
        description: "Candidato marcado como interessante",
      });
    } catch (error) {}
  };

  const handleCalibrationDislike = async (
    candidateId: string,
    reason?: string,
  ) => {
    try {
      await fetch("/api/backend-proxy/search/calibration/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: "dislike",
          reason,
          context: { source: "chat_calibration" },
        }),
      });
      toast.success("Feedback registrado", {
        description: "Preferência salva para calibração",
      });
    } catch (error) {}
  };

  // PR-D — escuta lia:unhandled_ui_action para tratar UIActions talent-specific
  // (switch_search_mode, open_communication_modal, trigger_export, etc.)
  // emitidas pelo UnifiedChat lateral quando user está na página de talent funnel.
  useUnhandledUIActionListener(handleTalentUIAction);

  return {
    handleQuickAction,
    handleTalentUIAction,
    handleCalibrationLike,
    handleCalibrationDislike,
  };
}
