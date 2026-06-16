"use client"

import React, { useState } from"react"
import { DEMO_VALUES } from"@/lib/pricing"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from"@/components/ui/dialog"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Textarea } from"@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent } from"@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { LIAIcon } from"@/components/ui/lia-icon"
import {
  User, Mail, Phone, Briefcase, MapPin, Calendar, FileText, Link,
  Plus, X, Upload, UserPlus, Brain, CheckCircle, AlertCircle,
  Linkedin, Github, Globe, DollarSign, Building, GraduationCap,
  Languages, Award, Target, Zap
} from"lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"

interface AddCandidateModalProps {
  isOpen: boolean
  onClose: () => void
  onAdd: (candidate: Record<string, unknown>) => void
}


interface LIAAnalysis {
  score?: number
  fitScore?: number
  culturalFit?: number
  technicalFit?: number
  strengths?: string[]
  improvements?: string[]
  recommendation?: string
  suggestedSkills?: string[]
  softSkills?: Record<string, number>
}


export function AddCandidateModal({ isOpen, onClose, onAdd }: AddCandidateModalProps) {
  const [activeTab, setActiveTab] = useState("basic")
  const [liaAnalysis] = useState<LIAAnalysis | null>(null)
  const [skills, setSkills] = useState<string[]>([])
  const [newSkill, setNewSkill] = useState("")

  // Form states
  const [formData, setFormData] = useState({
    name:"",
    email:"",
    phone:"",
    position:"",
    location:"",
    workModel:"híbrido",
    contractType:"CLT",
    currentCompany:"",
    experience:"",
    education:"",
    expectedSalary:"",
    currentSalary:"",
    linkedin:"",
    github:"",
    portfolio:"",
    resume:"",
    languages:"",
    certifications:"",
    about:""
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleAddSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()])
      setNewSkill("")
    }
  }

  const handleRemoveSkill = (skill: string) => {
    setSkills(skills.filter(s => s !== skill))
  }

  // P0-2: handleLIAAnalysis (analise fabricada via Math.random) removido.
  // Nao apresentar IA falsa; a analise real ocorre na ficha do candidato.

  const handleSubmit = () => {
    const newCandidate = {
      ...formData,
      skills,
      liaAnalysis,
      id: `NEW${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: 'active'
    }

    onAdd(newCandidate)

    // Reset form
    setFormData({
      name:"",
      email:"",
      phone:"",
      position:"",
      location:"",
      workModel:"híbrido",
      contractType:"CLT",
      currentCompany:"",
      experience:"",
      education:"",
      expectedSalary:"",
      currentSalary:"",
      linkedin:"",
      github:"",
      portfolio:"",
      resume:"",
      languages:"",
      certifications:"",
      about:""
    })
    setSkills([])
    setActiveTab("basic")

    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col bg-lia-bg-primary border-lia-border-subtle rounded-xl" data-testid="add-candidate-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="w-5 h-5 text-lia-text-secondary" />
            Adicionar Novo Candidato
          </DialogTitle>
          <DialogDescription>
            Cadastre um novo candidato no funil de talentos.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic">Dados Básicos</TabsTrigger>
            <TabsTrigger value="professional">Profissional</TabsTrigger>
            <TabsTrigger value="skills">Habilidades</TabsTrigger>
            <TabsTrigger value="analysis">Análise de Compatibilidade</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto px-1">
            <TabsContent value="basic" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome Completo *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange("name", e.target.value)}
                      placeholder="João Silva"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">E-mail *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      placeholder="joao.silva@email.com"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Telefone *</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => handleInputChange("phone", e.target.value)}
                      placeholder="(11) 99999-9999"
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
                      value={formData.location}
                      onChange={(e) => handleInputChange("location", e.target.value)}
                      placeholder="São Paulo, SP"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="workModel">Modelo de Trabalho</Label>
                  <Select value={formData.workModel} onValueChange={(value) => handleInputChange("workModel", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="presencial">Presencial</SelectItem>
                      <SelectItem value="híbrido">Híbrido</SelectItem>
                      <SelectItem value="remoto">Remoto</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contractType">Tipo de Contrato</Label>
                  <Select value={formData.contractType} onValueChange={(value) => handleInputChange("contractType", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CLT">CLT</SelectItem>
                      <SelectItem value="PJ">PJ</SelectItem>
                      <SelectItem value="Freelancer">Freelancer</SelectItem>
                      <SelectItem value="Estágio">Estágio</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="about">Sobre o Candidato</Label>
                <Textarea
                  id="about"
                  value={formData.about}
                  onChange={(e) => handleInputChange("about", e.target.value)}
                  placeholder="Breve descrição sobre o candidato, experiências e objetivos..."
                  rows={4}
                />
              </div>
            </TabsContent>

            <TabsContent value="professional" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="position">Cargo Desejado *</Label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="position"
                      value={formData.position}
                      onChange={(e) => handleInputChange("position", e.target.value)}
                      placeholder="Desenvolvedor Frontend"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currentCompany">Empresa Atual</Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="currentCompany"
                      value={formData.currentCompany}
                      onChange={(e) => handleInputChange("currentCompany", e.target.value)}
                      placeholder="Tech Corp"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="experience">Anos de Experiência</Label>
                  <Input
                    id="experience"
                    type="number"
                    value={formData.experience}
                    onChange={(e) => handleInputChange("experience", e.target.value)}
                    placeholder="5"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="education">Formação</Label>
                  <div className="relative">
                    <GraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="education"
                      value={formData.education}
                      onChange={(e) => handleInputChange("education", e.target.value)}
                      placeholder="Ciência da Computação - USP"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currentSalary">Salário Atual</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="currentSalary"
                      value={formData.currentSalary}
                      onChange={(e) => handleInputChange("currentSalary", e.target.value)}
                      placeholder={DEMO_VALUES.SALARY_PLACEHOLDER_CURRENT}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expectedSalary">Pretensão Salarial</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="expectedSalary"
                      value={formData.expectedSalary}
                      onChange={(e) => handleInputChange("expectedSalary", e.target.value)}
                      placeholder={DEMO_VALUES.SALARY_PLACEHOLDER_EXPECTED}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="linkedin">LinkedIn</Label>
                  <div className="relative">
                    <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="linkedin"
                      value={formData.linkedin}
                      onChange={(e) => handleInputChange("linkedin", e.target.value)}
                      placeholder="linkedin.com/in/..."
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="github">GitHub</Label>
                  <div className="relative">
                    <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="github"
                      value={formData.github}
                      onChange={(e) => handleInputChange("github", e.target.value)}
                      placeholder="github.com/..."
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="portfolio">Portfólio</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Input
                      id="portfolio"
                      value={formData.portfolio}
                      onChange={(e) => handleInputChange("portfolio", e.target.value)}
                      placeholder="portfolio.com"
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="resume">Upload do Currículo</Label>
                <div className="rounded-xl p-4 text-center bg-lia-bg-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg transition-colors motion-reduce:transition-none cursor-pointer border border-lia-border-subtle">
                  <Upload className="w-8 h-8 text-lia-text-secondary mx-auto mb-2" />
                  <p className="text-sm text-lia-text-primary">Clique para fazer upload ou arraste o arquivo</p>
                  <p className="text-xs text-lia-text-secondary mt-1">PDF, DOC ou DOCX (máx. 10MB)</p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="skills" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Habilidades Técnicas</Label>
                <div className="flex gap-2">
                  <Input
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    placeholder="Digite uma habilidade..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddSkill()
                      }
                    }}
                  />
                  <Button onClick={handleAddSkill} size="sm">
                    <Plus className="w-4 h-4 mr-1" />
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {skills.map((skill, skillIdx) => (
                    <Chip key={`skill-${skill}-${skillIdx}`} variant="neutral" muted className="px-1.5 py-0">
                      {skill}
                      <button
                        onClick={() => handleRemoveSkill(skill)}
                        className="ml-2 hover:text-status-error"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Chip>
                  ))}
                </div>
                {liaAnalysis?.suggestedSkills && (
                  <div className="mt-3 p-3 bg-lia-bg-tertiary rounded-xl">
                    <p className="text-xs text-lia-text-muted mb-2 flex items-center gap-1">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      Sugestões baseadas no perfil:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {liaAnalysis.suggestedSkills.map((skill: string) => (
                        <Chip
                          key={`suggested-${skill}`}
                          variant="neutral"
                          className="cursor-pointer hover:bg-lia-interactive-hover"
                          onClick={() => {
                            if (!skills.includes(skill)) {
                              setSkills([...skills, skill])
                            }
                          }}
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          {skill}
                        </Chip>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="languages">Idiomas</Label>
                  <div className="relative">
                    <Languages className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Textarea
                      id="languages"
                      value={formData.languages}
                      onChange={(e) => handleInputChange("languages", e.target.value)}
                      placeholder="Português (Nativo)&#10;Inglês (Avançado)&#10;Espanhol (Intermediário)"
                      rows={3}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="certifications">Certificações</Label>
                  <div className="relative">
                    <Award className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                    <Textarea
                      id="certifications"
                      value={formData.certifications}
                      onChange={(e) => handleInputChange("certifications", e.target.value)}
                      placeholder="AWS Certified&#10;Scrum Master&#10;Google Analytics"
                      rows={3}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="analysis" className="space-y-4 mt-4">
              {!liaAnalysis ? (
                <Card className="border-dashed">
                  <CardContent className="pt-6">
                    <div className="text-center py-8">
                      <LIAIcon size="lg" className="mx-auto mb-4 opacity-50" />
                      <h3 className="text-lg font-semibold mb-2 text-lia-text-primary">Análise de Compatibilidade</h3>
                      <p className="text-sm text-lia-text-primary mb-4">
                        A análise de compatibilidade fica disponível na ficha do candidato após o cadastro.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {/* Score Cards */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-lia-text-primary">Score Geral</span>
                          <Target className="w-4 h-4 text-lia-text-secondary" />
                        </div>
                        <div className="text-2xl font-semibold text-lia-text-primary">{liaAnalysis.score}%</div>
                        <div className="w-full bg-lia-interactive-active rounded-full h-1.5 mt-2">
                          <div
                            className="bg-lia-btn-primary-bg dark:bg-lia-text-tertiary h-1.5 rounded-full"
                            style={{width: `${liaAnalysis.score}%`}}
                          />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-lia-text-primary">Fit Cultural</span>
                          <User className="w-4 h-4 text-status-success" />
                        </div>
                        <div className="text-2xl font-semibold text-status-success">{liaAnalysis.culturalFit}%</div>
                        <div className="w-full bg-lia-interactive-active rounded-full h-1.5 mt-2">
                          <div
                            className="bg-status-success h-1.5 rounded-full"
                            style={{width: `${liaAnalysis.culturalFit}%`}}
                          />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-lia-text-primary">Fit Técnico</span>
                          <Zap className="w-4 h-4 text-wedo-purple" />
                        </div>
                        <div className="text-2xl font-semibold text-wedo-purple-text">{liaAnalysis.technicalFit}%</div>
                        <div className="w-full bg-lia-interactive-active rounded-full h-1.5 mt-2">
                          <div
                            className="bg-wedo-purple h-1.5 rounded-full"
                            style={{width: `${liaAnalysis.technicalFit}%`}}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Strengths and Improvements */}
                  <div className="grid grid-cols-2 gap-4">
                    <Card className="bg-status-success/10">
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2 mb-3">
                          <CheckCircle className="w-4 h-4 text-status-success" />
                          <h4 className="font-semibold text-status-success">Pontos Fortes</h4>
                        </div>
                        <ul className="space-y-1">
                          {(liaAnalysis.strengths || []).map((strength: string, index: number) => (
                            <li key={`strength-${index}`} className="text-sm text-status-success flex items-start gap-2">
                              <span className="text-status-success mt-0.5">•</span>
                              {strength}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>

                    <Card className="bg-wedo-orange/10">
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-2 mb-3">
                          <AlertCircle className="w-4 h-4 text-wedo-orange" />
                          <h4 className="font-semibold text-wedo-orange-text">Pontos de Atenção</h4>
                        </div>
                        <ul className="space-y-1">
                          {(liaAnalysis.improvements || []).map((improvement: string, index: number) => (
                            <li key={`improvement-${index}`} className="text-sm text-wedo-orange-text flex items-start gap-2">
                              <span className="text-wedo-orange-text mt-0.5">•</span>
                              {improvement}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Recommendation */}
                  <Card className="bg-lia-bg-tertiary">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <LIAIcon size="sm" />
                        <h4 className="font-semibold text-wedo-cyan-text">Recomendação</h4>
                      </div>
                      <p className="text-sm text-lia-text-muted">{liaAnalysis.recommendation}</p>
                    </CardContent>
                  </Card>

                  {/* Soft Skills */}
                  <Card>
                    <CardContent className="pt-4">
                      <h4 className="font-semibold mb-3">Habilidades Comportamentais</h4>
                      <div className="space-y-3">
                        {Object.entries(liaAnalysis.softSkills || {}).map(([skill, value]) => (
                          <div key={`skill-row-${skill}`} className="flex items-center gap-3">
                            <span className="text-sm text-lia-text-primary capitalize w-32">
                              {skill === 'communication' ? 'Comunicação' :
                               skill === 'teamwork' ? 'Trabalho em equipe' :
                               skill === 'leadership' ? 'Liderança' :
                               'Resolução de problemas'}
                            </span>
                            <div className="flex-1 bg-lia-interactive-active rounded-full h-2">
                              <div
                                className="bg-lia-btn-primary-bg dark:bg-lia-text-tertiary h-2 rounded-full"
                                style={{width: `${value}%`}}
                              />
                            </div>
                            <span className="text-sm font-medium text-lia-text-primary w-12 text-right">
                              {value as number}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>

        <DialogFooter className="mt-4 border-t border-lia-border-subtle bg-lia-bg-secondary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button variant="outline" onClick={onClose} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!formData.name || !formData.email || !formData.phone || !formData.position}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Candidato
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
