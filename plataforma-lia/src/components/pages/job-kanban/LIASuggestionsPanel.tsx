"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Brain, RefreshCw, Target, Wand2, X } from "lucide-react"

interface LIASuggestionsPanelProps {
  open: boolean
  onClose: () => void
  selectedTriagemQuestion: string | null
}

export function LIASuggestionsPanel({ open, onClose, selectedTriagemQuestion }: LIASuggestionsPanelProps) {
  if (!open) return null

  const suggestions = selectedTriagemQuestion?.includes('tech') ? [
    'Como você estrutura um Design System escalável para múltiplas plataformas?',
    'Descreva sua experiência com métodos de pesquisa de usuário e como os aplica',
    'Como você mede o ROI de iniciativas de UX em produtos digitais?',
    'Qual sua abordagem para design responsivo e acessibilidade?',
    'Como você colabora com desenvolvedores para garantir a implementação fiel do design?'
  ] : [
    'Como você lida com prazos apertados e múltiplas entregas simultâneas?',
    'Descreva uma situação de conflito em equipe que você resolveu com sucesso',
    'Como você se mantém atualizado com as tendências e tecnologias da área?',
    'Qual foi seu maior desafio profissional e como o superou?',
    'Como você prioriza múltiplas demandas de diferentes stakeholders?'
  ]

  return (
    <>
      {/* Overlay para fechar o painel ao clicar fora */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Painel Lateral */}
      <div className="fixed right-0 top-0 h-full z-50 w-[450px] bg-white dark:bg-lia-bg-primary animate-slideInRight">
        {/* Header */}
        <div className="bg-wedo-purple p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-md">
                <Wand2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold">Sugestões de Perguntas da LIA</h2>
                <p className="text-wedo-purple text-xs">Para Triagem - {selectedTriagemQuestion}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-lia-bg-primary/20 rounded-md transition-colors motion-reduce:transition-none"
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
              <h3 className="text-sm font-semibold text-lia-text-primary">
                Perguntas Recomendadas para Triagem
              </h3>
            </div>
            <p className="text-xs text-lia-text-secondary">
              Clique em "Substituir" para trocar a pergunta selecionada
            </p>
          </div>

          <div className="space-y-3">
            {suggestions.map((pergunta, index) => (
              <div key={`suggestion-${index}`} className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-colors motion-reduce:transition-none group">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-sm font-medium text-lia-text-primary group-hover:text-lia-text-primary">
                    {pergunta}
                  </h4>
                  <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated text-xs">
                    {index === 0 ? 'Recomendada' : index === 1 ? 'Popular' : 'Sugerida'}
                  </Badge>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      Relevância: {index === 0 ? 'Muito Alta' : index < 3 ? 'Alta' : 'Média'}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white"
                    onClick={onClose}
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Substituir
                  </Button>
                </div>
              </div>
            ))}

            {/* Botão para gerar mais sugestões */}
            <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button
                variant="outline"
                className="w-full text-sm"
              >
                <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                Gerar Mais Sugestões
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-lia-border-subtle dark:border-lia-border-subtle p-3 bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <p className="text-xs text-lia-text-primary">
              <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
              Baseado no perfil da vaga
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
