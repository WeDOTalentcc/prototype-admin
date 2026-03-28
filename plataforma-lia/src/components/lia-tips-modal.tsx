"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, Brain, MessageSquare, Users, Briefcase, BarChart3, BookOpen, Settings,
  Target, Search, Calendar, FileText, Zap, HelpCircle, Star, Database, Video, Phone,
  Copy, Play, Filter, ExternalLink
} from "lucide-react"

interface LIATipsModalProps {
  isOpen: boolean
  onClose: () => void
  currentPage?: string
  onNavigateToLibrary?: () => void
  onNavigateToChat?: () => void
}

const tipCategories = [
  {
    id: "general",
    name: "Geral",
    icon: Brain,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Use linguagem natural - a LIA entende contexto e nuances",
      "Seja específico nos critérios e filtros para melhores resultados",
      "Combine comandos diferentes para fluxos mais complexos",
      "A LIA aprende com suas interações e melhora suas sugestões",
      "Use comandos específicos como 'encontrar candidatos React'",
      "Pergunte sobre métricas: 'qual nossa taxa de conversão?'",
      "Solicite análises: 'compare candidatos por score'",
      "Configure automações: 'agende follow-up automático'"
    ]
  },
  {
    id: "candidates",
    name: "Candidatos",
    icon: Users,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Analise perfis individuais: 'Analise o perfil do João Silva'",
      "Compare candidatos: 'Compare os top 5 para UX Designer'",
      "Monte pipelines: 'Monte pipeline com candidatos sênior'",
      "Busque com critérios específicos: 'Busque React com 5+ anos'",
      "Agende entrevistas: 'Marque entrevista com Ana para terça'",
      "Envie follow-ups: 'Email para candidatos em processo'",
      "Calcule scores: 'Score de compatibilidade dos ativos'",
      "Analise diversidade: 'Relatório de diversidade aprovados'"
    ]
  },
  {
    id: "jobs",
    name: "Vagas",
    icon: Briefcase,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Crie vagas: 'Nova vaga para Data Scientist Sênior'",
      "Publique vagas: 'Publique Frontend Developer no LinkedIn'",
      "Analise funis: 'Analise funil da vaga Product Manager'",
      "Otimize descrições: 'Melhore descrição para atrair mais'",
      "Configure triagem: 'Setup processo automático'",
      "Compare métricas: 'Compare vagas similares'",
      "Analise concorrência: 'Pesquise salários no mercado'",
      "Crie templates: 'Template para vagas recorrentes'"
    ]
  },
  {
    id: "analytics",
    name: "Indicadores",
    icon: BarChart3,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Explique tendências: 'Por que caiu o Time to Hire?'",
      "Gere relatórios: 'Relatório diversidade mensal'",
      "Compare performance: 'Performance por departamento'",
      "Analise conversões: 'Tendências por canal'",
      "Identifique gargalos: 'Onde está o problema?'",
      "Projete necessidades: 'Contratações próximo trimestre'",
      "Calcule ROI: 'Retorno dos investimentos'",
      "Benchmarks: 'Compare com mercado'"
    ]
  },
  {
    id: "automation",
    name: "Automações",
    icon: Zap,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Configure triagem automática para posições",
      "Setup follow-ups automáticos para candidatos",
      "Crie alertas para candidatos ideais",
      "Configure lembretes de entrevistas",
      "Automatize envio de feedback requests",
      "Setup sync automático com ATS",
      "Configure relatórios automáticos",
      "Agende publicações em redes sociais"
    ]
  },
  {
    id: "integration",
    name: "Integrações",
    icon: Database,
    color: "text-gray-600 dark:text-gray-400",
    tips: [
      "Todas as ações são sincronizadas com seu ATS automaticamente",
      "Dados de candidatos e vagas são registrados em tempo real",
      "Relatórios extraem dados diretamente do sistema integrado",
      "Use Teams ou WhatsApp para comunicação por áudio",
      "Integre com LinkedIn para sourcing automático",
      "Sync com calendário para agendamentos",
      "Exporte relatórios para ferramentas externas",
      "Configure webhooks para notificações"
    ]
  }
]

