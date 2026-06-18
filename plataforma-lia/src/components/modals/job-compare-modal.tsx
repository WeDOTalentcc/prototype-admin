"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Scale,
  Download,
  Share2,
  Target,
  Award,
  Gift,
  DollarSign,
  MapPin,
  Brain,
  Briefcase,
} from "lucide-react"
import { LiaAnalysisPanel, CandidateFunnelPanel } from "./job-compare"
import { JobCompareTable } from "./job-compare/JobCompareTable"
import { useJobCompare, type ComparisonDimension } from "./job-compare/useJobCompare"

const COMPARISON_DIMENSIONS: {
  id: ComparisonDimension
  label: string
  icon: React.ElementType
}[] = [
  { id: "technical_requirements", label: "Técnicos", icon: Target },
  { id: "competencies", label: "Competências", icon: Award },
  { id: "benefits", label: "Benefícios", icon: Gift },
  { id: "salary_range", label: "Salário", icon: DollarSign },
  { id: "location", label: "Local", icon: MapPin },
  { id: "performance", label: "Performance", icon: Brain },
]

interface JobCompareModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    department?: string
    location?: string
    work_model?: string
    salary_range?: { min?: number; max?: number }
    status: string
    deadline?: string
    candidates_count?: number
    approved_count?: number
    screening_count?: number
    performance_score?: number
    benefits?: string[]
    technical_requirements?: Record<string, unknown>[]
    behavioral_competencies?: Record<string, unknown>[]
  }>
}

export function JobCompareModal({ isOpen, onClose, jobs }: JobCompareModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('job-compare', isOpen)

  const {
    selectedDimensions,
    toggleDimension,
    isExporting,
    formatSalaryRange,
    getScoreColor,
    liaAnalysis,
    handleExportPDF,
    handleShare,
  } = useJobCompare(jobs)

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="max-w-4xl max-h-[90vh] overflow-y-auto bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
        data-testid="job-compare-modal"
      >
        <DialogHeader className=" pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
                <Scale className="w-4 h-4 text-lia-text-secondary" />
              </div>
              <div>
                <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                  Comparar Vagas
                </DialogTitle>
                <p className="text-xs text-lia-text-secondary mt-0.5">
                  {jobs.length} vaga{jobs.length > 1 ? "s" : ""} selecionada{jobs.length > 1 ? "s" : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="h-7 px-2.5 text-xs gap-1.5 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
              >
                <Share2 className="w-3 h-3" />
                Compartilhar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportPDF}
                disabled={isExporting}
                className="h-7 px-2.5 text-xs gap-1.5 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
              >
                <Download className="w-3 h-3" />
                {isExporting ? "Gerando..." : "Exportar PDF"}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="grid grid-cols-[240px_1fr] gap-4">
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Vagas Selecionadas
                </h4>
                <div className="space-y-1.5 max-h-[120px] overflow-y-auto">
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-xl bg-lia-bg-primary border border-lia-border-subtle flex items-center justify-center flex-shrink-0">
                          <Briefcase className="w-3 h-3 text-lia-text-secondary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            {job.code && (
                              <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1 py-0.5 rounded-full">
                                {job.code}
                              </span>
                            )}
                          </div>
                          <span className="text-xs font-medium text-lia-text-primary truncate block">
                            {job.title}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Dimensões
                </h4>
                <div className="space-y-1.5 p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                  {COMPARISON_DIMENSIONS.map((dim) => (
                    <label
                      key={dim.id}
                      className="flex items-center gap-2 cursor-pointer group"
                    >
                      <Checkbox
                        checked={selectedDimensions.has(dim.id)}
                        onCheckedChange={() => toggleDimension(dim.id)}
                        className="w-3.5 h-3.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                      />
                      <dim.icon className="w-3 h-3 text-lia-text-tertiary group-hover:text-lia-text-primary" />
                      <span className="text-xs text-lia-text-primary group-hover:text-lia-text-primary">
                        {dim.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <JobCompareTable
              jobs={jobs}
              selectedDimensions={selectedDimensions}
              formatSalaryRange={formatSalaryRange}
              getScoreColor={getScoreColor}
            />
          </div>

          {jobs.length >= 2 && (
            <CandidateFunnelPanel jobs={jobs} />
          )}

          {liaAnalysis && jobs.length >= 2 && (
            <LiaAnalysisPanel liaAnalysis={liaAnalysis} />
          )}
        </div>

        <DialogFooter className="pt-3 border-t border-lia-border-subtle">
          <Button
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
