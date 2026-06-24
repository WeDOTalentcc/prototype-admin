"use client"

import React, { useState, useEffect } from"react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from"@/components/ui/dialog"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Textarea } from"@/components/ui/textarea"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { ScrollArea } from"@/components/ui/scroll-area"
import {
  User,
  Mail,
  Phone,
  Linkedin,
  Github,
  Globe,
  MapPin,
  Briefcase,
  GraduationCap,
  AlertTriangle,
  CheckCircle,
  X,
  Plus,
  Loader2,
  Brain,
  AlertCircle,
  Tag,
  FileText,
  Edit,
} from"lucide-react"
import { cn } from"@/lib/utils"
import { LIAIcon } from"@/components/ui/lia-icon"
import type { ParsedCVResponse } from"./cv-upload-modal"

interface Experience {
  company: string
  title: string
  start_date?: string
  end_date?: string
  is_current: boolean
  description?: string
  location?: string
}

interface Education {
  institution: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
  is_completed: boolean
  description?: string
}

interface ParsedCV {
  full_name: string
  email?: string
  phone?: string
  linkedin?: string
  github?: string
  portfolio?: string
  location?: string
  summary?: string
  experiences: Experience[]
  education: Education[]
  skills: string[]
  languages: string[]
  certifications: string[]
  raw_text: string
  file_name?: string
  file_type?: string
  file_size_bytes?: number
  confidence_score: number
  extraction_notes: string[]
  parsed_at: string
}

interface JobVacancy {
  id: string
  title: string
}

interface CVPreviewProps {
  isOpen: boolean
  onClose: () => void
  parsedData: ParsedCVResponse
  onConfirm: (candidateId: string) => void
  jobVacancies?: JobVacancy[]
}

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

