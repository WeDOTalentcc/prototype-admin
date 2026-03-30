"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { BarChart3, Brain, RefreshCw, Target, Wand2, X } from "lucide-react"

interface LIAQuestionsPanelProps {
  open: boolean
  onClose: () => void
}

export function LIAQuestionsPanel({ open, onClose }: LIAQuestionsPanelProps) {
  if (!open) return null

  return (
    <>
      {/* Overlay para fechar o painel ao clicar fora */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Painel Lateral */}
      <div className="fixed right-0 top-0 h-full z-50 w-[450px] bg-white dark:bg-lia-bg-primary" style={{animation: 'slideInRight 0.3s ease-out'}}>
        {/* Header */}
        <div className="bg-wedo-purple p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-md">
                <Wand2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold">Sugestões de Perguntas da LIA</h2>
                <p className="text-wedo-purple text-xs">Baseadas no perfil da vaga</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-lia-bg-primary/20 rounded-md transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Conteúdo */}
        <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                Perguntas Recomendadas para UX Design
              </h3>
            </div>
            <p className="text-xs text-gray-600 dark:text-lia-text-tertiary">
              Clique em "Substituir" para trocar a pergunta selecionada
            </p>
          </div>

          <div className="space-y-3">
            {/* Sugestão 1 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                  Qual método de pesquisa seria mais apropriado para validar a usabilidade de um protótipo em fase inicial?
                </h4>
                <div className="flex items-center gap-2">
                  <Badge className="bg-gray-200 text-gray-800 dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Recomendada</Badge>
                  <Badge className="bg-gray-100 text-gray-800 dark:text-lia-text-primary text-xs">2 min</Badge>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-lia-text-tertiary">
                <p>A) Teste A/B com grande amostra</p>
                <p>B) Card sorting</p>
                <p className="text-gray-950 dark:text-gray-50 font-bold">C) Teste de usabilidade moderado ✓</p>
                <p>D) Analytics quantitativo</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    Avalia: Métodos de Pesquisa
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Dificuldade: Médio
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Substituir
                </Button>
              </div>
            </div>

            {/* Sugestão 2 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                  Como você priorizaria funcionalidades em um MVP usando a matriz de esforço vs impacto?
                </h4>
                <div className="flex items-center gap-2">
                  <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-xs">Alta Relevância</Badge>
                  <Badge className="bg-gray-100 text-gray-800 dark:text-lia-text-primary text-xs">3 min</Badge>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-lia-text-tertiary">
                <p className="text-gray-950 dark:text-gray-50 font-bold">A) Alto impacto e baixo esforço primeiro ✓</p>
                <p>B) Alto esforço e alto impacto primeiro</p>
                <p>C) Baixo esforço independente do impacto</p>
                <p>D) Todas as funcionalidades igualmente</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    Avalia: Priorização
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Dificuldade: Fácil
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Substituir
                </Button>
              </div>
            </div>

            {/* Sugestão 3 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                  Qual é a diferença fundamental entre Design System e Style Guide?
                </h4>
                <div className="flex items-center gap-2">
                  <Badge className="bg-gray-200 text-gray-800 dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Conceitual</Badge>
                  <Badge className="bg-gray-100 text-gray-800 dark:text-lia-text-primary text-xs">2 min</Badge>
                </div>
              </div>
              <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-lia-text-tertiary">
                <p>A) Não há diferença, são sinônimos</p>
                <p className="text-gray-950 dark:text-gray-50 font-bold">B) Design System inclui componentes e padrões, Style Guide foca em visual ✓</p>
                <p>C) Style Guide é mais completo que Design System</p>
                <p>D) Design System é apenas para desenvolvedores</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-lia-text-primary">
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    Avalia: Conhecimento Técnico
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Dificuldade: Médio
                  </span>
                </div>
                <Button
                  size="sm"
                  className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                  onClick={onClose}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Substituir
                </Button>
              </div>
            </div>

            {/* Botão para gerar mais sugestões */}
            <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button variant="outline" className="w-full text-sm">
                <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                Gerar Mais Sugestões
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-lia-border-subtle dark:border-lia-border-subtle p-3 bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-800 dark:text-lia-text-primary">
              <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
              Baseado em 500+ testes
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs"
            >
              Fechar Painel
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
