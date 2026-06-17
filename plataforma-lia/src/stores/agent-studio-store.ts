"use client"

import { create } from "zustand"
import { devtools } from "zustand/middleware"
import type { AgentTemplate, CustomAgent, AgentCategory } from "@/components/pages-agent-studio/custom-agents/types"

type CreationMode = "idle" | "template" | "manual"

interface AgentStudioState {
  // Creation flow
  creationMode: CreationMode
  selectedTemplate: AgentTemplate | null
  draftAgent: Partial<CustomAgent>

  // Gallery filters
  activeCategory: AgentCategory | "all"

  // Actions
  setCreationMode: (mode: CreationMode) => void
  selectTemplate: (template: AgentTemplate) => void
  updateDraft: (partial: Partial<CustomAgent>) => void
  setActiveCategory: (category: AgentCategory | "all") => void
  reset: () => void
}

export const useAgentStudioStore = create<AgentStudioState>()(
  devtools(
    (set) => ({
      creationMode: "idle",
      selectedTemplate: null,
      draftAgent: {},
      activeCategory: "all",

      setCreationMode: (mode) => set({ creationMode: mode }),

      selectTemplate: (template) =>
        set({
          selectedTemplate: template,
          creationMode: "template",
          draftAgent: {
            name: template.name,
            role: template.description,
            description: template.description,
            system_prompt: template.system_prompt,
            allowed_tools: template.allowed_tools,
            domain: template.domain,
            icon: template.icon,
            context_level: template.context_level,
            max_steps: template.max_steps,
            temperature: template.temperature,
            enable_memory: template.enable_memory,
            excluded_tools: template.excluded_tools,
          },
        }),

      updateDraft: (partial) =>
        set((state) => ({ draftAgent: { ...state.draftAgent, ...partial } })),

      setActiveCategory: (category) => set({ activeCategory: category }),

      reset: () =>
        set({
          creationMode: "idle",
          selectedTemplate: null,
          draftAgent: {},
        }),
    }),
    { name: "agent-studio" }
  )
)
