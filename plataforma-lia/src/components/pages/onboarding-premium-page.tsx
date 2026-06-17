"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Users, Settings, BarChart3, Crown, Workflow, MessageSquare
} from "lucide-react"
import { type ApprovedCandidate, approvedCandidates } from "./onboarding-premium-types"
import { OnboardingKanbanView } from "./OnboardingKanbanView"
import { OnboardingTemplatesView } from "./OnboardingTemplatesView"
import { CandidateOnboardingModal } from "./CandidateOnboardingModal"

export function OnboardingPremiumPage() {
  const [selectedView, setSelectedView] = useState<'kanban' | 'candidates' | 'templates' | 'analytics'>('kanban')
  const [selectedCandidate, setSelectedCandidate] = useState<ApprovedCandidate | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [stageFilter, setStageFilter] = useState('all')

  const handleDragStart = (e: React.DragEvent, candidate: ApprovedCandidate) => {
    e.dataTransfer.setData('candidateId', candidate.id)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetStage: string) => {
    e.preventDefault()
    const candidateId = e.dataTransfer.getData('candidateId')
  }

  const filteredCandidates = approvedCandidates.filter(candidate => {
    const matchesSearch = candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         candidate.position.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStage = stageFilter === 'all' || candidate.stage === stageFilter
    return matchesSearch && matchesStage
  })

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-sm font-semibold font-sans text-lia-text-primary mb-1 flex items-center gap-1.5">
                <Crown className="w-6 h-6 text-lia-text-secondary" />
                Onboarding Automatizado Premium
              </h1>
              <p className="text-lia-text-secondary">
                Sistema completo de integração de novos colaboradores aprovados
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <Settings className="w-4 h-4" />
                Configurações
              </Button>
              <Button variant="outline" className="gap-2">
                <BarChart3 className="w-4 h-4" />
                Relatórios
              </Button>
            </div>
          </div>

          <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-xl w-fit">
            {[
              { id: 'kanban', label: 'Kanban', icon: Workflow },
              { id: 'candidates', label: 'Colaboradores', icon: Users },
              { id: 'templates', label: 'Templates', icon: MessageSquare },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as Parameters<typeof setSelectedView>[0])}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
                  selectedView === tab.id
                    ? 'bg-lia-bg-primary text-lia-text-primary'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {selectedView === 'kanban' && (
          <OnboardingKanbanView
            filteredCandidates={filteredCandidates}
            searchTerm={searchTerm}
            stageFilter={stageFilter}
            onSearchChange={setSearchTerm}
            onStageFilterChange={setStageFilter}
            onCandidateClick={setSelectedCandidate}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            approvedCandidates={approvedCandidates}
          />
        )}
        {selectedView === 'templates' && <OnboardingTemplatesView />}
        {selectedView === 'candidates' && (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
            <h3 className="text-xs font-medium text-lia-text-primary mb-2">Lista de Colaboradores</h3>
            <p className="text-lia-text-secondary">Visão detalhada em desenvolvimento</p>
          </div>
        )}
        {selectedView === 'analytics' && (
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
            <h3 className="text-xs font-medium text-lia-text-primary mb-2">Analytics de Onboarding</h3>
            <p className="text-lia-text-secondary">Métricas detalhadas em desenvolvimento</p>
          </div>
        )}

        {selectedCandidate && (
          <CandidateOnboardingModal
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        )}
      </div>
    </div>
  )
}
