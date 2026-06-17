"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
    color: "text-lia-text-secondary",
    tips: [
      "Use linguagem natural - a IA entende contexto e nuances",
      "Seja específico nos critérios e filtros para melhores resultados",
      "Combine comandos diferentes para fluxos mais complexos",
      "A IA aprende com suas interações e melhora suas sugestões",
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
    color: "text-lia-text-secondary",
    tips: [
      "Analise perfis individuais: 'Analise o perfil do João Silva'",
      "Compare candidatos: 'Compare os top 5 para UX Designer'",
      "Monte pipelines: 'Monte pipeline com candidatos sênior'",
      "Busque com critérios específicos: 'Busque React com 5+ anos'",
      "Agende entrevistas: 'Marque entrevista com Ana para terça'",
      "Envie follow-ups: 'Email para candidatos em processo'",
      "Calcule scores: 'Nota de compatibilidade dos ativos'",
      "Analise diversidade: 'Relatório de diversidade aprovados'"
    ]
  },
  {
    id: "jobs",
    name: "Vagas",
    icon: Briefcase,
    color: "text-lia-text-secondary",
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
    color: "text-lia-text-secondary",
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
    color: "text-lia-text-secondary",
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
    color: "text-lia-text-secondary",
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
  "Decidir": [
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

export function LIATipsModal({ isOpen, onClose, currentPage = "Decidir", onNavigateToLibrary, onNavigateToChat }: LIATipsModalProps) {
  const [activeCategory, setActiveCategory] = useState("general")

  if (!isOpen) return null

  const currentContextTips = contextualTips[currentPage as keyof typeof contextualTips] || contextualTips["Decidir"]

  // Funções para ações das dicas
  // ── sessionStorage keys handoff (Onda 4-N2 — documentação canonical) ──
  // Este componente é o ÚNICO PRODUTOR das 4 chaves sessionStorage abaixo.
  // Consumers identificados via grep (2026-05-24):
  //   - 'lia-selected-command' → consumido em src/components/lia-library/*
  //     (LiaLibraryPage lê no mount via useEffect pra pré-selecionar template)
  //   - 'lia-chat-prefill' → consumido em src/components/unified-chat/UnifiedChat.tsx
  //     (useEffect que pré-preenche inputText e dispara handleSend)
  //   - 'lia-filter-suggestion' + 'lia-filter-page' → consumido em
  //     src/components/funil-de-talentos/* (page lê ambas pra aplicar filtro
  //     contextual quando user veio do tips-modal)
  // sessionStorage (não localStorage) é intencional — handoff cross-page
  // dentro da MESMA sessão de browser; chave morre quando aba fecha (sem TTL).
  const handleCopyTip = (tip: string) => {
    navigator.clipboard.writeText(tip)
    // Poderia adicionar um toast de confirmação aqui
  }

  const handleUseInLibrary = (tip: string) => {
    // Onda 4-N2: handoff pra LiaLibraryPage via sessionStorage canonical
    sessionStorage.setItem('lia-selected-command', tip)
    if (onNavigateToLibrary) {
      onNavigateToLibrary()
      onClose()
    }
  }

  const handleTestInChat = (tip: string) => {
    // Onda 4-N2: handoff pra UnifiedChat via sessionStorage canonical
    sessionStorage.setItem('lia-chat-prefill', tip)
    if (onNavigateToChat) {
      onNavigateToChat()
      onClose()
    }
  }

  const handleApplyFilter = (tip: string) => {
    // Onda 4-N2: handoff pra funil-de-talentos via sessionStorage canonical
    // (par filter-suggestion + filter-page lido no mount pra aplicar filtro
    // contextual baseado em qual página estava ativa quando user clicou)
    sessionStorage.setItem('lia-filter-suggestion', tip)
    sessionStorage.setItem('lia-filter-page', currentPage)
    onClose()
  }

  // Componente para botões de ação de cada dica
  const TipActionButtons = ({ tip, isCommand = false }: { tip: string, isCommand?: boolean }) => (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
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
            className="h-6 px-2 text-xs text-lia-text-secondary hover:text-wedo-cyan-dark"
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
        className="h-6 px-2 text-xs text-wedo-purple-text hover:text-wedo-purple"
        title="Aplicar como filtro"
      >
        <Filter className="w-3 h-3" />
      </Button>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-lia-overlay z-50 flex items-center justify-center p-4">
      <div 
        className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-3xl max-h-[80vh] overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle"
       
      >
        {/* Header */}
        <div className="px-4 py-3 dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md flex items-center justify-center bg-wedo-cyan/15">
                <Brain className="w-5 h-5 text-wedo-cyan" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-lia-text-primary">
                  Dicas e Comandos de IA
                </h2>
                <p className="text-xs text-lia-text-primary">
                  Aprenda a maximizar o potencial da sua assistente de IA
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0 text-lia-text-secondary hover:text-lia-text-secondary">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex h-[calc(80vh-70px)]">
          {/* Sidebar Categories */}
          <div className="w-56 bg-lia-bg-secondary dark:bg-lia-bg-primary/50 border-r border-lia-border-subtle dark:border-lia-border-subtle overflow-y-auto">
            <div className="p-3">
              <h3 className="text-xs font-medium text-lia-text-primary mb-2 uppercase tracking-wide">Categorias</h3>
              <div className="space-y-0.5">
                {tipCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-left transition-colors motion-reduce:transition-none ${
 activeCategory === category.id
                        ? 'bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle'
                        : 'hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover border border-transparent'
                    }`}
                  >
                    <category.icon className={`w-3.5 h-3.5 ${activeCategory === category.id ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`} />
 <span className={`text-xs font-medium ${activeCategory === category.id ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                      {category.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto bg-lia-bg-secondary dark:bg-lia-bg-primary/50">
            <div className="p-4">
              {/* Context-specific tips for current page */}
              {activeCategory === "general" && (
                <Card className="mb-4 bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardHeader className="pb-3 pt-3 px-4">
                    <CardTitle className="text-xs flex items-center gap-2 font-medium text-lia-text-primary">
                      <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      Dicas para "{currentPage}"
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <div className="space-y-2">
                      {currentContextTips.map((tip, index) => (
                        <div key={`ctx-tip-${index}`} className="group p-2.5 bg-lia-bg-secondary dark:bg-lia-bg-primary/50 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none">
                          <div className="flex items-start gap-2">
                            <span className="text-lia-text-secondary mt-0.5 text-xs">•</span>
                            <div className="flex-1">
                              <p className="text-xs text-lia-text-primary">{tip}</p>
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
                        <h3 className="text-base-ui font-semibold text-lia-text-primary">
                          {category.name}
                        </h3>
                      </div>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                        {category.tips.map((tip, index) => (
                          <div
                            key={`cat-tip-${index}`}
                            className="group p-2.5 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle transition-colors motion-reduce:transition-none duration-200"
                          >
                            <p className="text-xs text-lia-text-primary">
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
                        onClick={() => {
                          const teamsUrl = process.env.NEXT_PUBLIC_TEAMS_URL || 'https://teams.microsoft.com'
                          window.open(teamsUrl, '_blank')
                        }}
                      >
                        <Video className="w-3 h-3" />
                        Teams
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 h-7 text-xs"
                        onClick={() => {
                          const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || ''
                          if (!whatsappNumber) {
                            console.warn('NEXT_PUBLIC_WHATSAPP_NUMBER not configured')
                            return
                          }
                          window.open(`https://wa.me/${whatsappNumber}?text=Olá LIA, preciso de ajuda`, '_blank')
                        }}
                      >
                        <Phone className="w-3 h-3" />
                        WhatsApp
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Actions Help */}
              <Card className="mt-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                <CardHeader className="pb-2 pt-3 px-3">
                  <CardTitle className="text-xs flex items-center gap-2 font-medium">
                    <HelpCircle className="w-3.5 h-3.5 text-lia-text-secondary" />
                    Ações Disponíveis
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-3 pb-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      <Copy className="w-3 h-3 text-lia-text-primary" />
                      <span className="text-lia-text-secondary">Copiar dica</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Play className="w-3 h-3 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">Testar no chat</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <BookOpen className="w-3 h-3 text-status-success" />
                      <span className="text-lia-text-secondary">Usar na biblioteca</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Filter className="w-3 h-3 text-wedo-purple" />
                      <span className="text-lia-text-secondary">Aplicar como filtro</span>
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
