import React from "react"
import { textStyles } from "@/lib/design-tokens"

interface HubHeaderProps {
  title: string
  description?: string
  /** Optional breadcrumb/section label shown above the title */
  subsection?: string
  /** Optional slot for action buttons (renders on the right) */
  children?: React.ReactNode
}

/**
 * Canonical hub-level page header for Settings hubs.
 *
 * Usage:
 *   <HubHeader title="Integracoes" description="Configure suas integracoes..." />
 *   <HubHeader title="Usuarios" subsection="Pessoas & Org" description="...">
 *     <Button size="sm">Novo</Button>
 *   </HubHeader>
 *
 * Design tokens: textStyles.h3 (title) + textStyles.description (subtitle).
 * Canonical pattern extracted from MinhaEmpresaHub, user-management, and 6 other hubs.
 */
export function HubHeader({ title, description, subsection, children }: HubHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-2">
      <div>
        {subsection && (
          <p className={`${textStyles.caption} uppercase tracking-wide mb-1`}>
            {subsection}
          </p>
        )}
        <h2 className={textStyles.h3}>{title}</h2>
        {description && (
          <p className={`${textStyles.description} mt-0.5`}>{description}</p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-3 shrink-0 ml-4">{children}</div>
      )}
    </div>
  )
}
