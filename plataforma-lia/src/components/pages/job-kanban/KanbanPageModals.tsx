"use client"

import React from "react"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"
import { KanbanPageModalsCore } from "./KanbanPageModalsCore"
import { KanbanPageModalsInline } from "./KanbanPageModalsInline"
import { KanbanPageModalsExtra } from "./KanbanPageModalsExtra"

export function KanbanPageModals(state: KanbanPageCoreState) {
  return (
    <>
      <KanbanPageModalsCore {...state} />
      <KanbanPageModalsInline {...state} />
      <KanbanPageModalsExtra {...state} />
    </>
  )
}
