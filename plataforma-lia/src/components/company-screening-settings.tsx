"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, Brain, CheckCircle, AlertCircle, Clock, User,
  MessageSquare, Star, Target, Heart, Zap, Award, TrendingUp,
  FileText, Copy, Edit, Download, Share2, ChevronRight,
  Phone, Video, Mail, Calendar, Globe, Users, Briefcase,
  GraduationCap, Code, Palette, Building, MapPin, DollarSign,
  Save, Plus, Trash2, Settings
} from "lucide-react"

interface CompanyScreeningSettingsProps {
  isOpen: boolean
  onClose: () => void
}

export function CompanyScreeningSettings({ isOpen, onClose }: CompanyScreeningSettingsProps) {
  const [activeSection, setActiveSection] = useState<'templates' | 'approach' | 'questions' | 'feedback' | 'guidelines'>('templates')
  const [selectedTemplate, setSelectedTemplate] = useState('default')

  if (!isOpen) return null

  const sections = [
    { id: 'templates', label: 'Templates', icon: FileText },
    { id: 'approach', label: 'Abordagem Padrão', icon: MessageSquare },
    { id: 'questions', label: 'Banco de Perguntas', icon: Target },
    { id: 'feedback', label: 'Modelos de Feedback', icon: Heart },
    { id: 'guidelines', label: 'Diretrizes', icon: Star }
  ]

  const companyTemplates = [
    {
      id: 'default',
      name: 'Padrão Empresa',
      description: 'Template padrão para todas as vagas',
      duration: '25-30 min',
      focus: 'Técnico + Cultural',
      active: true
    },
    {
      id: 'tech-senior',
      name: 'Tech Sênior',
      description: 'Para posições técnicas sênior',
      duration: '30-40 min',
      focus: 'Técnico + Liderança',
      active: true
    },
    {
      id: 'junior',
      name: 'Posições Júnior',
      description: 'Para candidatos iniciantes',
      duration: '20-25 min',
      focus: 'Potencial + Cultural',
      active: true
    }
  ]

  const approachSettings = {
    tone: "Profissional, mas acolhedor",
    structure: [
      "Apresentação pessoal (2-3 min)",
      "Contexto da vaga (3-5 min)",
      "Perguntas de triagem (15-20 min)",
      "Esclarecimento de dúvidas (3-5 min)",
      "Próximos passos (2 min)"
    ],
    guidelines: [
      "Mantenha um ritmo conversacional, não interrogatório",
      "Faça anotações discretas durante a conversa",
      "Dê espaço para o candidato fazer perguntas",
      "Observe não apenas as respostas, mas a forma de comunicação"
    ]
  }

  const questionBank = [
    {
      category: "Apresentação Pessoal",
      questions: [
        "Conte-me um pouco sobre você e sua trajetória profissional",
        "O que te motivou a se candidatar para esta posição?",
        "Como você ficou sabendo desta oportunidade?"
      ]
    },
    {
      category: "Experiência Técnica",
      questions: [
        "Descreva um projeto desafiador que você trabalhou recentemente",
        "Como você se mantém atualizado com as tecnologias da área?",
        "Qual foi sua maior conquista profissional?"
      ]
    },
    {
      category: "Fit Cultural",
      questions: [
        "Como você se adapta a ambientes de trabalho dinâmicos?",
        "Descreva como você lida com feedback construtivo",
        "O que você valoriza mais em uma equipe de trabalho?"
      ]
    }
  ]

  const feedbackTemplates = {
    approved: {
      subject: "Próximos passos - {VAGA}",
      timing: "24 horas",
      message: `Olá {NOME},

Ficamos muito satisfeitos com nossa conversa sobre a posição de {VAGA}!

Seu perfil está alinhado com o que buscamos e gostaríamos de dar continuidade ao processo.

Próximo passo: {PROXIMA_ETAPA}

Em breve entraremos em contato para agendar.

Parabéns e até logo!

Equipe de Recrutamento`
    },
    rejected: {
      subject: "Feedback sobre processo seletivo - {VAGA}",
      timing: "48 horas",
      message: `Olá {NOME},

Obrigado pelo seu interesse na posição de {VAGA} e pelo tempo dedicado em nossa conversa.

Após análise cuidadosa, decidimos seguir com candidatos cujo perfil está mais alinhado com as necessidades específicas desta vaga no momento.

✨ Pontos fortes identificados:
{PONTOS_FORTES}

🎯 Áreas de desenvolvimento sugeridas:
{AREAS_DESENVOLVIMENTO}

Seu perfil ficará em nosso radar para futuras oportunidades que possam ser um match ainda melhor!

Desejamos muito sucesso em sua jornada profissional.

Com carinho,
Equipe de Recrutamento`
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-md w-full max-w-6xl max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-gray-100 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
              <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold font-sans text-gray-950 dark:text-gray-50">
                Configurações de Triagem
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Defina padrões da empresa para roteiros de triagem
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              Exportar Configurações
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex">
          {/* Sidebar Navigation */}
          <div className="w-64 bg-white dark:bg-gray-800 p-4">
            <div className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id as any)}
                  className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors ${
                    activeSection === section.id
                      ? 'bg-gray-100 dark:bg-gray-800 text-wedo-cyan-dark dark:text-gray-400'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  <section.icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{section.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6">
            {/* Templates Section */}
            {activeSection === 'templates' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">Templates de Roteiro</h4>
                  <Button className="gap-2">
                    <Plus className="w-4 h-4" />
                    Novo Template
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {companyTemplates.map((template) => (
                    <Card key={template.id} className={`cursor-pointer transition-all ${
                      selectedTemplate === template.id ? 'ring-2 ring-gray-900/20 dark:ring-gray-50/20' : ''
                    }`}>
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-sm font-sans">{template.name}</CardTitle>
                          <Badge variant={template.active ? "default" : "secondary"}>
                            {template.active ? "Ativo" : "Inativo"}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-xs text-gray-800 dark:text-gray-200 mb-3">
                          {template.description}
                        </p>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Duração:</span>
                            <span className="font-medium">{template.duration}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Foco:</span>
                            <span className="font-medium">{template.focus}</span>
                          </div>
                        </div>
                        <div className="flex gap-2 mt-4">
                          <Button size="sm" variant="outline" className="flex-1">
                            <Edit className="w-3 h-3 mr-1" />
                            Editar
                          </Button>
                          <Button size="sm" variant="outline">
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Approach Section */}
            {activeSection === 'approach' && (
              <div className="space-y-6">
                <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">Abordagem Padrão</h4>

                <Card className="">
                  <CardHeader>
                    <CardTitle className="text-sm font-sans">Tom e Postura</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <input
                      type="text"
                      value={approachSettings.tone}
                      className="w-full p-3 rounded-md bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                    />
                  </CardContent>
                </Card>

                <Card className="">
                  <CardHeader>
                    <CardTitle className="text-sm font-sans">Estrutura da Conversa</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {approachSettings.structure.map((step, index) => (
                        <div key={index} className="flex items-center gap-3">
                          <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-400 text-xs font-bold">
                            {index + 1}
                          </div>
                          <input
                            type="text"
                            value={step}
                            className="flex-1 p-2 rounded-md bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                          <Button variant="ghost" size="sm">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" className="gap-2">
                        <Plus className="w-3 h-3" />
                        Adicionar Etapa
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Questions Section */}
            {activeSection === 'questions' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">Banco de Perguntas</h4>
                  <Button className="gap-2">
                    <Plus className="w-4 h-4" />
                    Nova Categoria
                  </Button>
                </div>

                {questionBank.map((category, categoryIndex) => (
                  <Card key={categoryIndex} className="">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-sans">{category.category}</CardTitle>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Plus className="w-3 h-3 mr-1" />
                            Pergunta
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {category.questions.map((question, questionIndex) => (
                          <div key={questionIndex} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                            <span className="text-sm flex-1">{question}</span>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Feedback Section */}
            {activeSection === 'feedback' && (
              <div className="space-y-6">
                <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">Modelos de Feedback</h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Approved Template */}
                  <Card className="">
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2 font-sans">
                        <CheckCircle className="w-4 h-4 text-status-success" />
                        Candidatos Aprovados
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Timing:</label>
                          <input
                            type="text"
                            value={feedbackTemplates.approved.timing}
                            className="w-full p-2 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Assunto:</label>
                          <input
                            type="text"
                            value={feedbackTemplates.approved.subject}
                            className="w-full p-2 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Mensagem:</label>
                          <textarea
                            value={feedbackTemplates.approved.message}
                            className="w-full p-3 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                            rows={8}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Rejected Template */}
                  <Card className="">
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2 font-sans">
                        <Heart className="w-4 h-4 text-wedo-orange" />
                        Feedback Construtivo
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Timing:</label>
                          <input
                            type="text"
                            value={feedbackTemplates.rejected.timing}
                            className="w-full p-2 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Assunto:</label>
                          <input
                            type="text"
                            value={feedbackTemplates.rejected.subject}
                            className="w-full p-2 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-800 dark:text-gray-200">Mensagem:</label>
                          <textarea
                            value={feedbackTemplates.rejected.message}
                            className="w-full p-3 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                            rows={8}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {/* Guidelines Section */}
            {activeSection === 'guidelines' && (
              <div className="space-y-6">
                <h4 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">Diretrizes da Empresa</h4>

                <Card className="">
                  <CardHeader>
                    <CardTitle className="text-sm font-sans">Orientações Gerais</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {approachSettings.guidelines.map((guideline, index) => (
                        <div key={index} className="flex items-start gap-3">
                          <Star className="w-4 h-4 text-status-warning mt-0.5" />
                          <input
                            type="text"
                            value={guideline}
                            className="flex-1 p-2 rounded-md text-sm bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                          />
                          <Button variant="ghost" size="sm">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" className="gap-2">
                        <Plus className="w-3 h-3" />
                        Nova Diretriz
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card className="">
                  <CardHeader>
                    <CardTitle className="text-sm font-sans">Variáveis Disponíveis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <code className="p-2 bg-gray-100 rounded-md">{"{NOME}"}</code>
                      <code className="p-2 bg-gray-100 rounded-md">{"{VAGA}"}</code>
                      <code className="p-2 bg-gray-100 rounded-md">{"{EMPRESA}"}</code>
                      <code className="p-2 bg-gray-100 rounded-md">{"{PONTOS_FORTES}"}</code>
                      <code className="p-2 bg-gray-100 rounded-md">{"{AREAS_DESENVOLVIMENTO}"}</code>
                      <code className="p-2 bg-gray-100 rounded-md">{"{PROXIMA_ETAPA}"}</code>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-800 dark:text-gray-200">
              Configurações serão aplicadas a novos roteiros criados
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline">
                Cancelar
              </Button>
              <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200">
                <Save className="w-4 h-4" />
                Salvar Configurações
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
