"use client"

import React from"react"
import { Database, Plus, ChevronDown, ChevronRight, Bot } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { textStyles, badgeStyles } from"@/lib/design-tokens"
import { useTalentPools, TalentPoolSummary } from"./useTalentPools"

/**
 * TalentPoolsSidebar — sidebar section for Talent Pools.
 *
 * Designed to be inserted into the main app sidebar navigation.
 * Follows the existing collapsible section pattern from settings-page-enhanced.tsx.
 *
 * Usage:
 *   <TalentPoolsSidebar
 *     activePoolId={selectedPoolId}
 *     onSelectPool={(id) => navigate(`/talent-pools/${id}`)}
 *     onCreatePool={() => setShowCreateModal(true)}
 *   />
 */

interface TalentPoolsSidebarProps {
  activePoolId?: string | null
  onSelectPool: (poolId: string) => void
  onCreatePool: () => void
  isCollapsed?: boolean
}

export default function TalentPoolsSidebar({
  activePoolId,
  onSelectPool,
  onCreatePool,
  isCollapsed = false,
}: TalentPoolsSidebarProps) {
  const { activePools, isLoading } = useTalentPools()
  const [isExpanded, setIsExpanded] = React.useState(true)

  if (isCollapsed) {
    return (
      <div className="py-2 px-3" title="Bancos de Talentos">
        <Database className="w-5 h-5 text-lia-text-tertiary mx-auto" />
      </div>
    )
  }

  return (
    <div className="py-1">
      {/* Section header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-lia-bg-tertiary rounded-xl transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-lia-text-tertiary" />
          <span className={textStyles.sidebarTitle}>Bancos de Talentos</span>
        </div>
        <div className="flex items-center gap-1">
          {activePools.length > 0 && (
            <Chip variant="neutral" muted className={badgeStyles.success}>{activePools.length}</Chip>
          )}
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-lia-text-tertiary" />
          )}
        </div>
      </button>

      {/* Pool items */}
      {isExpanded && (
        <div className="mt-1 space-y-0.5">
          {isLoading ? (
            <p className={`px-3 py-1 ${textStyles.caption}`}>Carregando...</p>
          ) : activePools.length === 0 ? (
            <p className={`px-3 py-1 ${textStyles.caption}`}>Nenhum banco ativo</p>
          ) : (
            activePools.map(pool => (
              <PoolItem
                key={pool.id}
                pool={pool}
                isActive={activePoolId === pool.id}
                onClick={() => onSelectPool(pool.id)}
              />
            ))
          )}

          {/* Create new */}
          <button
            onClick={onCreatePool}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-lia-text-tertiary hover:bg-lia-bg-tertiary hover:text-lia-text-secondary rounded-xl transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className={textStyles.sidebarItem}>Novo banco</span>
          </button>
        </div>
      )}
    </div>
  )
}

function PoolItem({
  pool,
  isActive,
  onClick,
}: {
  pool: TalentPoolSummary
  isActive: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-1.5 rounded-md transition-colors ${
        isActive ?"bg-lia-bg-tertiary text-lia-text-primary" :"text-lia-text-secondary hover:bg-lia-bg-secondary"
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {pool.agent_sourcing_enabled && (
          <Bot className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0" />
        )}
        <span className={`${textStyles.sidebarItem} truncate`}>{pool.name}</span>
      </div>
      <span className={`${textStyles.caption} flex-shrink-0 ml-2`}>
        {pool.candidates_count}
      </span>
    </button>
  )
}