export function CVPreview({
  isOpen,
  onClose,
  parsedData,
  onConfirm,
  jobVacancies = [],
}: CVPreviewProps) {
  // P0-2 (2026-06-18): notify LIA which modal is open
  useLiaModalTracking('cv-preview', isOpen)
  const [editedCV, setEditedCV] = useState<ParsedCV | null>(null)
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState("")
  const [notes, setNotes] = useState("")
  const [selectedJobId, setSelectedJobId] = useState<string>("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [overrideDuplicate, setOverrideDuplicate] = useState(false)
  const [activeTab, setActiveTab] = useState("contact")

  useEffect(() => {
    if (parsedData?.parsed_cv) {
      setEditedCV({ ...parsedData.parsed_cv })
      setTags([])
      setNotes("")
      setSelectedJobId("")
      setOverrideDuplicate(false)
      setError(null)
    }
  }, [parsedData])

  if (!editedCV) return null

  const handleInputChange = (field: keyof ParsedCV, value: string) => {
    setEditedCV((prev) => prev ? { ...prev, [field]: value } : null)
  }

  const handleAddTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag])
      setNewTag("")
    }
  }

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag))
  }

  const handleAddSkill = (skill: string) => {
    if (skill && editedCV && !editedCV.skills.includes(skill)) {
      setEditedCV({ ...editedCV, skills: [...editedCV.skills, skill] })
    }
  }

  const handleRemoveSkill = (skill: string) => {
    if (editedCV) {
      setEditedCV({ ...editedCV, skills: editedCV.skills.filter((s) => s !== skill) })
    }
  }

  const handleConfirm = async () => {
    if (!editedCV) return

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch("/api/backend-proxy/cv-parser/confirm", {
        method:"POST",
        headers: {"Content-Type":"application/json",
        },
        body: JSON.stringify({
          parsed_cv: editedCV,
          override_duplicate: overrideDuplicate,
          tags,
          notes: notes || null,
          job_vacancy_id: selectedJobId || null,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail ||"Erro ao criar candidato")
      }

      const data = await response.json()

      if (data.success && data.candidate_id) {
        onConfirm(data.candidate_id)
        handleClose()
      } else {
        throw new Error(data.message ||"Erro ao criar candidato")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message :"Erro ao criar candidato")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setEditedCV(null)
    setTags([])
    setNotes("")
    setSelectedJobId("")
    setOverrideDuplicate(false)
    setError(null)
    onClose()
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return"text-status-success bg-status-success/15"
    if (score >= 0.6) return"text-status-warning bg-status-warning/15"
    return"text-wedo-orange-text bg-wedo-orange/15"
  }

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return"Alta"
    if (score >= 0.6) return"Média"
    return"Baixa"
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <LIAIcon size="sm" />
              <DialogTitle>Revisão de Currículo</DialogTitle>
            </div>
            <div className={cn("flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium",
              getConfidenceColor(editedCV.confidence_score)
            )}>
              <Brain className="w-3 h-3 text-wedo-cyan" />
              Confiança: {getConfidenceLabel(editedCV.confidence_score)} ({Math.round(editedCV.confidence_score * 100)}%)
            </div>
          </div>
          <DialogDescription>
            Revise e edite os dados extraídos antes de criar o candidato
          </DialogDescription>
        </DialogHeader>

        {parsedData.duplicate_warning && (
          <div className="flex items-start gap-3 p-3 bg-status-warning/10 border border-status-warning/30 rounded-xl">
            <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-status-warning" aria-live="polite" aria-atomic="true">
                Possível candidato duplicado
              </p>
              <p className="text-xs text-status-warning mt-1">
                {parsedData.duplicate_warning.message}
                {" -"}
                <span className="font-medium">
                  {parsedData.duplicate_warning.existing_candidate_name}
                </span>
              </p>
              <label className="flex items-center gap-2 mt-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={overrideDuplicate}
                  onChange={(e) => setOverrideDuplicate(e.target.checked)}
                  className="rounded-md border-status-warning/30"
                />
                <span className="text-xs text-status-warning">
                  Criar mesmo assim (ignorar duplicado)
                </span>
              </label>
            </div>
          </div>
        )}

        {editedCV.extraction_notes.length > 0 && (
          <div className="flex items-start gap-3 p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-xl">
            <AlertCircle className="w-5 h-5 text-lia-text-secondary flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-lia-text-secondary">
                Notas da extração
              </p>
              <ul className="text-xs text-lia-text-secondary/80 mt-1 space-y-0.5">
                {editedCV.extraction_notes.map((note, i) => (
                  <li key={i}>• {note}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="contact">Contato</TabsTrigger>
            <TabsTrigger value="experience">Experiência</TabsTrigger>
            <TabsTrigger value="skills">Habilidades</TabsTrigger>
            <TabsTrigger value="additional">Adicional</TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1 mt-4">
            <TabsContent value="contact" className="space-y-4 m-0">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Nome Completo *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="full_name"
                      value={editedCV.full_name}
                      onChange={(e) => handleInputChange("full_name", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">E-mail</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="email"
                      type="email"
                      value={editedCV.email ||""}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Telefone</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="phone"
                      value={editedCV.phone ||""}
                      onChange={(e) => handleInputChange("phone", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="location">Localização</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="location"
                      value={editedCV.location ||""}
                      onChange={(e) => handleInputChange("location", e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="linkedin">LinkedIn</Label>
                  <div className="relative">
                    <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="linkedin"
                      value={editedCV.linkedin ||""}
                      onChange={(e) => handleInputChange("linkedin", e.target.value)}
                      className="pl-10"
                      placeholder="linkedin.com/in/..."
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="github">GitHub</Label>
                  <div className="relative">
                    <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="github"
                      value={editedCV.github ||""}
                      onChange={(e) => handleInputChange("github", e.target.value)}
                      className="pl-10"
                      placeholder="github.com/..."
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="summary">Resumo Profissional</Label>
                <Textarea
                  id="summary"
                  value={editedCV.summary ||""}
                  onChange={(e) => handleInputChange("summary", e.target.value)}
                  rows={3}
                />
              </div>
            </TabsContent>

            <TabsContent value="experience" className="space-y-4 m-0">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-lia-text-primary" />
                  <h3 className="font-medium text-sm">Experiências Profissionais</h3>
                  <Chip density="relaxed" variant="neutral" muted >
                    {editedCV.experiences.length}
                  </Chip>
                </div>

                {editedCV.experiences.length === 0 ? (
                  <p className="text-sm text-lia-text-primary italic">Nenhuma experiência extraída</p>
                ) : (
                  <div className="space-y-3">
                    {editedCV.experiences.map((exp, i) => (
                      <Card key={i} className="bg-lia-bg-secondary">
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium text-sm">{exp.title}</p>
                              <p className="text-xs text-lia-text-secondary">{exp.company}</p>
                              <p className="text-xs text-lia-text-primary">
                                {exp.start_date ||"?"} - {exp.is_current ?"Atual" : exp.end_date ||"?"}
                                {exp.location && ` • ${exp.location}`}
                              </p>
                            </div>
                            {exp.is_current && (
                              <Chip density="relaxed" variant="neutral" >Atual</Chip>
                            )}
                          </div>
                          {exp.description && (
                            <p className="text-xs text-lia-text-secondary mt-2 line-clamp-2">{exp.description}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-lia-text-primary" />
                  <h3 className="font-medium text-sm">Formação Acadêmica</h3>
                  <Chip density="relaxed" variant="neutral" muted >
                    {editedCV.education.length}
                  </Chip>
                </div>

                {editedCV.education.length === 0 ? (
                  <p className="text-sm text-lia-text-primary italic">Nenhuma formação extraída</p>
                ) : (
                  <div className="space-y-3">
                    {editedCV.education.map((edu, i) => (
                      <Card key={i} className="bg-lia-bg-secondary">
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium text-sm">
                                {edu.degree ||"Formação"}{edu.field_of_study && ` em ${edu.field_of_study}`}
                              </p>
                              <p className="text-xs text-lia-text-secondary">{edu.institution}</p>
                              <p className="text-xs text-lia-text-primary">
                                {edu.start_date ||"?"} - {edu.is_completed ? edu.end_date ||"Concluído" :"Em andamento"}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="skills" className="space-y-4 m-0">
              <div className="space-y-3">
                <Label>Habilidades</Label>
                <div className="flex flex-wrap gap-2">
                  {editedCV.skills.map((skill) => (
                    <Chip variant="neutral" muted key={skill} className="bg-lia-bg-tertiary text-lia-text-primary px-2 py-1">
                      {skill}
                      <button
                        onClick={() => handleRemoveSkill(skill)}
                        className="ml-1 hover:text-lia-text-primary"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Chip>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Adicionar habilidade..."
                    onKeyDown={(e) => {
                      if (e.key ==="Enter") {
                        e.preventDefault()
                        handleAddSkill(e.currentTarget.value)
                        e.currentTarget.value =""
                      }
                    }}
                  />
                </div>
              </div>

              <div className="space-y-3 pt-4 border-t">
                <Label>Idiomas</Label>
                <div className="flex flex-wrap gap-2">
                  {editedCV.languages.length === 0 ? (
                    <p className="text-sm text-lia-text-primary italic">Nenhum idioma extraído</p>
                  ) : (
                    editedCV.languages.map((lang) => (
                      <Chip key={lang} variant="neutral">{lang}</Chip>
                    ))
                  )}
                </div>
              </div>

              <div className="space-y-3 pt-4 border-t">
                <Label>Certificações</Label>
                <div className="flex flex-wrap gap-2">
                  {editedCV.certifications.length === 0 ? (
                    <p className="text-sm text-lia-text-primary italic">Nenhuma certificação extraída</p>
                  ) : (
                    editedCV.certifications.map((cert) => (
                      <Chip key={cert} variant="neutral">{cert}</Chip>
                    ))
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="additional" className="space-y-4 m-0">
              <div className="space-y-3">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {tags.map((tag) => (
                    <Chip variant="neutral" muted key={tag} className="bg-lia-bg-tertiary text-lia-text-primary px-2 py-1">
                      <Tag className="w-3 h-3 mr-1" />
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-lia-text-primary"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Chip>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Adicionar tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key ==="Enter") {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                  />
                  <Button variant="outline" size="sm" onClick={handleAddTag}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2 pt-4 border-t">
                <Label htmlFor="notes">Observações</Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Notas sobre o candidato..."
                  rows={3}
                />
              </div>

              {jobVacancies.length > 0 && (
                <div className="space-y-2 pt-4 border-t">
                  <Label>Vincular a Vaga (opcional)</Label>
                  <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione uma vaga..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Nenhuma</SelectItem>
                      {jobVacancies.map((job) => (
                        <SelectItem key={job.id} value={job.id}>
                          {job.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {editedCV.file_name && (
                <div className="flex items-center gap-2 p-3 bg-lia-bg-secondary rounded-xl text-xs text-lia-text-secondary mt-4">
                  <FileText className="w-4 h-4" />
                  <span>Arquivo: {editedCV.file_name}</span>
                  {editedCV.file_type && <Chip variant="neutral">{editedCV.file_type.toUpperCase()}</Chip>}
                </div>
              )}
            </TabsContent>
          </ScrollArea>
        </Tabs>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
            <p className="text-sm text-status-error">{error}</p>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!editedCV.full_name || isSubmitting || (!!parsedData.duplicate_warning && !overrideDuplicate)}
            className="gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                Criando...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Criar Candidato
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
