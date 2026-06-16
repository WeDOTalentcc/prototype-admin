"use client"

import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
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
} from"lucide-react"

interface WSITutorialModalProps {
  open: boolean
  onClose: () => void
}

export function WSITutorialModal({ open, onClose }: WSITutorialModalProps) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 bg-lia-overlay-light backdrop-blur-[1px] z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-lia-bg-primary rounded-xl w-full max-w-3xl max-h-[85vh] border border-lia-border-subtle flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 shrink-0">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-lia-bg-tertiary rounded-xl">
              <GraduationCap className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Tutorial: Metodologia WSI
            </h3>
            <Chip variant="neutral" muted className="text-micro px-2 py-0.5 h-5 bg-lia-bg-tertiary text-lia-text-secondary">
              WeDoTalent Skill Index
            </Chip>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4 text-lia-text-secondary" />
          </button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Seção 1: O que é WSI? */}
          <div className="p-4 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-tertiary border border-lia-border-default rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <h4 className="text-xs font-semibold text-lia-text-primary">O que é WSI?</h4>
            </div>
            <p className="text-xs text-lia-text-primary leading-relaxed">
              <strong>WeDoTalent Skill Index</strong> é um índice conversacional proprietário que combina
              IA com psicometria para validar competências técnicas, comportamentais e aderência cultural em
              triagens de <strong>5-10 minutos</strong>.
            </p>
          </div>

          {/* Seção 2: Base Teórica */}
          <div className="p-4 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-4 h-4 text-wedo-purple" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Base Teórica (4 Modelos Científicos)</h4>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 mb-1">
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-secondary text-lia-text-secondary">CBI</Chip>
                  <span className="text-micro text-lia-text-secondary">McClelland, 1973</span>
                </div>
                <p className="text-micro text-lia-text-primary">
                  Competency-Based Interviewing - perguntas situacionais baseadas em comportamentos passados
                </p>
              </div>
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 mb-1">
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">Bloom</Chip>
                  <span className="text-micro text-lia-text-secondary">Anderson et al., 2001</span>
                </div>
                <p className="text-micro text-lia-text-primary">
                  Taxonomia de níveis cognitivos (Lembrar → Criar)
                </p>
              </div>
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 mb-1">
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">Dreyfus</Chip>
                  <span className="text-micro text-lia-text-secondary">1980</span>
                </div>
                <p className="text-micro text-lia-text-primary">
                  Estágios de domínio de habilidade (1-5: Novice → Expert)
                </p>
              </div>
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 mb-1">
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">Big Five</Chip>
                  <span className="text-micro text-lia-text-secondary">1992</span>
                </div>
                <p className="text-micro text-lia-text-primary">
                  Traços comportamentais para aderência cultural
                </p>
              </div>
            </div>
          </div>

          {/* Seção 3: Versões do WSI - Tabela */}
          <div className="p-4 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <Layers3 className="w-4 h-4 text-lia-text-secondary" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Versões do WSI</h4>
            </div>
            <div className="overflow-hidden rounded-xl border border-lia-border-subtle">
              <table className="w-full text-xs">
                <thead className="bg-lia-bg-tertiary">
                  <tr>
                    <th className="text-left p-2 font-semibold text-lia-text-primary">Modelo</th>
                    <th className="text-center p-2 font-semibold text-lia-text-primary">Perguntas</th>
                    <th className="text-center p-2 font-semibold text-lia-text-primary">Tempo</th>
                    <th className="text-left p-2 font-semibold text-lia-text-primary">Indicado Para</th>
                  </tr>
                </thead>
                <tbody className="bg-lia-bg-primary divide-y divide-lia-border-subtle">
                  <tr>
                    <td className="p-2">
                      <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary">WSI Compact</Chip>
                    </td>
                    <td className="p-2 text-center text-lia-text-primary">6-8</td>
                    <td className="p-2 text-center text-lia-text-primary">5-7 min</td>
                    <td className="p-2 text-lia-text-primary">Triagens rápidas, alto volume</td>
                  </tr>
                  <tr>
                    <td className="p-2">
                      <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">WSI Compact+</Chip>
                    </td>
                    <td className="p-2 text-center text-lia-text-primary">8-10</td>
                    <td className="p-2 text-center text-lia-text-primary">7-9 min</td>
                    <td className="p-2 text-lia-text-primary">Vagas críticas, tech leads, gestão</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Seção 4: 7 Blocos da Triagem */}
          <div className="p-4 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <ClipboardList className="w-4 h-4 text-lia-text-secondary" />
              <h4 className="text-xs font-semibold text-lia-text-primary">7 Blocos da Triagem</h4>
            </div>
            <div className="space-y-2">
              {[
                { id: '0', name: 'Abordagem Inicial WhatsApp', time: '<1min', type: 'automático', color: 'bg-lia-bg-tertiary text-lia-text-primary' },
                { id: '1', name: 'Apresentação da Oportunidade', time: '3min', type: 'automático', color: 'bg-lia-bg-tertiary text-lia-text-primary' },
                { id: '2', name: 'Perguntas Padrão da Empresa', time: '2min', type: 'empresa', color: '' },
                { id: '3', name: 'Elegibilidade WSI', time: '2min', type: 'editável', color: '' },
                { id: '4', name: 'Avaliação Técnica', time: '5min', type: 'editável', color: '' },
                { id: '5', name: 'Análise Situacional e Fit', time: '4min', type: 'editável', color: '' },
                { id: '6', name: 'Resultado e Encerramento', time: '3min', type: 'automático', color: 'bg-lia-bg-tertiary text-lia-text-primary' },
              ].map((block) => (
                <div key={block.id} className="flex items-center gap-3 p-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                  <div className="w-6 h-6 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
                    <span className="text-micro font-semibold text-lia-text-primary">{block.id}</span>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-lia-text-primary">{block.name}</span>
                  </div>
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle">
                    {block.time}
                  </Chip>
                  <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 flex items-center ${block.color}`}>
                    {block.type}
                  </Chip>
                </div>
              ))}
            </div>
            <p className="text-micro text-lia-text-secondary mt-2 italic">
              Bloco 2: Perguntas configuradas em Configurações da Empresa → Perguntas de Triagem Padrão
            </p>
          </div>

          {/* Seção 5: Tipos de Validação */}
          <div className="p-4 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="w-4 h-4 text-status-success" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Tipos de Validação</h4>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { name: 'Autodeclaração', desc: 'Base inicial de domínio', icon: '📝' },
                { name: 'Contexto real', desc: 'Aplicação prática', icon: '🎯' },
                { name: 'Microteste', desc: 'Raciocínio técnico', icon: '🧪' },
                { name: 'Situação contextual', desc: 'Fit comportamental', icon: '🎭' },
              ].map((type, idx) => (
                <div key={idx} className="flex items-start gap-2 p-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                  <span className="text-xs">{type.icon}</span>
                  <div>
                    <span className="text-xs font-medium text-lia-text-primary block">{type.name}</span>
                    <span className="text-micro text-lia-text-secondary">{type.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Seção 6: Distribuição e Classificações */}
          <div className="p-4 bg-gradient-to-r from-lia-bg-secondary to-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <Scale className="w-4 h-4 text-lia-text-secondary" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Distribuição e Classificações</h4>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-micro text-lia-text-secondary mb-1">Distribuição de Perguntas</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 rounded-full bg-lia-interactive-active overflow-hidden">
                      <div className="h-full bg-lia-btn-primary-bg"></div>
                    </div>
                    <span className="text-micro text-lia-text-primary">70% técnicas</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-2 rounded-full bg-lia-interactive-active overflow-hidden">
                      <div className="h-full bg-wedo-purple"></div>
                    </div>
                    <span className="text-micro text-lia-text-primary">30% comportamentais</span>
                  </div>
                </div>
              </div>
              <div className="p-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <p className="text-micro text-lia-text-secondary mb-1">Fórmula de Cálculo</p>
                <p className="text-xs font-mono text-lia-text-primary bg-lia-bg-secondary px-2 py-1 rounded-full">WSI = Σ(Peso × Score) / 100</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-status-success/10 rounded-xl border border-status-success/30 text-center">
                  <div className="text-xs font-semibold text-status-success">≥ 4.2</div>
                  <p className="text-micro text-status-success">Aprovado automático</p>
                </div>
                <div className="p-2 bg-status-warning/10 rounded-xl border border-status-warning/30 text-center">
                  <div className="text-xs font-semibold text-status-warning">3.8-4.1</div>
                  <p className="text-micro text-status-warning">Revisão humana</p>
                </div>
                <div className="p-2 bg-status-error/10 rounded-xl border border-status-error/30 text-center">
                  <div className="text-xs font-semibold text-status-error">&lt; 3.8</div>
                  <p className="text-micro text-status-error">Reprovado</p>
                </div>
              </div>
            </div>
          </div>

          {/* Seção 7: Score Mínimo e Quando Ajustar */}
          <div className="p-4 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <Settings2 className="w-4 h-4 text-wedo-orange" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Ajuste de Score Mínimo</h4>
            </div>
            <div className="space-y-3">
              <p className="text-xs text-lia-text-primary leading-relaxed">
                O <strong>Score Mínimo de Aprovação</strong> (ex: 75%) é <strong>configurável pelo recrutador</strong>.
                O padrão do sistema é <strong>75%</strong> para auto-aprovação.
              </p>
              <div className="overflow-hidden rounded-xl border border-lia-border-subtle">
                <table className="w-full text-xs">
                  <thead className="bg-lia-bg-tertiary">
                    <tr>
                      <th className="text-left p-2 font-semibold text-lia-text-primary">Cenário</th>
                      <th className="text-left p-2 font-semibold text-lia-text-primary">Ação Recomendada</th>
                    </tr>
                  </thead>
                  <tbody className="bg-lia-bg-primary divide-y divide-lia-border-subtle">
                    <tr>
                      <td className="p-2 text-lia-text-primary">Taxa de aprovação muito baixa</td>
                      <td className="p-2 text-lia-text-primary">Reduza o score (ex: 82% → 70%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-lia-text-primary">Taxa de aprovação muito alta</td>
                      <td className="p-2 text-lia-text-primary">Aumente o score (ex: 70% → 85%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-lia-text-primary">Vaga muito específica/sênior</td>
                      <td className="p-2 text-lia-text-primary">Score mais alto (80-90%)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-lia-text-primary">Vaga júnior/estágio</td>
                      <td className="p-2 text-lia-text-primary">Score mais baixo (60-70%)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Seção 8: Saturação e Dynamic Cutoff */}
          <div className="p-4 bg-wedo-orange/10 border border-wedo-orange/30 rounded-xl">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-wedo-orange" />
              <h4 className="text-xs font-semibold text-lia-text-primary">Saturação e Dynamic Cutoff</h4>
            </div>
            <div className="space-y-3">
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-wedo-orange/30">
                <p className="text-micro font-medium text-wedo-orange-text mb-1">Smart Saturation</p>
                <p className="text-xs text-lia-text-primary leading-relaxed">
                  Quando a vaga atinge <strong>20 candidatos aprovados</strong>, a triagem automática é pausada.
                  O sistema sugere ações: agendar entrevistas em lote, revisar candidatos ou desbloquear pipeline.
                </p>
              </div>
              <div className="p-3 bg-lia-bg-primary rounded-xl border border-wedo-orange/30">
                <p className="text-micro font-medium text-wedo-orange-text mb-1">Dynamic Cutoff (Top 25%)</p>
                <p className="text-xs text-lia-text-primary leading-relaxed">
                  Após <strong>30-50 triagens</strong>, o sistema aplica corte dinâmico selecionando automaticamente
                  os <strong>top 25%</strong> candidatos por percentil histórico, garantindo qualidade mesmo em alto volume.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-lia-bg-primary rounded-xl border border-wedo-orange/30 text-center">
                  <div className="text-sm font-semibold text-wedo-orange-text">20</div>
                  <p className="text-micro text-lia-text-secondary">Limite saturação</p>
                </div>
                <div className="p-2 bg-lia-bg-primary rounded-xl border border-wedo-orange/30 text-center">
                  <div className="text-sm font-semibold text-wedo-orange-text">30-50</div>
                  <p className="text-micro text-lia-text-secondary">Triagens p/ cutoff</p>
                </div>
              </div>
            </div>
          </div>

          {/* Nota de Calibração */}
          <div className="p-3 bg-lia-bg-secondary border border-lia-border-medium rounded-xl">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary mt-0.5 shrink-0" />
              <div>
                <p className="text-micro font-medium text-lia-text-secondary mb-1">Calibração Automática</p>
                <p className="text-micro text-lia-text-secondary leading-relaxed">
                  Após atingir volume suficiente, a IA recalibra automaticamente os cortes por percentil histórico,
                  mantendo a qualidade das contratações.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 p-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <p className="text-micro text-lia-text-secondary">
              Metodologia proprietária WeDoTalent • Baseada em 4 modelos científicos validados
            </p>
            <Button
              size="sm"
              className="h-7 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
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
