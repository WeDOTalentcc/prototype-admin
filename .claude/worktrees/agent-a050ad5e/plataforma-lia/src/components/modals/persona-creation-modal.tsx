"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  X, User, Briefcase, MapPin, DollarSign, GraduationCap,
  Brain, Target, TrendingUp, Users, Zap,
  Plus, Trash2, Star, Clock, CheckCircle
} from "lucide-react"

interface PersonaCreationModalProps {
  isOpen: boolean
  onClose: () => void
  baseJob?: {
    title: string
    company: string
    description: string
    requirements: string[]
  }
  suggestedCandidates?: number
}

export function PersonaCreationModal({ isOpen, onClose, baseJob, suggestedCandidates }: PersonaCreationModalProps) {
  const [step, setStep] = useState(1)
  const [personaData, setPersonaData] = useState({
    name: baseJob?.title || '',
    description: '',
    avatar: '👨‍💻',
    basedOnJob: baseJob?.title || '',

    // Critérios
    requiredSkills: baseJob?.requirements || ['React', 'TypeScript'],
    preferredSkills: ['Next.js', 'GraphQL'],
    experienceMin: 3,
    experienceMax: 8,
    salaryMin: 10000,
    salaryMax: 18000,
    locations: ['São Paulo', 'Remoto'],
    education: ['Superior Completo'],

    // Configurações avançadas
    autoSourcing: true,
    smartAlerts: true,
    liaAnalysis: true,
    priorityLevel: 'medium'
  })

  const [preview, setPreview] = useState({
    estimatedCandidates: suggestedCandidates || 67,
    estimatedTimeToHire: 14,
    estimatedSuccessRate: 78,
    estimatedCostPerHire: 12500
  })

  const avatarOptions = ['👨‍💻', '👩‍💻', '🎨', '📊', '🚀', '⚡', '🎯', '💡', '🔧', '📱']

  if (!isOpen) return null

  const handleSkillAdd = (type: 'required' | 'preferred', skill: string) => {
    if (!skill.trim()) return

    setPersonaData(prev => ({
      ...prev,
      [type === 'required' ? 'requiredSkills' : 'preferredSkills']: [
        ...prev[type === 'required' ? 'requiredSkills' : 'preferredSkills'],
        skill.trim()
      ]
    }))
  }

  const handleSkillRemove = (type: 'required' | 'preferred', index: number) => {
    setPersonaData(prev => ({
      ...prev,
      [type === 'required' ? 'requiredSkills' : 'preferredSkills']:
        prev[type === 'required' ? 'requiredSkills' : 'preferredSkills'].filter((_, i) => i !== index)
    }))
  }

  const handleCreate = () => {
    // Simular criação da persona
    alert(`🎉 Persona "${personaData.name}" criada com sucesso!\n\n` +
          `📊 Métricas Iniciais:\n` +
          `• ${preview.estimatedCandidates} candidatos estimados\n` +
          `• ${preview.estimatedTimeToHire} dias tempo médio\n` +
          `• ${preview.estimatedSuccessRate}% taxa de sucesso estimada\n` +
          `• R$ ${preview.estimatedCostPerHire.toLocaleString()} custo por hire\n\n` +
          `🚀 Sourcing automático iniciado!`)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-md max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-950 dark:text-gray-50 flex items-center gap-2">
                <Star className="w-5 h-5 text-purple-600" />
                Criar Nova Persona
              </h2>
              <p className="text-sm text-gray-800 dark:text-gray-200 mt-1">
                {baseJob ? `Baseada na vaga: ${baseJob.title}` : 'Configuração manual completa'}
              </p>
            </div>
            <Button variant="outline" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-4 mt-4">
            {[1, 2, 3].map((stepNum) => (
              <div key={stepNum} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= stepNum
                    ? 'bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900'
                    : 'bg-gray-200 text-gray-800 dark:text-gray-200'
                }`}>
                  {step > stepNum ? <CheckCircle className="w-4 h-4" /> : stepNum}
                </div>
                <div className="ml-2 text-sm font-medium text-gray-800 dark:text-gray-200">
                  {stepNum === 1 && 'Informações Básicas'}
                  {stepNum === 2 && 'Critérios & Skills'}
                  {stepNum === 3 && 'Preview & Criação'}
                </div>
                {stepNum < 3 && <div className="w-8 h-0.5 bg-gray-300 ml-4" />}
              </div>
            ))}
          </div>
        </div>

        <div className="flex h-[calc(90vh-180px)]">
          {/* Main Form */}
          <div className="flex-1 p-6 overflow-y-auto">
            {/* Step 1: Informações Básicas */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Nome da Persona *
                  </label>
                  <Input
                    value={personaData.name}
                    onChange={(e) => setPersonaData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Ex: Desenvolvedor Frontend Sênior"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Descrição
                  </label>
                  <Textarea
                    value={personaData.description}
                    onChange={(e) => setPersonaData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Descreva o perfil ideal para esta persona..."
                    rows={3}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Avatar
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {avatarOptions.map((avatar) => (
                      <button
                        key={avatar}
                        onClick={() => setPersonaData(prev => ({ ...prev, avatar }))}
                        className={`text-2xl p-2 rounded-md hover:bg-gray-50 transition-all ${
                          personaData.avatar === avatar ? 'bg-blue-50' : 'bg-white'
                        }`}
                      >
                        {avatar}
                      </button>
                    ))}
                  </div>
                </div>

                {baseJob && (
 <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
 <h4 className="font-medium text-wedo-cyan-dark dark:text-gray-300 mb-2">
                      📋 Baseada na Vaga
                    </h4>
 <p className="text-sm text-wedo-cyan-dark dark:text-gray-500 mb-2">
                      <strong>{baseJob.title}</strong> na {baseJob.company}
                    </p>
 <p className="text-xs text-gray-600 dark:text-gray-300">
                      {baseJob.description}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Critérios & Skills */}
            {step === 2 && (
              <div className="space-y-6">
                {/* Skills Obrigatórias */}
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Skills Obrigatórias *
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {personaData.requiredSkills.map((skill, index) => (
                      <Badge key={index} className="bg-gray-50 dark:bg-gray-900 text-wedo-cyan-dark flex items-center gap-1">
                        {skill}
                        <button
                          onClick={() => handleSkillRemove('required', index)}
                          className="ml-1 hover:bg-gray-100 dark:bg-gray-800 rounded-full p-0.5"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Adicionar skill obrigatória"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSkillAdd('required', e.currentTarget.value)
                          e.currentTarget.value = ''
                        }
                      }}
                      className="flex-1"
                    />
                  </div>
                </div>

                {/* Skills Preferenciais */}
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Skills Preferenciais
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {personaData.preferredSkills.map((skill, index) => (
                      <Badge key={index} variant="outline" className="flex items-center gap-1">
                        {skill}
                        <button
                          onClick={() => handleSkillRemove('preferred', index)}
                          className="ml-1 hover:bg-gray-200 rounded-full p-0.5"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <Input
                    placeholder="Adicionar skill preferencial"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSkillAdd('preferred', e.currentTarget.value)
                        e.currentTarget.value = ''
                      }
                    }}
                  />
                </div>

                {/* Experiência */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Experiência Mínima (anos)
                    </label>
                    <Input
                      type="number"
                      value={personaData.experienceMin}
                      onChange={(e) => setPersonaData(prev => ({ ...prev, experienceMin: parseInt(e.target.value) || 0 }))}
                      min="0"
                      max="20"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Experiência Máxima (anos)
                    </label>
                    <Input
                      type="number"
                      value={personaData.experienceMax}
                      onChange={(e) => setPersonaData(prev => ({ ...prev, experienceMax: parseInt(e.target.value) || 0 }))}
                      min="0"
                      max="20"
                    />
                  </div>
                </div>

                {/* Salário */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Salário Mínimo (R$)
                    </label>
                    <Input
                      type="number"
                      value={personaData.salaryMin}
                      onChange={(e) => setPersonaData(prev => ({ ...prev, salaryMin: parseInt(e.target.value) || 0 }))}
                      min="0"
                      step="1000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                      Salário Máximo (R$)
                    </label>
                    <Input
                      type="number"
                      value={personaData.salaryMax}
                      onChange={(e) => setPersonaData(prev => ({ ...prev, salaryMax: parseInt(e.target.value) || 0 }))}
                      min="0"
                      step="1000"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Preview & Criação */}
            {step === 3 && (
              <div className="space-y-6">
                {/* Preview da Persona */}
                <Card className="border-l-4 border-l-green-500">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{personaData.avatar}</div>
                      <div>
                        <CardTitle>{personaData.name}</CardTitle>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {personaData.description || 'Persona criada automaticamente'}
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <p className="text-lg font-semibold text-gray-900 dark:text-gray-50">{preview.estimatedCandidates}</p>
                        <p className="text-xs text-gray-600">Candidatos Estimados</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-semibold text-green-600">{preview.estimatedTimeToHire}d</p>
                        <p className="text-xs text-gray-600">Tempo Médio</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-semibold text-purple-600">{preview.estimatedSuccessRate}%</p>
                        <p className="text-xs text-gray-600">Taxa Sucesso</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-semibold text-orange-600">R$ {(preview.estimatedCostPerHire/1000).toFixed(0)}k</p>
                        <p className="text-xs text-gray-600">Custo/Hire</p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Skills Obrigatórias:</p>
                        <div className="flex flex-wrap gap-1">
                          {personaData.requiredSkills.map((skill, index) => (
                            <Badge key={index} className="text-xs bg-gray-50 dark:bg-gray-900 text-wedo-cyan-dark">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="flex justify-between text-xs text-gray-800 dark:text-gray-200">
                        <span>Experiência: {personaData.experienceMin}-{personaData.experienceMax} anos</span>
                        <span>Salário: R$ {personaData.salaryMin.toLocaleString()}-{personaData.salaryMax.toLocaleString()}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Configurações Avançadas */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="w-5 h-5 text-purple-600" />
                      Configurações Inteligentes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">Sourcing Automático</p>
                          <p className="text-xs text-gray-600">LIA busca candidatos automaticamente</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={personaData.autoSourcing}
                          onChange={(e) => setPersonaData(prev => ({ ...prev, autoSourcing: e.target.checked }))}
                          className="rounded"
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">Alertas Inteligentes</p>
                          <p className="text-xs text-gray-600">Notificações sobre candidatos críticos</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={personaData.smartAlerts}
                          onChange={(e) => setPersonaData(prev => ({ ...prev, smartAlerts: e.target.checked }))}
                          className="rounded"
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">Análise LIA</p>
                          <p className="text-xs text-gray-600">Scoring automático e insights</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={personaData.liaAnalysis}
                          onChange={(e) => setPersonaData(prev => ({ ...prev, liaAnalysis: e.target.checked }))}
                          className="rounded"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Sidebar - LIA Suggestions */}
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-4">
            <div className="sticky top-0">
              <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-600" />
                Sugestões da LIA
              </h3>

              <div className="space-y-3">
                <div className="bg-white dark:bg-gray-900 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium">Mercado Aquecido</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Detectei alta demanda por {personaData.name.toLowerCase()} no mercado
                  </p>
                  <Badge className="bg-green-100 text-green-700 text-xs">
                    +23% vagas este mês
                  </Badge>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <span className="text-sm font-medium">Base Estimada</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    {preview.estimatedCandidates} candidatos correspondem aos critérios
                  </p>
                  <Badge className="bg-gray-50 dark:bg-gray-900 text-wedo-cyan-dark text-xs">
                    Base sólida para início
                  </Badge>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium">Otimização</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Sugiro incluir Vue.js como skill preferencial
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 text-xs w-full"
                    onClick={() => {
                      if (!personaData.preferredSkills.includes('Vue.js')) {
                        setPersonaData(prev => ({
                          ...prev,
                          preferredSkills: [...prev.preferredSkills, 'Vue.js']
                        }))
                      }
                    }}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    Aplicar
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex justify-between">
            <div className="flex gap-2">
              {step > 1 && (
                <Button variant="outline" onClick={() => setStep(step - 1)}>
                  Voltar
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              {step < 3 ? (
                <Button onClick={() => setStep(step + 1)}>
                  Próximo
                </Button>
              ) : (
                <Button onClick={handleCreate} className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
                  <Star className="w-4 h-4 mr-2" />
                  Criar Persona
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
