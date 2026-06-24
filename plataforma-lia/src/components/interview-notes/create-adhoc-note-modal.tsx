"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { AlertCircle, Calendar, Briefcase, User, Link2, Plus } from "lucide-react"

export interface CreateAdhocNoteModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateNote: (data: {
    candidateId: string
    candidateName: string
    jobId?: string
    jobTitle?: string
    interviewDate: string
    initialNotes?: string
  }) => void
  candidates: Array<{ id: string; name: string }>
  jobs: Array<{ id: string; title: string }>
}

export function CreateAdhocNoteModal({
  isOpen,
  onClose,
  onCreateNote,
  candidates,
  jobs,
}: CreateAdhocNoteModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('create-adhoc-note', isOpen)

  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("")
  const [selectedJobId, setSelectedJobId] = useState<string>("")
  const [interviewDate, setInterviewDate] = useState<string>("")
  const [initialNotes, setInitialNotes] = useState<string>("")

  // Get selected candidate and job details
  const selectedCandidate = useMemo(
    () => candidates.find((c) => c.id === selectedCandidateId),
    [selectedCandidateId, candidates]
  )

  const selectedJob = useMemo(
    () => jobs.find((j) => j.id === selectedJobId),
    [selectedJobId, jobs]
  )

  const handleSubmit = () => {
    if (!selectedCandidateId || !selectedCandidate || !interviewDate) {
      return
    }

    onCreateNote({
      candidateId: selectedCandidateId,
      candidateName: selectedCandidate.name,
      jobId: selectedJobId || undefined,
      jobTitle: selectedJob?.title || undefined,
      interviewDate,
      initialNotes: initialNotes.trim() || undefined,
    })

    // Reset form
    setSelectedCandidateId("")
    setSelectedJobId("")
    setInterviewDate("")
    setInitialNotes("")

    onClose()
  }

  const isFormValid = selectedCandidateId && interviewDate

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg rounded-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            <Plus className="w-5 h-5 text-lia-text-secondary" />
            Nova Nota de Entrevista
          </DialogTitle>
          <DialogDescription className="dark:text-lia-text-tertiary">
            Crie uma nota de entrevista avulsa (ad-hoc) para uma entrevista não agendada.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          {/* Candidate Selection */}
          <div className="space-y-2">
            <Label htmlFor="candidate" className="text-sm font-medium text-lia-text-primary">
              Candidato *
            </Label>
            <div className="relative">
              <User
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary"
              />
              <Select value={selectedCandidateId} onValueChange={setSelectedCandidateId}>
                <SelectTrigger id="candidate" className="pl-10">
                  <SelectValue placeholder="Selecione um candidato..." />
                </SelectTrigger>
                <SelectContent>
                  {candidates.map((candidate) => (
                    <SelectItem key={candidate.id} value={candidate.id}>
                      {candidate.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Interview Date */}
          <div className="space-y-2">
            <Label htmlFor="interview-date" className="text-sm font-medium text-lia-text-primary">
              Data da Entrevista *
            </Label>
            <div className="relative">
              <Calendar
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary"
              />
              <Input
                id="interview-date"
                type="datetime-local"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Job Link (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="job" className="text-sm font-medium text-lia-text-primary">
              Vincular a uma vaga
            </Label>
            <div className="relative">
              <Briefcase
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary"
              />
              <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                <SelectTrigger id="job" className="pl-10">
                  <SelectValue placeholder="Selecione uma vaga (opcional)..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Nenhuma</SelectItem>
                  {jobs.map((job) => (
                    <SelectItem key={job.id} value={job.id}>
                      {job.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Warning Alert */}
          {selectedJobId && (
            <div
              className="flex gap-3 rounded-xl p-3 text-sm bg-lia-interactive-active/30 border border-wedo-cyan/30"
            >
              <AlertCircle
                className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary"
              />
              <p className="text-lia-text-primary">
                Ao vincular a uma vaga, perguntas sugeridas serão geradas automaticamente.
              </p>
            </div>
          )}

          {/* Initial Notes */}
          <div className="space-y-2">
            <Label htmlFor="initial-notes" className="text-sm font-medium text-lia-text-primary">
              Observações iniciais
            </Label>
            <Textarea
              id="initial-notes"
              value={initialNotes}
              onChange={(e) => setInitialNotes(e.target.value)}
              placeholder="Adicione notas ou contexto sobre a entrevista (opcional)..."
              rows={4}
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter className="gap-3 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle pt-4">
          <Button variant="outline" onClick={onClose} className="dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active disabled:bg-lia-border-default disabled:text-lia-text-tertiary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Criar Nota
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
