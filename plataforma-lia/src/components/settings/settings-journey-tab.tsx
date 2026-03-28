"use client"

  import { useState } from "react"
  import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
  import { Badge } from "@/components/ui/badge"
  import { Button } from "@/components/ui/button"
  import {
    Map, Briefcase, Database, Workflow, Globe, Zap,
    MessageSquare, Mail, Phone, MessageCircle, Check,
    ArrowLeft, ArrowRight, AlertCircle, Eye, X, Loader2
  } from "lucide-react"

  export interface SettingsJourneyTabProps {
    onSettingsChange: (changed: boolean) => void
  }

  // Componente de Journey Mapping (NOVO)
export function SettingsJourneyTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [wizardData, setWizardData] = useState({
    vagasAbertura: '',
    sistemasUsados: [] as string[],
    etapasProcesso: [] as string[],
    automacoesDesejadas: [] as string[],
    canaisPublicacao: [] as string[],
    canaisComunicacaoCandidatos: ['whatsapp', 'email', 'ligacao'] as string[],
    careersPageUrl: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [blueprintId, setBlueprintId] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://7ce0a62c-6426-43d6-8c3c-f9e1dcef099b-00-1d771t3pez3we.picard.replit.dev'

  const submitWizard = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    
    try {
      let companyId: string | null = null
      try {
        const companyRes = await fetch('/api/backend-proxy/company/profile')
        if (companyRes.ok) {
          const companyData = await companyRes.json()
          companyId = companyData?.id || null
        }
      } catch (e) {
      }
      
      if (!companyId) {
        throw new Error('Não foi possível identificar a empresa. Por favor, configure o perfil da empresa primeiro.')
      }
      
      const payload = {
        company_id: companyId,
        vagas_abertura: wizardData.vagasAbertura || 'requisicao_formal',
        sistemas_usados: wizardData.sistemasUsados,
        etapas_processo: wizardData.etapasProcesso,
        automacoes_desejadas: wizardData.automacoesDesejadas,
        canais_publicacao: wizardData.canaisPublicacao,
        canais_comunicacao_candidatos: wizardData.canaisComunicacaoCandidatos,
        careers_page_url: wizardData.careersPageUrl || null
      }

      const response = await fetch(`${API_BASE}/api/v1/journey-mapping/wizard/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao salvar configuração')
      }

      const result = await response.json()
      setBlueprintId(result.id)
      setSubmitSuccess(true)
      onSettingsChange(false) // Reset dirty state
      
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Erro desconhecido')
    } finally {
      setIsSubmitting(false)
    }
  }

  const steps = [
    { id: 1, title: 'Abertura de Vagas', description: 'Como as vagas são abertas?' },
    { id: 2, title: 'Sistemas', description: 'Quais sistemas vocês usam?' },
    { id: 3, title: 'Etapas', description: 'Etapas do processo' },
    { id: 4, title: 'Automações', description: 'Automações desejadas' },
    { id: 5, title: 'Canais', description: 'Onde publicar vagas' }
  ]

  const sistemasDisponiveis = [
    { id: 'gupy', name: 'Gupy', category: 'ATS' },
    { id: 'pandape', name: 'Pandapé', category: 'ATS' },
    { id: 'stackone', name: 'StackOne', category: 'ATS' },
    { id: 'greenhouse', name: 'Greenhouse', category: 'ATS' },
    { id: 'workday', name: 'Workday', category: 'Workforce Planning' },
    { id: 'sap_sf', name: 'SAP SuccessFactors', category: 'Workforce Planning' },
    { id: 'senior', name: 'Senior Sistemas', category: 'HRIS/Folha' },
    { id: 'totvs', name: 'TOTVS RM', category: 'HRIS/Folha' },
    { id: 'adp', name: 'ADP', category: 'HRIS/Folha' },
    { id: 'hackerrank', name: 'HackerRank', category: 'Avaliação Técnica' },
    { id: 'codility', name: 'Codility', category: 'Avaliação Técnica' },
    { id: 'mindsight', name: 'Mindsight', category: 'Assessment' },
    { id: 'docusign', name: 'DocuSign', category: 'Assinatura Digital' },
    { id: 'clicksign', name: 'Clicksign', category: 'Assinatura Digital' },
    { id: 'slack', name: 'Slack', category: 'Comunicação' },
    { id: 'teams', name: 'Microsoft Teams', category: 'Comunicação' }
  ]

  const canaisDisponiveis = [
    { id: 'linkedin_jobs', name: 'LinkedIn Jobs', desc: 'Publicação direta no LinkedIn' },
    { id: 'indeed', name: 'Indeed', desc: 'Job board internacional' },
    { id: 'glassdoor', name: 'Glassdoor', desc: 'Vagas e avaliações da empresa' },
    { id: 'catho', name: 'Catho', desc: 'Job board brasileiro' },
    { id: 'infojobs', name: 'InfoJobs', desc: 'Job board brasileiro' },
    { id: 'site_proprio', name: 'Site Próprio', desc: 'Página de carreiras da empresa' },
    { id: 'universidades', name: 'Universidades', desc: 'Portais acadêmicos' },
    { id: 'redes_sociais', name: 'Redes Sociais', desc: 'Instagram, Facebook, etc.' }
  ]

  const etapasDisponiveis = [
    'Triagem de CVs',
    'Entrevista Inicial',
    'Teste Técnico',
    'Entrevista Técnica',
    'Entrevista com Gestor',
    'Assessment Cultural',
    'Proposta',
    'Onboarding'
  ]

  const automacoesDisponiveis = [
    { id: 'auto-screening', name: 'Triagem Automática', desc: 'Filtrar candidatos automaticamente por critérios' },
    { id: 'auto-schedule', name: 'Agendamento Automático', desc: 'Agendar entrevistas automaticamente' },
    { id: 'auto-notify', name: 'Notificações Automáticas', desc: 'Enviar emails e alertas automaticamente' },
    { id: 'auto-feedback', name: 'Coleta de Feedback', desc: 'Solicitar feedback de entrevistadores' },
    { id: 'auto-offer', name: 'Geração de Proposta', desc: 'Criar propostas automaticamente' },
    { id: 'auto-report', name: 'Relatórios Automáticos', desc: 'Gerar relatórios de métricas' }
  ]

  const canaisComunicacaoCandidatosDisponiveis = [
    { id: 'whatsapp', name: 'WhatsApp', desc: 'Mensagens via WhatsApp Business', icon: 'MessageSquare', essential: true },
    { id: 'email', name: 'Email', desc: 'Comunicação por email corporativo', icon: 'Mail', essential: true },
    { id: 'ligacao', name: 'Ligação', desc: 'Ligações telefônicas', icon: 'Phone', essential: true },
    { id: 'sms', name: 'SMS', desc: 'Mensagens de texto SMS', icon: 'MessageCircle', essential: false }
  ]

  const toggleSistema = (sistemaId: string) => {
    setWizardData(prev => ({
      ...prev,
      sistemasUsados: prev.sistemasUsados.includes(sistemaId)
        ? prev.sistemasUsados.filter(s => s !== sistemaId)
        : [...prev.sistemasUsados, sistemaId]
    }))
    onSettingsChange(true)
  }

  const toggleEtapa = (etapa: string) => {
    setWizardData(prev => ({
      ...prev,
      etapasProcesso: prev.etapasProcesso.includes(etapa)
        ? prev.etapasProcesso.filter(e => e !== etapa)
        : [...prev.etapasProcesso, etapa]
    }))
    onSettingsChange(true)
  }

  const toggleAutomacao = (automacaoId: string) => {
    setWizardData(prev => ({
      ...prev,
      automacoesDesejadas: prev.automacoesDesejadas.includes(automacaoId)
        ? prev.automacoesDesejadas.filter(a => a !== automacaoId)
        : [...prev.automacoesDesejadas, automacaoId]
    }))
    onSettingsChange(true)
  }

  const toggleCanal = (canalId: string) => {
    setWizardData(prev => ({
      ...prev,
      canaisPublicacao: prev.canaisPublicacao.includes(canalId)
        ? prev.canaisPublicacao.filter(c => c !== canalId)
        : [...prev.canaisPublicacao, canalId]
    }))
    onSettingsChange(true)
  }

  const toggleCanalComunicacaoCandidato = (canalId: string) => {
    setWizardData(prev => ({
      ...prev,
      canaisComunicacaoCandidatos: prev.canaisComunicacaoCandidatos.includes(canalId)
        ? prev.canaisComunicacaoCandidatos.filter(c => c !== canalId)
        : [...prev.canaisComunicacaoCandidatos, canalId]
    }))
    onSettingsChange(true)
  }

  const essentialChannelsRemoved = canaisComunicacaoCandidatosDisponiveis
    .filter(c => c.essential)
    .some(c => !wizardData.canaisComunicacaoCandidatos.includes(c.id))

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-l-4 border-l-gray-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-xl font-medium">
            <Map className="w-5 h-5 text-gray-700" />
            Journey Mapping
          </CardTitle>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            Configure o mapa da jornada de recrutamento da sua empresa através do wizard interativo.
          </p>
        </CardHeader>
      </Card>

      {/* Wizard Steps Indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-8">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => setCurrentStep(step.id)}
                  className={`flex flex-col items-center transition-all ${
                    currentStep === step.id
                      ? 'text-gray-600 dark:text-gray-400'
                      : currentStep > step.id
                      ? 'text-status-success'
                      : 'text-gray-500'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 border-2 transition-all ${
                      currentStep === step.id
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : currentStep > step.id
                        ? 'border-status-success/30 bg-status-success text-white'
                        : 'border-gray-300 bg-gray-50 dark:bg-gray-800'
                    }`}
                  >
                    {currentStep > step.id ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <span className="font-semibold">{step.id}</span>
                    )}
                  </div>
                  <span className="text-xs font-medium text-center">
                    {step.title}
                  </span>
                </button>
                {index < steps.length - 1 && (
                  <div
                    className={`w-16 h-0.5 mx-2 ${
                      currentStep > step.id ? 'bg-status-success' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Briefcase className="w-5 h-5 text-gray-600" />
              Como as vagas são abertas?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200">
              Descreva o fluxo típico de abertura de vagas na sua empresa.
            </p>
            <textarea
              value={wizardData.vagasAbertura}
              onChange={(e) => {
                setWizardData(prev => ({ ...prev, vagasAbertura: e.target.value }))
                onSettingsChange(true)
              }}
              placeholder="Ex: As vagas são abertas pelo gestor da área através de um formulário no sistema interno. Após aprovação do RH e do budget, a vaga é publicada..."
              rows={6}
              className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
             
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              {[
                { label: 'Requisição Formal', desc: 'Aprovação hierárquica necessária' },
                { label: 'Demanda Direta', desc: 'Gestor solicita diretamente ao RH' },
                { label: 'Planejamento Anual', desc: 'Vagas planejadas no workforce' }
              ].map((option) => (
                <button
                  key={option.label}
                  onClick={() => {
                    setWizardData(prev => ({ ...prev, vagasAbertura: option.label + ': ' + option.desc }))
                    onSettingsChange(true)
                  }}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-md hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50 transition-all text-left"
                >
                  <div className="font-medium text-sm">{option.label}</div>
                  <div className="text-xs text-gray-600 mt-1">{option.desc}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Database className="w-5 h-5 text-gray-700" />
              Quais sistemas vocês usam?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm text-gray-800 dark:text-gray-200">
              Selecione os sistemas e plataformas que sua empresa utiliza no processo de recrutamento.
            </p>

            {['ATS', 'Workforce Planning', 'HRIS/Folha', 'Avaliação Técnica', 'Assessment', 'Assinatura Digital', 'Comunicação'].map((category) => (
              <div key={category}>
                <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">
                  {category}
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {sistemasDisponiveis.filter(s => s.category === category).map((sistema) => (
                    <button
                      key={sistema.id}
                      onClick={() => toggleSistema(sistema.id)}
                      className={`p-3 border rounded-md transition-all ${
                        wizardData.sistemasUsados.includes(sistema.id)
                          ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {wizardData.sistemasUsados.includes(sistema.id) && (
                          <Check className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium">{sistema.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Workflow className="w-5 h-5 text-gray-700" />
              Etapas do processo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200">
              Selecione as etapas que fazem parte do seu processo de recrutamento.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {etapasDisponiveis.map((etapa) => (
                <button
                  key={etapa}
                  onClick={() => toggleEtapa(etapa)}
                  className={`p-3 border rounded-md transition-all text-left ${
                    wizardData.etapasProcesso.includes(etapa)
                      ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded-md border flex items-center justify-center ${
                      wizardData.etapasProcesso.includes(etapa)
                        ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                        : 'border-gray-300'
                    }`}>
                      {wizardData.etapasProcesso.includes(etapa) && <Check className="w-3 h-3" />}
                    </div>
                    <span className="text-sm">{etapa}</span>
                  </div>
                </button>
              ))}
            </div>

            {wizardData.etapasProcesso.length > 0 && (
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                <h4 className="text-sm font-semibold mb-3">
                  Ordem das etapas selecionadas:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {wizardData.etapasProcesso.map((etapa, index) => (
                    <Badge key={etapa} variant="secondary" className="px-3 py-1">
                      {index + 1}. {etapa}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {currentStep === 4 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="w-5 h-5 text-gray-700" />
                Automações desejadas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Selecione as automações que você gostaria de implementar no seu processo.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {automacoesDisponiveis.map((automacao) => (
                  <button
                    key={automacao.id}
                    onClick={() => toggleAutomacao(automacao.id)}
                    className={`p-4 border rounded-md transition-all text-left ${
                      wizardData.automacoesDesejadas.includes(automacao.id)
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-5 h-5 rounded-md border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        wizardData.automacoesDesejadas.includes(automacao.id)
                          ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                          : 'border-gray-300'
                      }`}>
                        {wizardData.automacoesDesejadas.includes(automacao.id) && <Check className="w-3 h-3" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{automacao.name}</div>
                        <div className="text-xs text-gray-600 mt-1">{automacao.desc}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <MessageSquare className="w-5 h-5 text-gray-700" />
                Canais de Comunicação com Candidatos
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Defina como a LIA poderá se comunicar com os candidatos durante o processo seletivo.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {canaisComunicacaoCandidatosDisponiveis.map((canal) => (
                  <button
                    key={canal.id}
                    onClick={() => toggleCanalComunicacaoCandidato(canal.id)}
                    className={`p-4 border rounded-md transition-all text-left ${
                      wizardData.canaisComunicacaoCandidatos.includes(canal.id)
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-2 text-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        wizardData.canaisComunicacaoCandidatos.includes(canal.id)
                          ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {canal.id === 'whatsapp' && <MessageSquare className="w-5 h-5" />}
                        {canal.id === 'email' && <Mail className="w-5 h-5" />}
                        {canal.id === 'ligacao' && <Phone className="w-5 h-5" />}
                        {canal.id === 'sms' && <MessageCircle className="w-5 h-5" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{canal.name}</div>
                        {canal.essential && (
                          <span className="text-micro text-gray-600 dark:text-gray-400 font-medium">Recomendado</span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {essentialChannelsRemoved && (
                <div className="flex items-start gap-3 p-4 bg-status-warning/10 border border-status-warning/30 rounded-md">
                  <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-status-warning">
                      Atenção: Canais essenciais desativados
                    </p>
                    <p className="text-xs text-status-warning mt-1">
                      Limitar os canais de comunicação pode comprometer a velocidade e eficiência do processo seletivo, 
                      reduzindo as chances de contato rápido com os melhores candidatos.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {currentStep === 5 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Globe className="w-5 h-5 text-gray-700" />
              Canais de Publicação
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200">
              Onde vocês publicam as vagas? Selecione os canais que sua empresa utiliza.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {canaisDisponiveis.map((canal) => (
                <button
                  key={canal.id}
                  onClick={() => toggleCanal(canal.id)}
                  className={`p-4 border rounded-md transition-all text-left ${
                    wizardData.canaisPublicacao.includes(canal.id)
                      ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-5 h-5 rounded-md border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      wizardData.canaisPublicacao.includes(canal.id)
                        ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                        : 'border-gray-300'
                    }`}>
                      {wizardData.canaisPublicacao.includes(canal.id) && <Check className="w-3 h-3" />}
                    </div>
                    <div>
                      <div className="font-medium text-sm">{canal.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{canal.desc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {wizardData.canaisPublicacao.includes('site_proprio') && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                <label className="text-sm font-medium">
                  URL da página de carreiras:
                </label>
                <input
                  type="url"
                  value={wizardData.careersPageUrl}
                  onChange={(e) => {
                    setWizardData(prev => ({ ...prev, careersPageUrl: e.target.value }))
                    onSettingsChange(true)
                  }}
                  placeholder="https://suaempresa.com/carreiras"
                  className="w-full mt-2 p-3 border border-gray-300 dark:border-gray-600 rounded-md text-sm"
                 
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Success Message */}
      {submitSuccess && (
        <Card className="border-status-success/30 bg-status-success/10 dark:bg-status-success/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-status-success flex items-center justify-center">
                <Check className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-status-success dark:text-status-success">
                  Jornada configurada com sucesso!
                </h3>
                <p className="text-sm text-status-success dark:text-status-success">
                  Suas configurações foram salvas. LIA está pronta para otimizar seu recrutamento.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Message */}
      {submitError && (
        <Card className="border-status-error/30 bg-status-error/10 dark:bg-status-error/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-status-error flex items-center justify-center">
                <X className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-status-error dark:text-status-error">
                  Erro ao salvar configuração
                </h3>
                <p className="text-sm text-status-error dark:text-status-error">
                  {submitError}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
          disabled={currentStep === 1 || isSubmitting}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Voltar
        </Button>
        {currentStep < 5 ? (
          <Button
            onClick={() => setCurrentStep(prev => Math.min(5, prev + 1))}
            className="bg-gray-900"
          >
            Próximo
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={submitWizard}
            disabled={isSubmitting || submitSuccess}
            style={{backgroundColor: isSubmitting ? 'var(--gray-400)' : 'var(--gray-600)'}}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : submitSuccess ? (
              <>
                <Check className="w-4 h-4 mr-2" />
                Configuração Salva
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Concluir Configuração
              </>
            )}
          </Button>
        )}
      </div>

      {/* Journey Map Preview */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Eye className="w-5 h-5 text-gray-700" />
            Mapa da Jornada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-6">
            {wizardData.etapasProcesso.length > 0 ? (
              <div className="flex items-center gap-2 overflow-x-auto pb-4">
                {wizardData.etapasProcesso.map((etapa, index) => (
                  <div key={etapa} className="flex items-center">
                    <div className="flex flex-col items-center">
                      <div
                        className="w-32 h-20 rounded-md border-2 flex items-center justify-center p-2 text-center"
                        style={{backgroundColor: 'white'}}
                      >
                        <span className="text-xs font-medium">
                          {etapa}
                        </span>
                      </div>
                      <span className="text-xs text-gray-600 mt-2">Etapa {index + 1}</span>
                    </div>
                    {index < wizardData.etapasProcesso.length - 1 && (
                      <ArrowRight className="w-6 h-6 mx-2 text-gray-500 flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-600">
                <Map className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">
                  Selecione as etapas do processo para visualizar o mapa da jornada
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
  