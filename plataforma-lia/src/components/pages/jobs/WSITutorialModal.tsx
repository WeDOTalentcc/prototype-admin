"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  AlertCircle,
  BookOpen,
  Brain,
  CheckCircle,
  ClipboardList,
  GraduationCap,
  Layers3,
  Lightbulb,
  Scale,
  Settings2,
  X,
} from "lucide-react"

interface WSITutorialModalProps {
  open: boolean
  onClose: () => void
}

export function WSITutorialModal({ open, onClose }: WSITutorialModalProps) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-md w-full max-w-3xl max-h-[85vh] border border-gray-200 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-md">
              <GraduationCap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <h3 className="text-sm font-semibold text-gray-950">
              Tutorial: Metodologia WSI
            </h3>
            <Badge className="text-micro px-2 py-0.5 h-5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
              WeDoTalent Skill Index
            </Badge>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Seção 1: O que é WSI? */}
          <div className="p-4 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-gray-100 dark:to-gray-800 border border-gray-300 dark:border-gray-600 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h4 className="text-xs font-semibold text-gray-950">O que é WSI?</h4>
            </div>
            <p className="text-xs text-gray-800 leading-relaxed">
              <strong>WeDoTalent Skill Index</strong> é um índice conversacional proprietário que combina
              IA com psicometria para validar competências técnicas, comportamentais e fit cultural em
              triagens de <strong>5-10 minutos</strong>.
            </p>
          </div>

          {/* Seção 2: Base Teórica */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-4 h-4 text-wedo-purple" />
              <h4 className="text-xs font-semibold text-gray-950">Base Teórica (4 Modelos Científicos)</h4>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-white rounded-md border border-gray-100">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 dark:bg-gray-900 text-gray-600">CBI</Badge>
                  <span className="text-micro text-gray-600">McClelland, 1973</span>
                </div>
                <p className="text-micro text-gray-800">
                  Competency-Based Interviewing - perguntas situacionais baseadas em comportamentos passados
                </p>
              </div>
              <div className="p-3 bg-white rounded-md border border-gray-100">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-status-success/15 text-status-success">Bloom</Badge>
                  <span className="text-micro text-gray-600">Anderson et al., 2001</span>
                </div>
                <p className="text-micro text-gray-800">
                  Taxonomia de níveis cognitivos (Lembrar → Criar)
                </p>
              </div>
              <div className="p-3 bg-white rounded-md border border-gray-100">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-orange/15 text-wedo-orange">Dreyfus</Badge>
                  <span className="text-micro text-gray-600">1980</span>
                </div>
                <p className="text-micro text-gray-800">
                  Estágios de domínio de habilidade (1-5: Novice → Expert)
                </p>
              </div>
              <div className="p-3 bg-white rounded-md border border-gray-100">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/15 text-wedo-purple">Big Five</Badge>
                  <span className="text-micro text-gray-600">1992</span>
                </div>
                <p className="text-micro text-gray-800">
                  Traços comportamentais para fit cultural
                </p>
              </div>
            </div>
          </div>

          {/* Seção 3: Versões do WSI - Tabela */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <Layers3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <h4 className="text-xs font-semibold text-gray-950">Versões do WSI</h4>
            </div>
            <div className="overflow-hidden rounded-md border border-gray-200">
              <table className="w-full text-xs">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-2 font-semibold text-gray-800">Modelo</th>
                    <th className="text-center p-2 font-semibold text-gray-800">Perguntas</th>
                    <th className="text-center p-2 font-semibold text-gray-800">Tempo</th>
                    <th className="text-left p-2 font-semibold text-gray-800">Indicado Para</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  <tr>
                    <td className="p-2">
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">WSI Compact</Badge>
                    </td>
                    <td className="p-2 text-center text-gray-800">6-8</td>
                    <td className="p-2 text-center text-gray-800">5-7 min</td>
                    <td className="p-2 text-gray-800">Triagens rápidas, alto volume</td>
                  </tr>
                  <tr>
                    <td className="p-2">
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/15 text-wedo-purple">WSI Compact+</Badge>
                    </td>
                    <td className="p-2 text-center text-gray-800">8-10</td>
                    <td className="p-2 text-center text-gray-800">7-9 min</td>
                    <td className="p-2 text-gray-800">Vagas críticas, tech leads, gestão</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Seção 4: 7 Blocos da Triagem */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <ClipboardList className="w-4 h-4 text-gray-600" />
              <h4 className="text-xs font-semibold text-gray-950">7 Blocos da Triagem</h4>
            </div>
            <div className="space-y-2">
              {[
                { id: '0', name: 'Abordagem Inicial WhatsApp', time: '<1min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
                { id: '1', name: 'Apresentação da Oportunidade', time: '3min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
                { id: '2', name: 'Perguntas Padrão da Empresa', time: '2min', type: 'empresa', color: 'bg-wedo-cyan/15 text-wedo-cyan-dark' },
                { id: '3', name: 'Elegibilidade WSI', time: '2min', type: 'editável', color: 'bg-status-success/15 text-status-success' },
                { id: '4', name: 'Avaliação Técnica', time: '5min', type: 'editável', color: 'bg-status-success/15 text-status-success' },
                { id: '5', name: 'Análise Situacional e Fit', time: '4min', type: 'editável', color: 'bg-status-success/15 text-status-success' },
                { id: '6', name: 'Resultado e Encerramento', time: '3min', type: 'automático', color: 'bg-gray-100 text-gray-800' },
              ].map((block) => (
                <div key={block.id} className="flex items-center gap-3 p-2 bg-white rounded-md border border-gray-100">
                  <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                    <span className="text-micro font-semibold text-gray-900 dark:text-gray-50">{block.id}</span>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-gray-950">{block.name}</span>
                  </div>
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-600 border border-gray-200">
                    {block.time}
                  </Badge>
                  <Badge className={`text-micro px-1.5 py-0 h-4 ${block.color}`}>
                    {block.type}
                  </Badge>
                </div>
              ))}
            </div>
            <p className="text-micro text-gray-600 mt-2 italic">
              Bloco 2: Perguntas configuradas em Configurações da Empresa → Perguntas de Triagem Padrão
            </p>
          </div>

          {/* Seção 5: Tipos de Validação */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="w-4 h-4 text-status-success" />
              <h4 className="text-xs font-semibold text-gray-950">Tipos de Validação</h4>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { name: 'Autodeclaração', desc: 'Base inicial de domínio', icon: '📝' },
                { name: 'Contexto real', desc: 'Aplicação prática', icon: '🎯' },
                { name: 'Microteste', desc: 'Raciocínio técnico', icon: '🧪' },
                { name: 'Situação contextual', desc: 'Fit comportamental', icon: '🎭' },
              ].map((type, idx) => (
                <div key={idx} className="flex items-start gap-2 p-2 bg-white rounded-md border border-gray-100">
                  <span className="text-xs">{type.icon}</span>
                  <div>
                    <span className="text-xs font-medium text-gray-950 block">{type.name}</span>
                    <span className="text-micro text-gray-600">{type.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Seção 6: Distribuição e Classificações */}
          <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-50 dark:to-gray-900 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <Scale className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <h4 className="text-xs font-semibold text-gray-950">Distribuição e Classificações</h4>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-micro text-gray-600 mb-1">Distribuição de Perguntas</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
                      <div className="h-full bg-gray-900 dark:bg-gray-50" style={{width: '70%'}}></div>
                    </div>
                    <span className="text-micro text-gray-800">70% técnicas</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-2 rounded-full bg-gray-200 overflow-hidden">
                      <div className="h-full bg-wedo-purple" style={{width: '30%'}}></div>
                    </div>
                    <span className="text-micro text-gray-800">30% comportamentais</span>
                  </div>
                </div>
              </div>
              <div className="p-2 bg-white rounded-md border border-gray-100">
                <p className="text-micro text-gray-600 mb-1">Fórmula de Cálculo</p>
                <p className="text-xs font-mono text-gray-950 bg-gray-50 px-2 py-1 rounded-full">WSI = Σ(Peso × Score) / 100</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-status-success/10 rounded-md border border-status-success/30 text-center">
                  <div className="text-xs font-semibold text-status-success">≥ 4.2</div>
                  <p className="text-micro text-status-success">Aprovado automático</p>
                </div>
                <div className="p-2 bg-status-warning/10 rounded-md border border-status-warning/30 text-center">
                  <div className="text-xs font-semibold text-status-warning">3.8-4.1</div>
                  <p className="text-micro text-status-warning">Revisão humana</p>
                </div>
                <div className="p-2 bg-status-error/10 rounded-md border border-status-error/30 text-center">
                  <div className="text-xs font-semibold text-status-error">&lt; 3.8</div>
                  <p className="text-micro text-status-error">Reprovado</p>
                </div>
              </div>
            </div>
          </div>

          {/* Seção 7: Score Mínimo e Quando Ajustar */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <Settings2 className="w-4 h-4 text-wedo-orange" />
              <h4 className="text-xs font-semibold text-gray-950">Ajuste de Score Mínimo</h4>
            </div>
            <div className="space-y-3">
              <p className="text-xs text-gray-800 leading-relaxed">
                O <strong>Score Mínimo de Aprovação</strong> (ex: 75%) é <strong>configurável pelo recrutador</strong>.
                O padrão do sistema é <strong>75%</strong> para auto-aprovação.
              </p>
              <div className="overflow-hidden rounded-md border border-gray-200">
                <table className="w-full text-xs">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-2 font-semibold text-gray-800">Cenário</th>
                      <th className="text-left p-2 font-semibold text-gray-800">Ação Recomendada</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    <tr>
                      <td className="p-2 text-gray-800">Taxa de aprovação muito baixa</td>
                      <td className="p-2 text-gray-800">Reduza o score (ex: 82% → 70%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-gray-800">Taxa de aprovação muito alta</td>
                      <td className="p-2 text-gray-800">Aumente o score (ex: 70% → 85%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-gray-800">Vaga muito específica/sênior</td>
                      <td className="p-2 text-gray-800">Score mais alto (80-90%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-gray-800">Vaga júnior/estágio</td>
                      <td className="p-2 text-gray-800">Score mais baixo (60-70%)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Seção 8: Saturação e Dynamic Cutoff */}
          <div className="p-4 bg-wedo-orange/10 border border-wedo-orange/30 rounded-md">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-wedo-orange" />
              <h4 className="text-xs font-semibold text-gray-950">Saturação e Dynamic Cutoff</h4>
            </div>
            <div className="space-y-3">
              <div className="p-3 bg-white rounded-md border border-wedo-orange/30">
                <p className="text-micro font-medium text-wedo-orange mb-1">Smart Saturation</p>
                <p className="text-xs text-gray-800 leading-relaxed">
                  Quando a vaga atinge <strong>20 candidatos aprovados</strong>, a triagem automática é pausada.
                  O sistema sugere ações: agendar entrevistas em lote, revisar candidatos ou desbloquear pipeline.
                </p>
              </div>
              <div className="p-3 bg-white rounded-md border border-wedo-orange/30">
                <p className="text-micro font-medium text-wedo-orange mb-1">Dynamic Cutoff (Top 25%)</p>
                <p className="text-xs text-gray-800 leading-relaxed">
                  Após <strong>30-50 triagens</strong>, o sistema aplica corte dinâmico selecionando automaticamente
                  os <strong>top 25%</strong> candidatos por percentil histórico, garantindo qualidade mesmo em alto volume.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-white rounded-md border border-wedo-orange/30 text-center">
                  <div className="text-sm font-semibold text-wedo-orange">20</div>
                  <p className="text-micro text-gray-600">Limite saturação</p>
                </div>
                <div className="p-2 bg-white rounded-md border border-wedo-orange/30 text-center">
                  <div className="text-sm font-semibold text-wedo-orange">30-50</div>
                  <p className="text-micro text-gray-600">Triagens p/ cutoff</p>
                </div>
              </div>
            </div>
          </div>

          {/* Nota de Calibração */}
          <div className="p-3 bg-gray-50 dark:bg-gray-900 border border-gray-900 dark:border-gray-50 rounded-md">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-micro font-medium text-gray-700 dark:text-gray-300 mb-1">Calibração Automática</p>
                <p className="text-micro text-gray-700 dark:text-gray-300 leading-relaxed">
                  Após atingir volume suficiente, a LIA recalibra automaticamente os cortes por percentil histórico,
                  mantendo a qualidade das contratações.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <p className="text-micro text-gray-600">
              Metodologia proprietária WeDoTalent • Baseada em 4 modelos científicos validados
            </p>
            <Button
              size="sm"
              className="h-7 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              onClick={onClose}
            >
              Entendi
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
