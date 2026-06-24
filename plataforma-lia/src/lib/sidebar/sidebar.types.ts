/**
 * sidebar.types.ts
 *
 * Framework-agnostic interfaces for the Sidebar component.
 * Designed for portability: React today, Vue 3 tomorrow.
 *
 * Vue 3 portability notes:
 * - SidebarProps maps 1:1 to defineProps<SidebarProps>()
 * - SidebarState maps 1:1 to reactive<SidebarState>() or ref()
 * - No JSX types here — only plain data contracts
 *
 * @version 1.0.0
 * @sprint F2-6
 */

import type { RecentItem } from "@/hooks/shared/use-recent-items"

// ─── Menu Item ─────────────────────────────────────────────────────────────

/**
 * A single navigable item in the sidebar menu tree.
 * icon is kept as React.ElementType here; in Vue, replace with
 * a Component type (e.g. `DefineComponent | FunctionalComponent`).
 */
export interface MenuItemType {
  /** Lucide icon component (framework-specific — swap for Vue equivalent) */
  icon: React.ElementType
  /** Display label — also used as navigation key */
  label: string
  /** Core items are always accessible, no module check required */
  isCore?: boolean
  /** License module ID for gated features */
  moduleId?: string
  /** Visual premium badge indicator */
  isPremium?: boolean
  /** Visual beta badge indicator — marks features in testing phase */
  isBeta?: boolean
  /** Visual draft badge indicator — marks features in draft/WIP phase */
  isDraft?: boolean
  /** Nested navigation items */
  subItems?: MenuItemType[]
  /** Custom navigation key (used instead of label when set) */
  navKey?: string
  /** If true, clicking navigates to the parent page AND expands sub-items */
  navigateOnClick?: boolean
  /** If true, sub-items are always visible (no expand/collapse chevron) */
  alwaysExpanded?: boolean
  /** Maximum visible sub-items before "ver todos" link (default: unlimited) */
  maxVisibleSubItems?: number
  /** Label for "see all" link when sub-items exceed maxVisibleSubItems */
  seeAllLabel?: string
  /** Navigation target for the "see all" link */
  seeAllTarget?: string
  /** Highlights this item as the LIA differentiator (purple left accent) */
  isDifferentiator?: boolean
  /** Marks this as a coming-soon placeholder — visually dimmed */
  isFuturo?: boolean
}

// ─── Job Filter Item ────────────────────────────────────────────────────────

export interface JobFilterItemType {
  icon: React.ElementType
  label: string
  value: string
  count?: number
}

// ─── Sidebar Props ──────────────────────────────────────────────────────────

/**
 * Public API contract for the Sidebar component.
 * In Vue: defineProps<SidebarProps>()
 */
export interface SidebarProps {
  /** Currently active page label */
  currentPage: string
  /** Navigation callback — emits page label */
  onNavigate: (page: string) => void
  /** Active job filter value (optional, page-specific) */
  jobFilter?: string
  /** Job filter change callback */
  onJobFilterChange?: (filter: string) => void
  /** Recent items list for the history section */
  recentItems?: RecentItem[]
  /** Callback when a recent item is clicked */
  onRecentItemClick?: (item: RecentItem) => void
  /** Callback to remove a specific recent item */
  onRecentItemRemove?: (id: string, type: RecentItem["type"]) => void
  /** Callback to clear all recent items */
  onRecentItemsClear?: () => void
  /** Callback to open global search modal */
  onShowSearch?: () => void
  /** Whether the notification panel is open (attached mode) */
  notificationOpen?: boolean
  /** Toggle notification panel (attached mode) */
  onNotificationToggle?: () => void
}

// ─── Sidebar State ──────────────────────────────────────────────────────────

/**
 * Internal state shape of the Sidebar.
 * Extracted for framework-agnostic portability.
 *
 * React: managed via useState/useReducer in useSidebarState hook.
 * Vue 3: use reactive<SidebarState>() or individual ref()s.
 */
export interface SidebarState {
  /** Whether the sidebar is fully collapsed to icon-only mode */
  isCollapsed: boolean
  /** Whether a hover-triggered temporary expansion is active */
  isTemporaryExpanded: boolean
  /** Current pixel width of the sidebar (user-resizable) */
  sidebarWidth: number
  /** Whether the user is actively dragging the resize handle */
  isResizing: boolean
  /** Whether the component has mounted (SSR guard) */
  isMounted: boolean
  /** Whether the LIA Tips modal is visible */
  showTipsModal: boolean
}

// ─── Derived / Computed ─────────────────────────────────────────────────────

/**
 * Values computed from SidebarState.
 * In Vue 3: map each field to a computed() ref.
 */
export interface SidebarComputed {
  /** True when label/content should be rendered (not collapsed, or hover-expanded) */
  shouldShowContent: boolean
  /** CSS width string to apply to the sidebar container */
  dynamicWidth: string
}

// ─── Events (Vue 3 emit contract) ───────────────────────────────────────────

/**
 * Vue 3 emit interface — kept here for documentation parity.
 * React equivalent: the callback props in SidebarProps.
 *
 * Usage in Vue:
 *   const emit = defineEmits<SidebarEmits>()
 */
export interface SidebarEmits {
  (event: "navigate", page: string): void
  (event: "jobFilterChange", filter: string): void
  (event: "recentItemClick", item: RecentItem): void
  (event: "recentItemRemove", id: string, type: RecentItem["type"]): void
  (event: "recentItemsClear"): void
  (event: "showSearch"): void
}

// ─── localStorage Keys ───────────────────────────────────────────────────────

export const SIDEBAR_STORAGE_KEYS = {
  COLLAPSED: "sidebar-collapsed",
  WIDTH: "sidebar-width",
} as const

// ─── Constants ───────────────────────────────────────────────────────────────

export const SIDEBAR_DEFAULTS = {
  WIDTH: 256,
  MIN_WIDTH: 180,
  MAX_WIDTH: 400,
  COLLAPSED_WIDTH: "64px",
} as const
