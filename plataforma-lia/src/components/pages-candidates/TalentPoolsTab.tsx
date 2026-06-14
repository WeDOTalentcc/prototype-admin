"use client"

import React, { useState } from"react"
import { Database, Plus, Users, Bot, ArrowRight, ArrowLeft } from"lucide-react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  textStyles, cardStyles, badgeStyles, buttonStyles,
  actionButtonStyles
} from"@/lib/design-tokens"
import { useTalentPools, TalentPoolSummary } from"@/components/pages-talent-pools/useTalentPools"
import TalentPoolPage, { CreatePoolModal } from"@/components/pages-talent-pools/TalentPoolPage"

/**
 * TalentPoolsTab — tab content for"Bancos Vivos" in the Funil de Talentos page.
 *
 * Shows grid of pool cards with summary stats.
 * Integrates with existing tab system via useCandidatesActions.
 */

interface TalentPoolsTabProps {
  onSelectPool: (poolId: string, poolName: string) => void
  /** When set, renders the pool detail inline instead of the grid. */
  openPoolId?: string | null
  /** Called from the inline detail back button to return to the grid. */
  onClosePool?: () => void
}

export default function TalentPoolsTab({ onSelectPool, openPoolId, onClosePool }: TalentPoolsTabProps) {
  const { pools, activePools, isLoading, createPool } = useTalentPools()
  const [showCreateModal, setShowCreateModal] = useState(false)

  if (openPoolId) {
    return (
      <div className="space-y-4">
        <Button
          variant="ghost"
          className={`${buttonStyles.ghost} -ml-2`}
          onClick={() => onClosePool?.()}
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Voltar aos bancos
        </Button>
        <TalentPoolPage poolId={openPoolId} />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className={textStyles.caption}>Carregando bancos de talentos...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.h3}>Bancos de Talentos Vivos</h3>
          <p className={textStyles.description}>
            Bancos permanentes para captar e qualificar candidatos independentemente de vagas abertas.
          </p>
        </div>
        <Button className={buttonStyles.primary} onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-1" />
          Novo Banco
        </Button>
      </div>

      {/* Grid */}
      {activePools.length === 0 ? (
        <Card className={cardStyles.flat}>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="w-12 h-12 text-lia-text-muted mb-3" />
            <p className={textStyles.body}>Nenhum banco de talentos criado</p>
            <p className={textStyles.caption}>
              Crie um banco para captar candidatos de forma contínua.
            </p>
            <Button
              className={`${buttonStyles.outline} mt-4`}
              onClick={() => setShowCreateModal(true)}
            >
              <Plus className="w-4 h-4 mr-1" />
              Criar primeiro banco
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pools.map(pool => (
            <PoolCard key={pool.id} pool={pool} onClick={() => onSelectPool(pool.id, pool.name)} />
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreatePoolModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(id, name) => {
            setShowCreateModal(false)
            onSelectPool(id, name)
          }}
        />
      )}
    </div>
  )
}

function PoolCard({ pool, onClick }: { pool: TalentPoolSummary; onClick: () => void }) {
  const statusConfig = {
    active: { label:"Ativo", style: badgeStyles.success },
    paused: { label:"Pausado", style: badgeStyles.warning },
    archived: { label:"Arquivado", style: badgeStyles.error },
  }
  const status = statusConfig[pool.status]

  return (
    <Card
      className={`${cardStyles.default} cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="min-w-0 flex-1">
            <h4 className={`${textStyles.subtitle} truncate`}>{pool.name}</h4>
            {pool.ideal_profile_name && (
              <p className={`${textStyles.caption} truncate mt-0.5`}>
                Arquétipo: {pool.ideal_profile_name}
              </p>
            )}
          </div>
          <Chip variant="neutral" muted className={status.style}>{status.label}</Chip>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center gap-1" title="Total de candidatos">
            <Users className="w-3.5 h-3.5 text-lia-text-tertiary" />
            <span className={textStyles.bodySmall}>{pool.candidates_count}</span>
          </div>
          <div className="flex items-center gap-1" title="Candidatos triados">
            <span className={textStyles.bodySmall}>✅ {pool.screened_count}</span>
          </div>
          <div className="flex items-center gap-1" title="Prontos para mover para vaga">
            <span className={textStyles.bodySmall}>🎯 {pool.ready_count}</span>
          </div>
          {typeof pool.assignments_count === "number" && pool.assignments_count > 0 ? (
            <div className="flex items-center gap-1 ml-auto" title={`${pool.assignments_count} ${pool.assignments_count === 1 ? "agente atribuído" : "agentes atribuídos"} a este banco`}>
              <Bot className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className={textStyles.bodySmall}>
                {pool.assignments_count} {pool.assignments_count === 1 ? "agente" : "agentes"}
              </span>
            </div>
          ) : pool.agent_sourcing_enabled ? (
            <div className="flex items-center gap-1 ml-auto" title="Sourcing legacy ativo (em migração para o novo modelo de agentes)">
              <Bot className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className={textStyles.bodySmall}>Sourcing legacy</span>
            </div>
          ) : null}
        </div>

        {/* Action */}
        <div className="mt-3 pt-3 border-t border-lia-border-subtle">
          <button className="flex items-center gap-1 text-sm text-lia-text-secondary hover:text-lia-text-primary transition-colors">
            Ver candidatos <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
