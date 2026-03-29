"use client"

// quick-actions-modals.tsx
// Barrel de re-exportações — mantém compatibilidade com imports existentes.
// Cada modal foi extraído para camada própria em ./quick-actions/
// Split: ContactModal (636L), ScheduleModal (695L), QuickViewModal (531L), BatchActionModal (244L)

export { ContactModal } from "./quick-actions/contact-modal"
export { ScheduleModal } from "./quick-actions/schedule-modal"
export { QuickViewModal } from "./quick-actions/quick-view-modal"
export { BatchActionModal } from "./quick-actions/batch-action-modal"
