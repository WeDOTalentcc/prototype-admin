"use client"

import React, { useState, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import {
  Users,
  Search,
  Briefcase,
  Brain,
  Star,
  Check,
  UserPlus,
  Mail,
  Megaphone,
} from "lucide-react"

interface JobAssignRecruiterModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    recruiter?: string
    recruiter_id?: string
  }>
  recruiters: Array<{
    id: string
    name: string
    email?: string
    avatar?: string
    active_jobs_count?: number
    performance_score?: number
  }>
  onAssign: (jobIds: string[], recruiterId: string, options: {
    notifyRecruiter?: boolean
    transferCommunications?: boolean
  }) => void
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

export function JobAssignRecruiterModal({
  isOpen,
  onClose,
  jobs,
  recruiters,
  onAssign,
}: JobAssignRecruiterModalProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedRecruiterId, setSelectedRecruiterId] = useState<string | null>(null)
  const [notifyRecruiter, setNotifyRecruiter] = useState(true)
  const [transferCommunications, setTransferCommunications] = useState(false)

  const safeRecruiters = React.useMemo(() => recruiters ?? [], [recruiters])

  const filteredRecruiters = useMemo(() => {
    if (!searchTerm.trim()) return safeRecruiters
    const term = searchTerm.toLowerCase()
    return safeRecruiters.filter(
      (r) =>
        r.name.toLowerCase().includes(term) ||
        (r.email && r.email.toLowerCase().includes(term))
    )
  }, [safeRecruiters, searchTerm])

  const recommendedRecruiter = useMemo(() => {
    if (safeRecruiters.length === 0) return null
    return safeRecruiters.reduce((best, current) => {
      const currentScore =
        (current.performance_score || 0) - (current.active_jobs_count || 0) * 2
      const bestScore =
        (best.performance_score || 0) - (best.active_jobs_count || 0) * 2
      return currentScore > bestScore ? current : best
    }, safeRecruiters[0])
  }, [safeRecruiters])

  const handleAssign = () => {
    if (!selectedRecruiterId) return
    onAssign(
      jobs.map((j) => j.id),
      selectedRecruiterId,
      {
        notifyRecruiter,
        transferCommunications,
      }
    )
    onClose()
  }

  const handleClose = () => {
    setSearchTerm("")
    setSelectedRecruiterId(null)
    setNotifyRecruiter(true)
    setTransferCommunications(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle rounded-xl" data-testid="assign-recruiter-modal">
        <DialogHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <Users className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Atribuir Recrutador
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Vagas Selecionadas
                </h4>
                <div className="space-y-1.5 max-h-[120px] overflow-y-auto">
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-xl bg-lia-bg-primary border border-lia-border-subtle flex items-center justify-center flex-shrink-0">
                          <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            {job.code && (
                              <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                                {job.code}
                              </span>
                            )}
                            <span className="text-base-ui font-semibold text-lia-text-primary truncate">
                              {job.title}
                            </span>
                          </div>
                          <span className="text-xs text-lia-text-secondary">
                            Atual: {job.recruiter || "Não definido"}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Opções
                </h4>
                <div className="space-y-2 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="notify"
                      checked={notifyRecruiter}
                      onCheckedChange={(checked) =>
                        setNotifyRecruiter(checked === true)
                      }
                      className="border-lia-border-subtle data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                    />
                    <Label
                      htmlFor="notify"
                      className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1"
                    >
                      <Megaphone className="w-3 h-3 text-lia-text-muted" />
                      Notificar recrutador sobre atribuição
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="transfer"
                      checked={transferCommunications}
                      onCheckedChange={(checked) =>
                        setTransferCommunications(checked === true)
                      }
                      className="border-lia-border-subtle data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                    />
                    <Label
                      htmlFor="transfer"
                      className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1"
                    >
                      <Mail className="w-3 h-3 text-lia-text-muted" />
                      Transferir comunicações pendentes
                    </Label>
                  </div>
                </div>
              </div>

              {recommendedRecruiter && (
                <div className="p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                  <div className="flex items-start gap-2">
                    <div className="w-6 h-6 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                    </div>
                    <div>
                      <h5 className="text-xs font-semibold text-lia-text-primary mb-0.5">
                        Sugestão da LIA
                      </h5>
                      <p className="text-xs text-lia-text-primary leading-relaxed">
                        Recomendo <strong>{recommendedRecruiter.name}</strong> ({recommendedRecruiter.active_jobs_count ?? 0} vagas, {recommendedRecruiter.performance_score ?? 0}% perf.)
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                Selecionar Recrutador
              </h4>
              <div className="relative mb-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-muted" />
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar recrutador..."
                  className="h-8 pl-9 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                />
              </div>

              <div className="space-y-1.5 max-h-chart-sm overflow-y-auto border border-lia-border-subtle rounded-xl p-2">
                {filteredRecruiters.length === 0 ? (
                  <div className="text-center py-4 text-xs text-lia-text-tertiary">
                    Nenhum recrutador encontrado
                  </div>
                ) : (
                  filteredRecruiters.map((recruiter) => {
                    const isRecommended = recommendedRecruiter?.id === recruiter.id
                    const isSelected = selectedRecruiterId === recruiter.id

                    return (
                      <div
                        key={recruiter.id}
                        onClick={() => setSelectedRecruiterId(recruiter.id)}
                        className={`p-2.5 rounded-md cursor-pointer transition-colors motion-reduce:transition-none ${
                          isSelected
                            ? "bg-lia-bg-tertiary border-2 border-lia-btn-primary-bg"
                            : "bg-lia-bg-secondary border border-lia-border-subtle hover:border-lia-border-medium"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Avatar className="w-8 h-8">
                            {recruiter.avatar ? (
                              <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                            ) : null}
                            <AvatarFallback className={`text-micro font-medium ${isRecommended ? "bg-lia-bg-tertiary text-lia-text-secondary" : "bg-lia-bg-tertiary text-lia-text-secondary"}`}>
                              {getInitials(recruiter.name)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs font-semibold text-lia-text-primary truncate">
                                {recruiter.name}
                              </span>
                              {isRecommended && (
                                <span className="flex items-center gap-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                                  <Star className="w-2.5 h-2.5" />
                                  Recom.
                                </span>
                              )}
                              {isSelected && (
                                <Check className="w-3.5 h-3.5 text-lia-text-primary ml-auto flex-shrink-0" />
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
                              <span>{recruiter.active_jobs_count ?? 0} vagas</span>
                              <span>Perf: {recruiter.performance_score ?? 0}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="pt-3 border-t border-lia-border-subtle bg-lia-bg-secondary gap-2">
          <Button
            variant="outline"
            onClick={handleClose}
            className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg text-lia-text-secondary"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleAssign}
            disabled={!selectedRecruiterId}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active disabled:opacity-50"
          >
            <UserPlus className="w-3.5 h-3.5 mr-1.5" />
            Atribuir Recrutador
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
