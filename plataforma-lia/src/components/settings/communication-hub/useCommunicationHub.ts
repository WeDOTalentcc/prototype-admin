import { useReducer, useMemo, useRef, useEffect, useCallback } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import type { EmailTemplate, AiResultModal } from './CommunicationHub.types'
import { TEMPLATE_GROUPS } from './CommunicationHub.constants'
import { apiFetch } from '@/lib/api/api-fetch'
import { notifyChatOfSettingsUpdate } from '@/lib/api/settings-notify'
import { useAiPersona } from "@/hooks/company/use-ai-persona"

// ---------------------------------------------------------------------------
// Reducer state & actions
// ---------------------------------------------------------------------------

interface CommunicationHubState {
  activeTab: string
  selectedTemplate: EmailTemplate | null
  editingTemplate: EmailTemplate | null
  aiPrompt: string
  aiResultModal: AiResultModal | null
  isGenerating: boolean
  channelFilter: "all" | "email" | "whatsapp"
  triggerTypeFilter: "all" | "automatic" | "manual" | "both"
  searchQuery: string
  expandedGroups: string[]
  isEditingSignature: boolean
  isEditingSchedule: boolean
  saving: boolean
  savingSettings: boolean
  savingWeeklyDigest: boolean
  error: string | null
  successMessage: string | null
}

