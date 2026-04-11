"use client"

import { Button } from "@/components/ui/button"
import {
  Users, Download, Settings, ClipboardList, TrendingUp, BarChart3
} from "lucide-react"
import { useOnboardingPage } from "./useOnboardingPage"
import type { OnboardingView } from "./useOnboardingPage"
import { OnboardingOverview } from "./onboarding-overview"
import { OnboardingCandidates } from "./onboarding-candidates"
import { OnboardingTemplates } from "./onboarding-templates"
import { CandidateDetailModal } from "./onboarding-candidate-detail-modal"

const tabs: { id: OnboardingView; label: string; icon: typeof BarChart3 }[] = [
  { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
  { id: 'candidates', label: 'Colaboradores', icon: Users },
  { id: 'templates', label: 'Templates', icon: ClipboardList },
  { id: 'analytics', label: 'Analytics', icon: TrendingUp }
]

export function OnboardingPage() {
  const {
    selectedView,
    setSelectedView,
    selectedCandidate,
    setSelectedCandidate,
    searchTerm,
    setSearchTerm,
    statusFilter,
    setStatusFilter,
    filteredCandidates
  } = useOnboardingPage()

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-sm font-semibold font-sans text-lia-text-primary mb-1">
                Onboarding Automatizado
              </h1>
              <p className="text-lia-text-secondary">
                Gerencie e automatize o processo de integração de novos colaboradores
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <Download className="w-4 h-4" />
                Exportar
              </Button>
              <Button variant="outline" className="gap-2">
                <Settings className="w-4 h-4" />
                Configurações
              </Button>
            </div>
          </div>

          <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-xl w-fit">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id)}
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

        {selectedView === 'overview' && <OnboardingOverview />}
        {selectedView === 'candidates' && (
          <OnboardingCandidates
            filteredCandidates={filteredCandidates}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            setSelectedCandidate={setSelectedCandidate}
          />
        )}
        {selectedView === 'templates' && <OnboardingTemplates />}
        {selectedView === 'analytics' && (
          <div className="text-center py-12">
            <TrendingUp className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
            <h3 className="text-xs font-medium text-lia-text-primary mb-2">Analytics em Desenvolvimento</h3>
            <p className="text-lia-text-secondary">Métricas avançadas de onboarding em breve</p>
          </div>
        )}

        {selectedCandidate && (
          <CandidateDetailModal
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        )}
      </div>
    </div>
  )
}