const contextualTips = {
  "Tarefas": [
    "Pergunte sobre suas tarefas prioritárias do dia",
    "Solicite resumo das atividades e deadlines",
    "Crie relatório semanal de progresso",
    "Configure automações do seu workflow",
    "Analise sua produtividade semanal"
  ],
  "Candidatos": [
    "Analise perfis e gere resumos executivos",
    "Compare múltiplos candidatos lado a lado",
    "Monte pipelines organizados por critérios",
    "Agende entrevistas considerando disponibilidade",
    "Execute buscas avançadas com filtros inteligentes"
  ],
  "Vagas": [
    "Crie e publique vagas em múltiplos canais",
    "Analise performance e métricas de vagas",
    "Configure processos de triagem automática",
    "Otimize descrições para atrair candidatos",
    "Compare vagas similares e benchmarks"
  ],
  "Indicadores": [
    "Solicite insights detalhados sobre KPIs",
    "Explique tendências e variações",
    "Gere relatórios personalizados",
    "Execute análises preditivas",
    "Identifique oportunidades de melhoria"
  ],
  "Biblioteca LIA": [
    "Explore comandos organizados por categoria",
    "Aprenda a maximizar o potencial da IA",
    "Teste comandos diretamente na biblioteca",
    "Configure seu workspace personalizado",
    "Descubra automações avançadas"
  ],
  "Chat com LIA": [
    "Use linguagem natural para conversar",
    "Faça perguntas específicas sobre processos",
    "Solicite análises e relatórios detalhados",
    "Configure automações complexas",
    "Integre com ferramentas externas"
  ]
}

