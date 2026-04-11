"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { useState } from"react"
import { useModalA11y } from"@/hooks/ui/use-modal-a11y"
import {
  FileText,
  FileVideo,
  Mic,
  ChevronLeft,
  ChevronRight,
  ZoomOut,
  ZoomIn,
  RotateCw,
  Pause,
  Play,
  Download,
  X,
  Brain,
  MessageSquareText,
} from"lucide-react"
import { Image } from"lucide-react"
import { Button } from"@/components/ui/button"
import { Badge } from"@/components/ui/badge"
import { textStyles } from"@/lib/design-tokens"

export interface FileItem {
  name: string
  type?: string
  url?: string
  videoType?: string
  audioType?: string
  duration?: string
  transcript?: Array<{ timestamp?: string; time?: string; speaker?: string; role?: string; text?: string; content?: string }>
  highlights?: string[]
}

interface Candidate {
  avatar_url?: string
  avatar?: string
}

interface FilePreviewModalProps {
  showPreview: boolean
  selectedFile: FileItem | null
  previewType: 'pdf' | 'image' | 'video' | 'audio' | null
  onClose: () => void
  candidate: Candidate
}

export function FilePreviewModal({ showPreview, selectedFile, previewType, onClose, candidate }: FilePreviewModalProps) {
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfTotalPages, setPdfTotalPages] = useState<number | null>(null)
  const [imageZoom, setImageZoom] = useState(100)
  const [videoPlaying, setVideoPlaying] = useState(false)
  const [audioPlaying, setAudioPlaying] = useState(false)
  const dialogRef = useModalA11y(showPreview, onClose)

  if (!showPreview || !selectedFile) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-overlay flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-label={`Preview: ${selectedFile.name}`} className="bg-lia-bg-primary rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header do Preview */}
        <div className="flex items-center justify-between p-3 bg-lia-bg-primary">
          <div className="flex items-center gap-2">
            {previewType === 'pdf' && <FileText className="w-4 h-4 text-lia-text-primary" />}
            {previewType === 'image' && <Image className="w-4 h-4 text-lia-text-primary" />}
            {previewType === 'video' && <FileVideo className="w-4 h-4 text-status-error" />}
            {previewType === 'audio' && <Mic className="w-4 h-4 text-lia-text-tertiary" />}
            <span className="text-sm font-medium text-lia-text-primary">
              {selectedFile.name}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Controles específicos por tipo */}
            {previewType === 'pdf' && (
              <>
                <div className="flex items-center gap-1 bg-lia-bg-tertiary rounded-md px-2 py-1">
                  <Button size="sm" variant="ghost" className="p-0.5 h-5 w-5" onClick={() => setPdfPage(Math.max(1, pdfPage - 1))}>
                    <ChevronLeft className="w-3 h-3" />
                  </Button>
                  <span className="text-xs text-lia-text-secondary px-1">
                    {pdfPage} / {pdfTotalPages || 5}
                  </span>
                  <Button size="sm" variant="ghost" className="p-0.5 h-5 w-5" onClick={() => setPdfPage(Math.min(pdfTotalPages || 5, pdfPage + 1))}>
                    <ChevronRight className="w-3 h-3" />
                  </Button>
                </div>
              </>
            )}

            {previewType === 'image' && (
              <div className="flex items-center gap-1">
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(Math.max(25, imageZoom - 25))}>
                  <ZoomOut className="w-3 h-3" />
                </Button>
                <span className="text-xs text-lia-text-secondary w-10 text-center">
                  {imageZoom}%
                </span>
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(Math.min(200, imageZoom + 25))}>
                  <ZoomIn className="w-3 h-3" />
                </Button>
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6" onClick={() => setImageZoom(100)}>
                  <RotateCw className="w-3 h-3" />
                </Button>
              </div>
            )}

            {previewType === 'video' && (
              <Button
                size="sm"
                variant="ghost"
                className="p-1 h-6 w-6"
                onClick={() => setVideoPlaying(!videoPlaying)}
              >
                {videoPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
              </Button>
            )}

            {previewType === 'audio' && (
              <Button
                size="sm"
                variant="ghost"
                className="p-1 h-6 w-6"
                onClick={() => setAudioPlaying(!audioPlaying)}
              >
                {audioPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
              </Button>
            )}

            <Button size="sm" variant="outline" className="gap-1 px-2 py-1 text-xs h-6">
              <Download className="w-3 h-3" />
              Baixar
            </Button>

            <Button
              size="sm"
              variant="ghost"
              className="p-1 h-6 w-6"
              onClick={onClose}
              aria-label="Fechar preview"
              data-dismiss="true"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {/* Conteúdo do Preview com Transcrição para Vídeos */}
        <div className="p-4 overflow-auto">
          {previewType === 'pdf' && (
            <div className="bg-lia-bg-tertiary rounded-xl p-6 min-h-[600px] flex items-center justify-center">
              <div className="text-center">
                <FileText className="w-16 h-16 text-lia-text-secondary mx-auto mb-3" />
                <p className="text-lia-text-secondary mb-2">
                  Visualizando página {pdfPage} de {pdfTotalPages || 5}
                </p>
                <p className="text-sm text-lia-text-primary">
                  [Conteúdo do PDF seria renderizado aqui]
                </p>
              </div>
            </div>
          )}

          {previewType === 'image' && (
            <div className="flex items-center justify-center">
              <img
                src={selectedFile.url || candidate.avatar_url || candidate.avatar}
                alt={selectedFile.name}
                style={{width: `${imageZoom}%`, maxWidth: '100%'}}
                className="rounded-md transition-colors motion-reduce:transition-none duration-300"
              />
            </div>
          )}

          {previewType === 'video' && (
            <div className="grid grid-cols-3 gap-4">
              {/* Vídeo Player */}
              <div className="col-span-2">
                <div className="bg-black rounded-md aspect-video flex items-center justify-center">
                  <div className="text-center">
                    <FileVideo className="w-16 h-16 text-lia-text-secondary mx-auto mb-3" />
                    <p className="text-white mb-2">
                      {videoPlaying ? 'Reproduzindo vídeo...' : 'Clique para reproduzir'}
                    </p>
                    <p className="text-lia-text-secondary text-sm">
                      {selectedFile.name}
                    </p>
                  </div>
                </div>

                {/* Perguntas de Triagem (se for vídeo de prescreening) */}
                {selectedFile.videoType === 'prescreening' && (
                  <div className="mt-4 bg-lia-bg-primary rounded-xl p-3">
                    <h4 className="text-xs font-medium text-lia-text-primary mb-2 flex items-center gap-1">
                      <MessageSquareText className="w-3.5 h-3.5 text-lia-text-primary" />
                      Perguntas de Triagem
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>1.</span>
                        <p className={textStyles.bodySmall}>
                          Por favor, apresente-se e conte sobre sua experiência profissional
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>2.</span>
                        <p className={textStyles.bodySmall}>
                          Por que você está interessado nesta vaga e em nossa empresa?
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>3.</span>
                        <p className={textStyles.bodySmall}>
                          Quais são suas principais conquistas profissionais?
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>4.</span>
                        <p className={textStyles.bodySmall}>
                          Qual sua disponibilidade para início e expectativa salarial?
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Análise de IA com Parecer da LIA */}
                <div className="mt-4 bg-lia-bg-primary rounded-xl p-3">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-2 flex items-center gap-1">
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Análise da LIA
                  </h4>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Confiança</p>
                      <p className="text-sm font-bold text-lia-text-primary">92%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Comunicação</p>
                      <p className="text-sm font-bold text-lia-text-primary">95%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Clareza</p>
                      <p className="text-sm font-bold text-lia-text-primary">88%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Entusiasmo</p>
                      <p className="text-sm font-bold text-lia-text-primary">90%</p>
                    </div>
                  </div>

                  {/* Parecer da LIA */}
                  <div className="border-t border-lia-border-subtle pt-3">
                    <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      Parecer da LIA
                    </h5>
                    <div className="space-y-2 text-xs text-lia-text-secondary">
                      <p>
                        <span className="font-semibold text-lia-text-primary">Pontos Fortes:</span> O candidato demonstra excelente capacidade de comunicação,
                        com respostas claras e estruturadas. Apresenta postura profissional e confiante durante toda a entrevista.
                        Suas experiências são relevantes para a posição.
                      </p>
                      <p>
                        <span className="font-semibold text-lia-text-primary">Pontos de Atenção:</span> Poderia ter elaborado mais sobre metodologias
                        específicas de design. A resposta sobre trabalho em equipe foi um pouco genérica.
                      </p>
                      <p>
                        <span className="font-semibold text-lia-text-primary">Recomendação:</span> Candidato altamente recomendado para próxima fase.
                        Sugiro aprofundar questionamentos sobre liderança técnica e experiência com design systems em escala.
                      </p>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-lia-border-subtle">
                        <span className={textStyles.bodySmall}>Score Geral</span>
                        <Badge className="text-xs px-2 py-0.5 bg-status-success text-white" >
                          91% - Altamente Recomendado
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Feed de Transcrição - Melhorado */}
              <div className="col-span-1">
                <div className="bg-lia-bg-primary rounded-xl p-3 h-full overflow-y-auto">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-3 sticky top-0 bg-lia-bg-primary pb-2 border-b border-lia-border-subtle">
                    📝 Transcrição
                  </h4>

                  {/* Indicador do tipo de vídeo */}
                  <div className="mb-3 p-2 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
                    <div className="flex items-center gap-2">
                      <Badge className="text-xs px-1.5 py-0.5">
                        {selectedFile.videoType === 'interview' ? 'Entrevista Gravada' : 'Vídeo de Triagem'}
                      </Badge>
                      <span className={textStyles.bodySmall}>Duração: {selectedFile.duration || '3:45'}</span>
                    </div>
                  </div>

                  <div className="space-y-3 text-xs">
                    {selectedFile.transcript && selectedFile.transcript.length > 0 ? (
                      <>
                        {selectedFile.transcript.map((segment, idx) => (
                          <div key={idx} className="border-l-2 border-lia-border-medium dark:border-lia-border-medium pl-3">
                            <p className={`${textStyles.bodySmall} mb-1`}>
                              {segment.timestamp || segment.time || ''} • {segment.speaker || segment.role || 'Participante'}
                            </p>
                            <p className="text-lia-text-primary">"{segment.text || segment.content || ''}"
                            </p>
                          </div>
                        ))}
                      </>
                    ) : (
                      <div className="text-center py-4 text-lia-text-secondary">
                        <p className="text-xs">Transcrição não disponível para este vídeo</p>
                      </div>
                    )}

                    {/* Highlights identificados pela LIA - only show if data available */}
                    {selectedFile.highlights && selectedFile.highlights.length > 0 && (
                      <div className="mt-4 p-2 bg-lia-bg-primary rounded-xl">
                        <p className="text-xs font-semibold text-lia-text-primary mb-1">
                          🎯 Highlights da LIA
                        </p>
                        <ul className="space-y-1 text-xs text-lia-text-secondary">
                          {selectedFile.highlights.map((highlight, idx) => (
                            <li key={idx}>• {highlight}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Conteúdo do Modal para Áudio */}
          {previewType === 'audio' && (
            <div className="grid grid-cols-3 gap-4">
              {/* Áudio Player e Conteúdo Principal */}
              <div className="col-span-2">
                {/* Player de Áudio */}
                <div className="bg-lia-bg-tertiary rounded-xl p-4 flex items-center justify-center">
                  <div className="text-center w-full">
                    <div className="flex items-center justify-center mb-3">
                      <div className="w-16 h-16 rounded-full bg-lia-interactive-active flex items-center justify-center">
                        <Mic className="w-8 h-8 text-lia-text-secondary" />
                      </div>
                    </div>
                    <p className="text-lia-text-primary mb-2">
                      {audioPlaying ? 'Reproduzindo áudio...' : 'Clique para reproduzir'}
                    </p>
                    <p className="text-lia-text-tertiary text-sm mb-3">
                      {selectedFile.name}
                    </p>
                    {/* Barra de progresso */}
                    <div className="flex items-center gap-3 max-w-md mx-auto">
                      <Button
                        size="sm"
                        variant="outline"
                        className="p-2 h-8 w-8 rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active border-0"
                        onClick={() => setAudioPlaying(!audioPlaying)}
                      >
                        {audioPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white" />}
                      </Button>
                      <div className="flex-1">
                        <div className="h-2 bg-lia-interactive-active rounded-full overflow-hidden">
                          <div className="h-full bg-lia-btn-primary-bg rounded-full transition-[width,height]" style={{width: audioPlaying ? '35%' : '0%'}} />
                        </div>
                      </div>
                      <span className="text-xs text-lia-text-secondary font-mono w-20 text-right">
                        {audioPlaying ? '1:35' : '0:00'} / {selectedFile.duration || '4:32'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Perguntas de Triagem (se for áudio de prescreening) */}
                {selectedFile.audioType === 'prescreening' && (
                  <div className="mt-4 bg-lia-bg-primary rounded-xl p-3">
                    <h4 className="text-xs font-medium text-lia-text-primary mb-2 flex items-center gap-1">
                      <MessageSquareText className="w-3.5 h-3.5 text-lia-text-primary" />
                      Perguntas de Triagem
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>1.</span>
                        <p className={textStyles.bodySmall}>
                          Por favor, apresente-se e conte sobre sua experiência profissional
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>2.</span>
                        <p className={textStyles.bodySmall}>
                          Por que você está interessado nesta vaga e em nossa empresa?
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>3.</span>
                        <p className={textStyles.bodySmall}>
                          Quais são suas principais conquistas profissionais?
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className={`${textStyles.bodySmall} font-medium`}>4.</span>
                        <p className={textStyles.bodySmall}>
                          Qual sua disponibilidade para início e expectativa salarial?
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Análise de IA com Parecer da LIA */}
                <div className="mt-4 bg-lia-bg-primary rounded-xl p-3">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-2 flex items-center gap-1">
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Análise da LIA
                  </h4>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Clareza</p>
                      <p className="text-sm font-bold text-lia-text-primary">94%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Confiança</p>
                      <p className="text-sm font-bold text-lia-text-primary">91%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Conhecimento</p>
                      <p className="text-sm font-bold text-lia-text-primary">96%</p>
                    </div>
                    <div className="text-center">
                      <p className={textStyles.bodySmall}>Comunicação</p>
                      <p className="text-sm font-bold text-lia-text-primary">89%</p>
                    </div>
                  </div>

                  {/* Parecer da LIA */}
                  <div className="border-t border-lia-border-subtle pt-3">
                    <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      Parecer da LIA
                    </h5>
                    <div className="space-y-2 text-xs text-lia-text-secondary">
                      <p>
                        <span className="font-semibold text-lia-text-primary">Pontos Fortes:</span> O candidato demonstra excelente articulação e domínio técnico.
                        Experiência sólida em liderança de times mobile, com resultados mensuráveis (redução de 40% no tempo de desenvolvimento).
                      </p>
                      <p>
                        <span className="font-semibold text-lia-text-primary">Pontos de Atenção:</span> Poderia detalhar mais sobre gestão de conflitos e metodologias ágeis.
                        A experiência com React Native é recente (últimos 2 anos).
                      </p>
                      <p>
                        <span className="font-semibold text-lia-text-primary">Recomendação:</span> Candidato altamente recomendado para próxima fase.
                        Sugiro aprofundar sobre arquitetura de apps e experiência com CI/CD mobile.
                      </p>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-lia-border-subtle">
                        <span className={textStyles.bodySmall}>Score Geral</span>
                        <Badge className="text-xs px-2 py-0.5 bg-status-success text-white" >
                          93% - Altamente Recomendado
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Feed de Transcrição - Deepgram */}
              <div className="col-span-1">
                <div className="bg-lia-bg-primary rounded-xl p-3 h-full overflow-y-auto">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-3 sticky top-0 bg-lia-bg-primary pb-2 border-b border-lia-border-subtle">
                    📝 Transcrição
                  </h4>

                  {/* Indicador do tipo de áudio */}
                  <div className="mb-3 p-2 bg-lia-bg-secondary border border-lia-border-subtle rounded-xl">
                    <div className="flex items-center gap-2">
                      <Badge className="text-xs px-1.5 py-0.5 bg-lia-btn-primary-bg text-lia-btn-primary-text border-0">
                        {selectedFile.audioType === 'interview' ? 'Entrevista Gravada' : 'Áudio de Triagem'}
                      </Badge>
                      <span className={textStyles.bodySmall}>Duração: {selectedFile.duration || '4:32'}</span>
                    </div>
                  </div>

                  <div className="space-y-3 text-xs">
                    {/* Transcrição de exemplo */}
                    <div className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={`${textStyles.bodySmall} mb-1`}>
                        0:00 • Candidato
                      </p>
                      <p className="text-lia-text-primary">"Olá, meu nome é Bruno Carvalho Dias e estou muito interessado nessa oportunidade de Tech Lead Mobile. Tenho mais de 8 anos de experiência em desenvolvimento mobile, sendo os últimos 4 anos focado em liderança técnica..."
                      </p>
                    </div>

                    <div className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={`${textStyles.bodySmall} mb-1`}>
                        1:15 • Candidato
                      </p>
                      <p className="text-lia-text-primary">"Trabalhei na Unicorn Startup onde liderei um time de 6 desenvolvedores. Implementamos React Native para unificar as plataformas iOS e Android, reduzindo o tempo de desenvolvimento em 40%..."
                      </p>
                    </div>

                    <div className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={`${textStyles.bodySmall} mb-1`}>
                        2:30 • Candidato
                      </p>
                      <p className="text-lia-text-primary">"Sobre minhas principais conquistas, destaco a migração completa de duas aplicações nativas para React Native, mantendo 99.5% de uptime durante todo o processo..."
                      </p>
                    </div>

                    <div className="border-l-2 border-lia-border-subtle pl-3">
                      <p className={`${textStyles.bodySmall} mb-1`}>
                        3:45 • Candidato
                      </p>
                      <p className="text-lia-text-primary">
                        Estou disponível para início imediato e minha expectativa salarial está na faixa de {CURRENCY_SYMBOL} 25.000 a {CURRENCY_SYMBOL} 30.000, considerando o nível de senioridade e responsabilidades da posição.
                      </p>
                    </div>

                    {/* Highlights identificados pela LIA */}
                    <div className="mt-4 p-2 bg-lia-bg-tertiary rounded-xl">
                      <p className="text-xs font-semibold text-lia-text-primary mb-1">
                        🎯 Highlights da LIA
                      </p>
                      <ul className="space-y-1 text-xs text-lia-text-secondary">
                        <li>• 8+ anos de experiência em mobile</li>
                        <li>• Liderança de time de 6 devs</li>
                        <li>• Redução de 40% no tempo de dev</li>
                        <li>• Disponibilidade imediata</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
