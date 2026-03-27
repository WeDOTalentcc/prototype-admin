"use client"

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
          <DialogTitle className="flex items-center gap-2 text-lg dark:text-gray-50">
            <Plus className="w-5 h-5 text-gray-700" />
            Nova Nota de Entrevista
          </DialogTitle>
          <DialogDescription className="dark:text-gray-400">
            Crie uma nota de entrevista avulsa (ad-hoc) para uma entrevista não agendada.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          {/* Candidate Selection */}
          <div className="space-y-2">
            <Label htmlFor="candidate" className="text-sm font-medium text-gray-800 dark:text-gray-200">
              Candidato *
            </Label>
            <div className="relative">
              <User
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
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
            <Label htmlFor="interview-date" className="text-sm font-medium text-gray-800 dark:text-gray-200">
              Data da Entrevista *
            </Label>
            <div className="relative">
              <Calendar
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
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
            <Label htmlFor="job" className="text-sm font-medium text-gray-800 dark:text-gray-200">
              Vincular a uma vaga
            </Label>
            <div className="relative">
              <Briefcase
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
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
              className="flex gap-3 rounded-md p-3 text-sm"
              style={{
                backgroundColor: "rgba(229, 231, 235, 0.3)",
                border: "1px solid rgba(96, 190, 209, 0.3)",
              }}
            >
              <AlertCircle
                className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700"
              />
              <p className="text-gray-800">
                Ao vincular a uma vaga, perguntas sugeridas serão geradas automaticamente.
              </p>
            </div>
          )}

          {/* Initial Notes */}
          <div className="space-y-2">
            <Label htmlFor="initial-notes" className="text-sm font-medium text-gray-800 dark:text-gray-200">
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

        <DialogFooter className="gap-3 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700 pt-4">
          <Button variant="outline" onClick={onClose} className="dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid}
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 disabled:bg-gray-300 disabled:text-gray-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Criar Nota
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