export function LIATipsModal({ isOpen, onClose, currentPage = "Tarefas", onNavigateToLibrary, onNavigateToChat }: LIATipsModalProps) {
  const [activeCategory, setActiveCategory] = useState("general")

  if (!isOpen) return null

  const currentContextTips = contextualTips[currentPage as keyof typeof contextualTips] || contextualTips["Tarefas"]

  // Funções para ações das dicas
  const handleCopyTip = (tip: string) => {
    navigator.clipboard.writeText(tip)
    // Poderia adicionar um toast de confirmação aqui
  }

  const handleUseInLibrary = (tip: string) => {
    // Salva a dica no localStorage para ser usada na biblioteca
    localStorage.setItem('lia-selected-command', tip)
    if (onNavigateToLibrary) {
      onNavigateToLibrary()
      onClose()
    }
  }

  const handleTestInChat = (tip: string) => {
    // Salva a dica no localStorage para ser usada no chat
    localStorage.setItem('lia-chat-prefill', tip)
    if (onNavigateToChat) {
      onNavigateToChat()
      onClose()
    }
  }

  const handleApplyFilter = (tip: string) => {
    // Salva a dica para ser usada nos filtros da página atual
    localStorage.setItem('lia-filter-suggestion', tip)
    localStorage.setItem('lia-filter-page', currentPage)
    onClose()
    // A página atual pode detectar isso e aplicar o filtro
  }

  // Componente para botões de ação de cada dica
  const TipActionButtons = ({ tip, isCommand = false }: { tip: string, isCommand?: boolean }) => (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      <Button
        size="sm"
        variant="ghost"
        onClick={() => handleCopyTip(tip)}
        className="h-6 px-2 text-xs"
        title="Copiar dica"
      >
        <Copy className="w-3 h-3" />
      </Button>

      {isCommand && (
        <>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleTestInChat(tip)}
            className="h-6 px-2 text-xs text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark"
            title="Testar no chat"
          >
            <Play className="w-3 h-3" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleUseInLibrary(tip)}
            className="h-6 px-2 text-xs text-status-success hover:text-status-success"
            title="Usar na biblioteca"
          >
            <BookOpen className="w-3 h-3" />
          </Button>
        </>
      )}

      <Button
        size="sm"
        variant="ghost"
        onClick={() => handleApplyFilter(tip)}
        className="h-6 px-2 text-xs text-wedo-purple hover:text-wedo-purple"
        title="Aplicar como filtro"
      >
        <Filter className="w-3 h-3" />
      </Button>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div 
        className="bg-white dark:bg-gray-900 rounded-md w-full max-w-3xl max-h-[80vh] overflow-hidden border border-gray-200 dark:border-gray-700"
       
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md flex items-center justify-center bg-wedo-cyan/15">
                <Brain className="w-5 h-5 text-wedo-cyan" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                  Dicas e Comandos da LIA
                </h2>
                <p className="text-xs text-gray-800 dark:text-gray-200">
                  Aprenda a maximizar o potencial da sua assistente de IA
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0 text-gray-600 hover:text-gray-700">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex h-[calc(80vh-70px)]">
          {/* Sidebar Categories */}
          <div className="w-56 bg-gray-50 dark:bg-gray-900/50 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <div className="p-3">
              <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 uppercase tracking-wide">Categorias</h3>
              <div className="space-y-0.5">
                {tipCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left transition-colors ${
                      activeCategory === category.id
                        ? 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                        : 'hover:bg-white dark:hover:bg-gray-800 border border-transparent'
                    }`}
                  >
                    <category.icon className={`w-3.5 h-3.5 ${activeCategory === category.id ? 'text-gray-800 dark:text-gray-200' : 'text-gray-600'}`} />
 <span className={`text-xs font-medium ${activeCategory === category.id ? 'text-gray-950' : 'text-gray-600 dark:text-gray-400'}`}>
                      {category.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900/50">
            <div className="p-4">
              {/* Context-specific tips for current page */}
              {activeCategory === "general" && (
                <Card className="mb-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                  <CardHeader className="pb-3 pt-3 px-4">
                    <CardTitle className="text-xs flex items-center gap-2 font-medium text-gray-800 dark:text-gray-200">
                      <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      Dicas para "{currentPage}"
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <div className="space-y-2">
                      {currentContextTips.map((tip, index) => (
                        <div key={index} className="group p-2.5 bg-gray-50 dark:bg-gray-900/50 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-white dark:hover:bg-gray-800 transition-colors">
                          <div className="flex items-start gap-2">
                            <span className="text-gray-600 mt-0.5 text-xs">•</span>
                            <div className="flex-1">
                              <p className="text-xs text-gray-800 dark:text-gray-200">{tip}</p>
                              <TipActionButtons tip={tip} isCommand={tip.includes('"') || tip.includes('Analise') || tip.includes('Compare')} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Category tips */}
              <div className="space-y-3">
                {tipCategories
                  .filter(cat => activeCategory === cat.id)
                  .map((category) => (
                    <div key={category.id}>
                      <div className="flex items-center gap-2 mb-3">
                        <category.icon className={`w-4 h-4 ${category.color}`} />
                        <h3 className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                          {category.name}
                        </h3>
                      </div>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                        {category.tips.map((tip, index) => (
                          <div
                            key={index}
                            className="group p-2.5 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:transition-all duration-200"
                          >
                            <p className="text-xs text-gray-800 dark:text-gray-200">
                              {tip}
                            </p>
                            <TipActionButtons
                              tip={tip}
                              isCommand={
                                tip.includes('"') ||
                                tip.includes('Analise') ||
                                tip.includes('Compare') ||
                                tip.includes('Monte') ||
                                tip.includes('Busque') ||
                                tip.includes('Crie') ||
                                tip.includes('Gere') ||
                                tip.includes('Configure')
                              }
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>

              {/* Integration info */}
              {activeCategory === "integration" && (
                <Card className="mt-4 bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30">
                  <CardHeader className="pb-2 pt-3 px-3">
                    <CardTitle className="text-xs flex items-center gap-2 font-medium">
                      <Database className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
                      Canais de Comunicação
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-3 pb-3">
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 h-7 text-xs"
                        onClick={() => window.open('https://teams.microsoft.com', '_blank')}
                      >
                        <Video className="w-3 h-3" />
                        Teams
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 h-7 text-xs"
                        onClick={() => window.open('https://wa.me/5511999999999?text=Olá LIA, preciso de ajuda', '_blank')}
                      >
                        <Phone className="w-3 h-3" />
                        WhatsApp
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Actions Help */}
              <Card className="mt-4 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                <CardHeader className="pb-2 pt-3 px-3">
                  <CardTitle className="text-xs flex items-center gap-2 font-medium">
                    <HelpCircle className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    Ações Disponíveis
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-3 pb-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      <Copy className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                      <span className="text-gray-600 dark:text-gray-400">Copiar dica</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Play className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                      <span className="text-gray-600 dark:text-gray-400">Testar no chat</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <BookOpen className="w-3 h-3 text-status-success" />
                      <span className="text-gray-600 dark:text-gray-400">Usar na biblioteca</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Filter className="w-3 h-3 text-wedo-purple" />
                      <span className="text-gray-600 dark:text-gray-400">Aplicar como filtro</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
