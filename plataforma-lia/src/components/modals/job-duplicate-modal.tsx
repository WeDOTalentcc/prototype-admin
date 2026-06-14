"use client"

import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Copy,
  Check,
  MapPin,
  Building,
  Users,
  Calendar,
  Briefcase,
} from "lucide-react"

interface JobDuplicateModalProps {
  isOpen: boolean
  onClose: () => void
  job: {
    id: string
    code?: string
    title: string
    department?: string
    location?: string
    recruiter?: string
    recruiter_email?: string
    candidates_count?: number
    approved_count?: number
  } | null
  recruiters?: Array<{ id: string; name: string; email?: string }>
  onDuplicate: (options: {
    newTitle: string
    deadlineShortlist: string
    deadlineScreening: string
    deadlineClosing: string
    candidateOption: 'all' | 'approved' | 'none'
    recruiterId: string
  }) => void
}

const KEPT_ITEMS = [
  "Descrição da vaga",
  "Requisitos técnicos",
  "Perguntas de triagem",
  "Competências",
  "Faixa salarial",
  "Benefícios",
  "Gestor responsável",
  "Modelo de trabalho",
]

function getDefaultDate(daysFromNow: number): string {
  const date = new Date()
  date.setDate(date.getDate() + daysFromNow)
  return date.toISOString().split("T")[0]
}

export function JobDuplicateModal({
  isOpen,
  onClose,
  job,
  recruiters = [],
  onDuplicate,
}: JobDuplicateModalProps) {
  const [newTitle, setNewTitle] = useState("")
  const [deadlineShortlist, setDeadlineShortlist] = useState("")
  const [deadlineScreening, setDeadlineScreening] = useState("")
  const [deadlineClosing, setDeadlineClosing] = useState("")
  const [candidateOption, setCandidateOption] = useState<'all' | 'approved' | 'none'>('none')
  const [recruiterId, setRecruiterId] = useState("")

  useEffect(() => {
    if (isOpen && job) {
      setNewTitle(`${job.title} (Cópia)`)
      setDeadlineShortlist(getDefaultDate(30))
      setDeadlineScreening(getDefaultDate(30))
      setDeadlineClosing(getDefaultDate(30))
      setCandidateOption('none')
      const currentRecruiter = recruiters.find(r => r.email === job.recruiter_email || r.name === job.recruiter)
      setRecruiterId(currentRecruiter?.id || recruiters[0]?.id || "")
    }
  }, [isOpen, job, recruiters])

  const handleDuplicate = () => {
    onDuplicate({
      newTitle,
      deadlineShortlist,
      deadlineScreening,
      deadlineClosing,
      candidateOption,
      recruiterId,
    })
  }

  if (!job) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent data-testid="job-duplicate-modal" className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <Copy className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Duplicar Vaga
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                1 vaga selecionada
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Vaga Original
                </h4>
                <div className="flex items-start gap-2">
                  <div className="w-8 h-8 rounded-xl bg-lia-bg-primary border border-lia-border-subtle flex items-center justify-center flex-shrink-0">
                    <Briefcase className="w-4 h-4 text-lia-text-secondary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      {job.code && (
                        <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                          {job.code}
                        </span>
                      )}
                      <span className="text-base-ui font-semibold text-lia-text-primary truncate">
                        {job.title}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-lia-text-secondary">
                      {job.department && (
                        <span className="flex items-center gap-0.5">
                          <Building className="w-2.5 h-2.5" />
                          {job.department}
                        </span>
                      )}
                      {job.location && (
                        <span className="flex items-center gap-0.5">
                          <MapPin className="w-2.5 h-2.5" />
                          {job.location}
                        </span>
                      )}
                      <span className="flex items-center gap-0.5">
                        <Users className="w-2.5 h-2.5" />
                        {job.candidates_count || 0} cand.
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  O que será mantido
                </h4>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                  {KEPT_ITEMS.map((item) => (
                    <div key={item} className="flex items-center gap-1.5 text-xs text-lia-text-primary">
                      <Check className="w-3 h-3 text-status-success flex-shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Candidatos
                </h4>
                <RadioGroup
                  value={candidateOption}
                  onValueChange={(val) => setCandidateOption(val as 'all' | 'approved' | 'none')}
                  className="space-y-1"
                >
                  <div className="flex items-center space-x-2 p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                    <RadioGroupItem value="all" id="all" className="border-lia-border-medium text-lia-text-primary" />
                    <Label htmlFor="all" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
                      <Users className="w-2.5 h-2.5 text-lia-text-muted" />
                      Todos ({job.candidates_count || 0})
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                    <RadioGroupItem value="approved" id="approved" className="border-lia-border-medium text-lia-text-primary" />
                    <Label htmlFor="approved" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
                      <Check className="w-2.5 h-2.5 text-lia-text-muted" />
                      Apenas aprovados ({job.approved_count || 0})
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                    <RadioGroupItem value="none" id="none" className="border-lia-border-medium text-lia-text-primary" />
                    <Label htmlFor="none" className="text-xs text-lia-text-primary cursor-pointer">
                      Começar com base vazia
                    </Label>
                  </div>
                </RadioGroup>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Nova Vaga
                </h4>
                <div className="space-y-2">
                  <div className="space-y-1">
                    <Label className="text-xs text-lia-text-primary">Nome</Label>
                    <Input
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="Nome da nova vaga"
                      className="h-8 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-lia-text-primary">Recrutador Responsável</Label>
                    <Select value={recruiterId} onValueChange={setRecruiterId}>
                      <SelectTrigger className="h-8 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20">
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {recruiters.map((recruiter) => (
                          <SelectItem key={recruiter.id} value={recruiter.id} className="text-xs">
                            {recruiter.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
                  Novas Datas
                </h4>
                <div className="space-y-2">
                  <div className="space-y-1">
                    <Label className="text-xs text-lia-text-primary flex items-center gap-1">
                      <Calendar className="w-2.5 h-2.5 text-lia-text-muted" />
                      Deadline Short List
                    </Label>
                    <Input
                      type="date"
                      value={deadlineShortlist}
                      onChange={(e) => setDeadlineShortlist(e.target.value)}
                      className="h-8 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-lia-text-primary flex items-center gap-1">
                      <Calendar className="w-2.5 h-2.5 text-lia-text-muted" />
                      Fim da Triagem
                    </Label>
                    <Input
                      type="date"
                      value={deadlineScreening}
                      onChange={(e) => setDeadlineScreening(e.target.value)}
                      className="h-8 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-lia-text-primary flex items-center gap-1">
                      <Calendar className="w-2.5 h-2.5 text-lia-text-muted" />
                      Conclusão da Vaga
                    </Label>
                    <Input
                      type="date"
                      value={deadlineClosing}
                      onChange={(e) => setDeadlineClosing(e.target.value)}
                      className="h-8 text-xs border-lia-border-subtle focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="pt-3 border-t border-lia-border-subtle gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleDuplicate}
            disabled={!newTitle.trim() || !recruiterId}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <Copy className="w-3.5 h-3.5 mr-1.5" />
            Criar Duplicata
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