type CommunicationHubAction =
  | { type: "SET_TAB"; payload: string }
  | { type: "SELECT_TEMPLATE"; payload: EmailTemplate | null }
  | { type: "SET_EDITING_TEMPLATE"; payload: EmailTemplate | null }
  | { type: "SET_AI_PROMPT"; payload: string }
  | { type: "SET_AI_RESULT_MODAL"; payload: AiResultModal | null }
  | { type: "SET_IS_GENERATING"; payload: boolean }
  | { type: "SET_CHANNEL_FILTER"; payload: "all" | "email" | "whatsapp" }
  | { type: "SET_TRIGGER_FILTER"; payload: "all" | "automatic" | "manual" | "both" }
  | { type: "SET_SEARCH_QUERY"; payload: string }
  | { type: "SET_EXPANDED_GROUPS"; payload: string[] }
  | { type: "SET_IS_EDITING_SIGNATURE"; payload: boolean }
  | { type: "SET_IS_EDITING_SCHEDULE"; payload: boolean }
  | { type: "SET_SAVING"; payload: boolean }
  | { type: "SET_SAVING_SETTINGS"; payload: boolean }
  | { type: "SET_SAVING_WEEKLY_DIGEST"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_SUCCESS"; payload: string | null }

const initialState: CommunicationHubState = {
  activeTab: "templates",
  selectedTemplate: null,
  editingTemplate: null,
  aiPrompt: "",
  aiResultModal: null,
  isGenerating: false,
  channelFilter: "all",
  triggerTypeFilter: "all",
  searchQuery: "",
  expandedGroups: ["primeiro_contato", "triagem", "entrevista"],
  isEditingSignature: false,
  isEditingSchedule: false,
  saving: false,
  savingSettings: false,
  savingWeeklyDigest: false,
  error: null,
  successMessage: null,
}

function communicationHubReducer(
  state: CommunicationHubState,
  action: CommunicationHubAction
): CommunicationHubState {
  switch (action.type) {
    case "SET_TAB":
      return { ...state, activeTab: action.payload }
    case "SELECT_TEMPLATE":
      return { ...state, selectedTemplate: action.payload }
    case "SET_EDITING_TEMPLATE":
      return { ...state, editingTemplate: action.payload }
    case "SET_AI_PROMPT":
      return { ...state, aiPrompt: action.payload }
    case "SET_AI_RESULT_MODAL":
      return { ...state, aiResultModal: action.payload }
    case "SET_IS_GENERATING":
      return { ...state, isGenerating: action.payload }
    case "SET_CHANNEL_FILTER":
      return { ...state, channelFilter: action.payload }
    case "SET_TRIGGER_FILTER":
      return { ...state, triggerTypeFilter: action.payload }
    case "SET_SEARCH_QUERY":
      return { ...state, searchQuery: action.payload }
    case "SET_EXPANDED_GROUPS":
      return { ...state, expandedGroups: action.payload }
    case "SET_IS_EDITING_SIGNATURE":
      return { ...state, isEditingSignature: action.payload }
    case "SET_IS_EDITING_SCHEDULE":
      return { ...state, isEditingSchedule: action.payload }
    case "SET_SAVING":
      return { ...state, saving: action.payload }
    case "SET_SAVING_SETTINGS":
      return { ...state, savingSettings: action.payload }
    case "SET_SAVING_WEEKLY_DIGEST":
      return { ...state, savingWeeklyDigest: action.payload }
    case "SET_ERROR":
      return { ...state, error: action.payload }
    case "SET_SUCCESS":
      return { ...state, successMessage: action.payload }
    default:
      return state
  }
}

// ---------------------------------------------------------------------------
// React Query fetchers
// ---------------------------------------------------------------------------

async function fetchTemplates(): Promise<EmailTemplate[]> {
  const res = await apiFetch(`/api/backend-proxy/email-templates?visibility=recruiter`)
  if (!res.ok) return []
  const result = await res.json()
  const items = result.items || (Array.isArray(result) ? result : [])
  return items.map((t: Record<string, unknown>) => ({
    id: t.id,
    name: t.name,
    category: t.category || "followup",
    subject: t.subject || "",
    body:
      (t.content as string) ||
      t.body ||
      t.body_text ||
      (t.body_html ? (t.body_html as string).replace(/<[^>]*>/g, "") : ""),
    variables: t.variables || [],
    isActive: t.is_active ?? true,
    lastUpdated: t.updated_at || t.last_updated || new Date().toISOString().split("T")[0],
    channel: t.channel || "email",
    situation: t.situation || "",
    trigger_type: t.trigger_type || "manual",
    used_in: t.used_in || [],
    priority: t.priority || "medium",
  }))
}

interface CommunicationSettings {
  signature: string
  sendingHours: { start: number; end: number }
  respectHolidays: boolean
  respectWeekends: boolean
  maxMessagesPerDay: number
  companyId: string
}

function communicationSettingsDefaults(): CommunicationSettings {
  return {
    signature:
      "{{recrutador_nome}} | {{cargo}}\n{{empresa_nome}}\n\u{1F4E7} {{email}} | \u{1F4F1} {{telefone}}\n\u{1F310} {{website}}",
    sendingHours: { start: 8, end: 20 },
    respectHolidays: true,
    respectWeekends: true,
    maxMessagesPerDay: 3,
    companyId: "",
  }
}

async function fetchCommunicationSettings(): Promise<CommunicationSettings> {
  const defaults = communicationSettingsDefaults()

  const [profileRes, settingsRes] = await Promise.all([
    apiFetch("/api/backend-proxy/company/profile").catch(() => null),
    apiFetch("/api/backend-proxy/company/communication-settings").catch(() => null),
  ])

  if (profileRes?.ok) {
    const profileData = await profileRes.json().catch(() => ({}))
    if (profileData?.id) defaults.companyId = profileData.id
  }

  if (settingsRes?.ok) {
    const settings = await settingsRes.json().catch(() => ({}))
    if (settings && !settings.error) {
      if (settings.signature) defaults.signature = settings.signature
      if (settings.sending_hours_start !== undefined)
        defaults.sendingHours.start = settings.sending_hours_start
      if (settings.sending_hours_end !== undefined)
        defaults.sendingHours.end = settings.sending_hours_end
      if (settings.respect_holidays !== undefined)
        defaults.respectHolidays = settings.respect_holidays
      if (settings.respect_weekends !== undefined)
        defaults.respectWeekends = settings.respect_weekends
      if (settings.max_messages_per_day !== undefined)
        defaults.maxMessagesPerDay = settings.max_messages_per_day
    }
  }

  return defaults
}

async function fetchWeeklyDigestPreference(): Promise<boolean> {
  try {
    const res = await apiFetch("/api/backend-proxy/digest/weekly/preferences")
    if (res.ok) {
      const data = await res.json()
      if (data?.weekly_report_enabled !== undefined) return data.weekly_report_enabled
    }
  } catch {
    // silently default to true
  }
  return true
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCommunicationHub(activeSubsection?: string) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [state, dispatch] = useReducer(communicationHubReducer, {
    ...initialState,
    activeTab: activeSubsection || "templates",
  })

  const queryClient = useQueryClient()
  const bodyTextareaRef = useRef<HTMLTextAreaElement>(null)
  const isMountedRef = useRef(true)

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  // Sync activeSubsection prop -> reducer tab
  useEffect(() => {
    if (activeSubsection) {
      dispatch({ type: "SET_TAB", payload: activeSubsection })
    }
  }, [activeSubsection])

  // --- Server data via React Query ---

  const {
    data: templates = [],
    isLoading: loadingTemplates,
  } = useQuery<EmailTemplate[]>({
    queryKey: ["communication-templates"],
    queryFn: fetchTemplates,
    staleTime: 60_000,
  })

  const {
    data: communicationSettings,
    isLoading: loadingSettings,
  } = useQuery<CommunicationSettings>({
    queryKey: ["communication-settings"],
    queryFn: fetchCommunicationSettings,
    staleTime: 60_000,
  })

  const {
    data: weeklyDigestEnabled = true,
  } = useQuery<boolean>({
    queryKey: ["weekly-digest-preference"],
    queryFn: fetchWeeklyDigestPreference,
    staleTime: 60_000,
  })

  // Derive server state with fallbacks
  const defaults = communicationSettingsDefaults()
  const signature = communicationSettings?.signature ?? defaults.signature
  const sendingHours = communicationSettings?.sendingHours ?? defaults.sendingHours
  const respectHolidays = communicationSettings?.respectHolidays ?? defaults.respectHolidays
  const respectWeekends = communicationSettings?.respectWeekends ?? defaults.respectWeekends
  const maxMessagesPerDay = communicationSettings?.maxMessagesPerDay ?? defaults.maxMessagesPerDay
  const companyId = communicationSettings?.companyId ?? defaults.companyId
  const loading = loadingTemplates || loadingSettings

  // ---------------------------------------------------------------------------
  // Derived / memoized
  // ---------------------------------------------------------------------------

  const getTemplateGroup = useCallback((template: EmailTemplate): string => {
    const situation = template.situation?.toLowerCase() || ""
    for (const [groupKey, group] of Object.entries(TEMPLATE_GROUPS)) {
      if (group.situations.some((s) => situation.includes(s) || s.includes(situation))) {
        return groupKey
      }
    }
    return "outros"
  }, [])

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const matchesChannel =
        state.channelFilter === "all" || template.channel === state.channelFilter
      const matchesTrigger =
        state.triggerTypeFilter === "all" || template.trigger_type === state.triggerTypeFilter
      const matchesSearch =
        state.searchQuery === "" ||
        template.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
        template.subject?.toLowerCase().includes(state.searchQuery.toLowerCase())
      return matchesChannel && matchesTrigger && matchesSearch
    })
  }, [templates, state.channelFilter, state.triggerTypeFilter, state.searchQuery])

  const groupedTemplates = useMemo(() => {
    const groups: Record<string, EmailTemplate[]> = {}
    Object.keys(TEMPLATE_GROUPS).forEach((key) => {
      groups[key] = []
    })
    filteredTemplates.forEach((template) => {
      const groupKey = getTemplateGroup(template)
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(template)
    })
    return groups
  }, [filteredTemplates, getTemplateGroup])

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const showSuccess = useCallback(
    (msg: string, durationMs = 3000) => {
      dispatch({ type: "SET_SUCCESS", payload: msg })
      setTimeout(() => {
        if (isMountedRef.current) dispatch({ type: "SET_SUCCESS", payload: null })
      }, durationMs)
    },
    []
  )

  const showError = useCallback(
    (msg: string, durationMs = 5000) => {
      dispatch({ type: "SET_ERROR", payload: msg })
      setTimeout(() => {
        if (isMountedRef.current) dispatch({ type: "SET_ERROR", payload: null })
      }, durationMs)
    },
    []
  )

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const insertVariableAtCursor = useCallback(
    (variable: string) => {
      if (!state.editingTemplate || !bodyTextareaRef.current) return

      const textarea = bodyTextareaRef.current
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = state.editingTemplate.body

      const newText = text.substring(0, start) + variable + text.substring(end)
      dispatch({
        type: "SET_EDITING_TEMPLATE",
        payload: state.editingTemplate ? { ...state.editingTemplate, body: newText } : null,
      })

      setTimeout(() => {
        textarea.focus()
        const newCursorPos = start + variable.length
        textarea.setSelectionRange(newCursorPos, newCursorPos)
      }, 0)
    },
    [state.editingTemplate]
  )

  const handleChannelFilterChange = useCallback(
    (channel: "all" | "email" | "whatsapp") => {
      dispatch({ type: "SET_CHANNEL_FILTER", payload: channel })
      dispatch({ type: "SELECT_TEMPLATE", payload: null })
      dispatch({ type: "SET_EDITING_TEMPLATE", payload: null })
    },
    []
  )

  const handleToggleWeeklyDigest = useCallback(async () => {
    dispatch({ type: "SET_SAVING_WEEKLY_DIGEST", payload: true })
    const newValue = !weeklyDigestEnabled
    try {
      const res = await apiFetch("/api/backend-proxy/digest/weekly/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: newValue }),
      })
      if (res.ok) {
        queryClient.setQueryData<boolean>(["weekly-digest-preference"], newValue)
        notifyChatOfSettingsUpdate({
          actionId: "toggle_weekly_digest",
          section: "communication",
          field: "weekly_digest",
          value: newValue,
        })
        showSuccess(newValue ? "Resumo semanal ativado" : "Resumo semanal desativado")
      }
    } catch {
      showError("Erro ao atualizar preferencia do resumo semanal")
    } finally {
      dispatch({ type: "SET_SAVING_WEEKLY_DIGEST", payload: false })
    }
  }, [weeklyDigestEnabled, queryClient, showSuccess, showError])

  // fetchData kept for backward-compat with CommunicationHub.tsx useEffect
  const fetchData = useCallback(async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["communication-templates"] }),
      queryClient.invalidateQueries({ queryKey: ["communication-settings"] }),
      queryClient.invalidateQueries({ queryKey: ["weekly-digest-preference"] }),
    ])
  }, [queryClient])

  const saveCommunicationSettings = useCallback(async () => {
    try {
      dispatch({ type: "SET_SAVING_SETTINGS", payload: true })
      dispatch({ type: "SET_ERROR", payload: null })

      const response = await apiFetch("/api/backend-proxy/company/communication-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signature,
          sending_hours_start: sendingHours.start,
          sending_hours_end: sendingHours.end,
          respect_holidays: respectHolidays,
          respect_weekends: respectWeekends,
          max_messages_per_day: maxMessagesPerDay,
          lgpd_compliant: true,
        }),
      })

      if (!response.ok) {
        throw new Error("Falha ao salvar configuracoes")
      }

      await queryClient.invalidateQueries({ queryKey: ["communication-settings"] })

      notifyChatOfSettingsUpdate({
        actionId: "configure_communication_settings",
        section: "communication",
        field: "settings",
        value: {
          sendingHoursStart: sendingHours.start,
          sendingHoursEnd: sendingHours.end,
          maxPerDay: maxMessagesPerDay,
        },
      })
      showSuccess("Configuracoes salvas com sucesso!")
    } catch (err) {
      showError(err instanceof Error ? err.message : "Erro ao salvar configuracoes")
    } finally {
      dispatch({ type: "SET_SAVING_SETTINGS", payload: false })
    }
  }, [
    signature,
    sendingHours,
    respectHolidays,
    respectWeekends,
    maxMessagesPerDay,
    queryClient,
    showSuccess,
    showError,
  ])

  const saveTemplateToAPI = useCallback(
    async (template: EmailTemplate) => {
      try {
        dispatch({ type: "SET_SAVING", payload: true })
        const response = await apiFetch(`/api/backend-proxy/email-templates/${template.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: template.name,
            category: template.category,
            subject: template.subject,
            body_html: template.body,
            variables: template.variables,
            is_active: template.isActive,
          }),
        })

        if (!response.ok) {
          throw new Error("Falha ao salvar template")
        }

        await queryClient.invalidateQueries({ queryKey: ["communication-templates"] })

        notifyChatOfSettingsUpdate({
          actionId: "update_email_template",
          section: "communication",
          field: template.name,
          value: template.category,
        })
        showSuccess("Template salvo com sucesso!")
      } catch (err) {
        showError(err instanceof Error ? err.message : "Erro ao salvar")
      } finally {
        dispatch({ type: "SET_SAVING", payload: false })
      }
    },
    [queryClient, showSuccess, showError]
  )

  const handleAdjustWithAI = useCallback(async () => {
    if (!state.editingTemplate || !state.aiPrompt.trim()) return

    dispatch({ type: "SET_IS_GENERATING", payload: true })
    try {
      const response = await apiFetch("/api/backend-proxy/email-templates/adjust", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_id: state.editingTemplate.id,
          prompt: state.aiPrompt,
          current_subject: state.editingTemplate.subject || "",
          current_body: state.editingTemplate.body,
          channel: state.editingTemplate.channel || "email",
        }),
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          dispatch({
            type: "SET_AI_RESULT_MODAL",
            payload: {
              show: true,
              newSubject: result.data.subject || state.editingTemplate.subject,
              newBody: result.data.body,
              changesMade: result.data.changes_made || ["Ajustes aplicados"],
            },
          })
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        showError(errorData.details?.detail || `Erro ao ajustar template com ${personaName}`)
      }
    } catch {
      showError("Erro ao conectar com o servico de IA")
    } finally {
      dispatch({ type: "SET_IS_GENERATING", payload: false })
      dispatch({ type: "SET_AI_PROMPT", payload: "" })
    }
  }, [state.editingTemplate, state.aiPrompt, showError])

  const handleConfirmAIAdjustment = useCallback(() => {
    if (!state.aiResultModal || !state.editingTemplate) return
    dispatch({
      type: "SET_EDITING_TEMPLATE",
      payload: state.editingTemplate
        ? {
            ...state.editingTemplate,
            subject: state.aiResultModal.newSubject,
            body: state.aiResultModal.newBody,
          }
        : null,
    })
    showSuccess(
      `Ajustes de ${personaName} aplicados. Clique em \"Salvar\" para confirmar as alteracoes.`,
      5000
    )
    dispatch({ type: "SET_AI_RESULT_MODAL", payload: null })
  }, [state.aiResultModal, state.editingTemplate, showSuccess])

  const handleCancelAIAdjustment = useCallback(() => {
    dispatch({ type: "SET_AI_RESULT_MODAL", payload: null })
  }, [])

  const handleSaveTemplate = useCallback(async () => {
    if (!state.editingTemplate) return

    const updatedTemplate = {
      ...state.editingTemplate,
      lastUpdated: new Date().toISOString().split("T")[0],
    }
    dispatch({ type: "SET_EDITING_TEMPLATE", payload: null })
    await saveTemplateToAPI(updatedTemplate)
  }, [state.editingTemplate, saveTemplateToAPI])

  // ---------------------------------------------------------------------------
  // Setters (backward-compat shims -- keep public API identical to v1)
  // ---------------------------------------------------------------------------

  const setActiveTab = useCallback(
    (tab: string) => dispatch({ type: "SET_TAB", payload: tab }),
    []
  )
  const setSelectedTemplate = useCallback(
    (t: EmailTemplate | null) => dispatch({ type: "SELECT_TEMPLATE", payload: t }),
    []
  )
  const setEditingTemplate = useCallback(
    (t: EmailTemplate | null | ((prev: EmailTemplate | null) => EmailTemplate | null)) => {
      if (typeof t === "function") {
        dispatch({ type: "SET_EDITING_TEMPLATE", payload: t(state.editingTemplate) })
      } else {
        dispatch({ type: "SET_EDITING_TEMPLATE", payload: t })
      }
    },
    [state.editingTemplate]
  )
  const setAiPrompt = useCallback(
    (v: string) => dispatch({ type: "SET_AI_PROMPT", payload: v }),
    []
  )
  const setTriggerTypeFilter = useCallback(
    (v: "all" | "automatic" | "manual" | "both") =>
      dispatch({ type: "SET_TRIGGER_FILTER", payload: v }),
    []
  )
  const setSearchQuery = useCallback(
    (v: string) => dispatch({ type: "SET_SEARCH_QUERY", payload: v }),
    []
  )
  const setExpandedGroups = useCallback(
    (v: string[] | ((prev: string[]) => string[])) => {
      if (typeof v === "function") {
        dispatch({ type: "SET_EXPANDED_GROUPS", payload: v(state.expandedGroups) })
      } else {
        dispatch({ type: "SET_EXPANDED_GROUPS", payload: v })
      }
    },
    [state.expandedGroups]
  )
  const setIsEditingSignature = useCallback(
    (v: boolean) => dispatch({ type: "SET_IS_EDITING_SIGNATURE", payload: v }),
    []
  )
  const setIsEditingSchedule = useCallback(
    (v: boolean) => dispatch({ type: "SET_IS_EDITING_SCHEDULE", payload: v }),
    []
  )

  // Signature/schedule setters write back via query client optimistic update
  const setSignature = useCallback(
    (v: string) => {
      queryClient.setQueryData<CommunicationSettings>(["communication-settings"], (prev) =>
        prev ? { ...prev, signature: v } : { ...communicationSettingsDefaults(), signature: v }
      )
    },
    [queryClient]
  )
  const setSendingHours = useCallback(
    (
      v:
        | { start: number; end: number }
        | ((prev: { start: number; end: number }) => { start: number; end: number })
    ) => {
      queryClient.setQueryData<CommunicationSettings>(["communication-settings"], (prev) => {
        const base = prev ?? communicationSettingsDefaults()
        const next = typeof v === "function" ? v(base.sendingHours) : v
        return { ...base, sendingHours: next }
      })
    },
    [queryClient]
  )
  const setRespectHolidays = useCallback(
    (v: boolean) => {
      queryClient.setQueryData<CommunicationSettings>(["communication-settings"], (prev) =>
        prev
          ? { ...prev, respectHolidays: v }
          : { ...communicationSettingsDefaults(), respectHolidays: v }
      )
    },
    [queryClient]
  )
  const setRespectWeekends = useCallback(
    (v: boolean) => {
      queryClient.setQueryData<CommunicationSettings>(["communication-settings"], (prev) =>
        prev
          ? { ...prev, respectWeekends: v }
          : { ...communicationSettingsDefaults(), respectWeekends: v }
      )
    },
    [queryClient]
  )
  const setMaxMessagesPerDay = useCallback(
    (v: number) => {
      queryClient.setQueryData<CommunicationSettings>(["communication-settings"], (prev) =>
        prev
          ? { ...prev, maxMessagesPerDay: v }
          : { ...communicationSettingsDefaults(), maxMessagesPerDay: v }
      )
    },
    [queryClient]
  )

  return {
    // State (from reducer)
    activeTab: state.activeTab,
    setActiveTab,
    selectedTemplate: state.selectedTemplate,
    setSelectedTemplate,
    editingTemplate: state.editingTemplate,
    setEditingTemplate,
    aiPrompt: state.aiPrompt,
    setAiPrompt,
    aiResultModal: state.aiResultModal,
    bodyTextareaRef,
    isGenerating: state.isGenerating,
    channelFilter: state.channelFilter,
    triggerTypeFilter: state.triggerTypeFilter,
    setTriggerTypeFilter,
    searchQuery: state.searchQuery,
    setSearchQuery,
    expandedGroups: state.expandedGroups,
    setExpandedGroups,
    isEditingSignature: state.isEditingSignature,
    setIsEditingSignature,
    isEditingSchedule: state.isEditingSchedule,
    setIsEditingSchedule,
    saving: state.saving,
    savingSettings: state.savingSettings,
    savingWeeklyDigest: state.savingWeeklyDigest,
    error: state.error,
    successMessage: state.successMessage,
    // Server state (from React Query)
    templates,
    loading,
    signature,
    setSignature,
    sendingHours,
    setSendingHours,
    respectHolidays,
    setRespectHolidays,
    respectWeekends,
    setRespectWeekends,
    maxMessagesPerDay,
    setMaxMessagesPerDay,
    weeklyDigestEnabled,
    companyId,
    // Derived
    filteredTemplates,
    groupedTemplates,
    // Handlers
    handleChannelFilterChange,
    insertVariableAtCursor,
    fetchData,
    saveCommunicationSettings,
    handleAdjustWithAI,
    handleConfirmAIAdjustment,
    handleCancelAIAdjustment,
    handleSaveTemplate,
    handleToggleWeeklyDigest,
  }
}
