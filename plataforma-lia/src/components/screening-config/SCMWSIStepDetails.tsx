"use client"

import { CheckCircle2, ChevronDown, ChevronUp } from "lucide-react"

interface WSIGenerationContextData {
  title?: string
  seniority?: string
  responsibilities: string[]
  technicalSkills: string[]
  behavioralCompetencies: string[]
  methodologyBreakdown?: Record<string, number>
  blockBreakdown?: Record<number, number>
  companyStandardFound?: boolean
}

interface SCMWSIStepDetailsProps {
  wsiGenerationStep: number
  wsiGenerationContext: WSIGenerationContextData | null
  wsiSummaryTypedText: string
  wsiSummaryTypingDone: boolean
  wsiGeneratedCount: number
  wsiSummaryExpanded: boolean
  setWsiSummaryExpanded: (value: boolean) => void
}

export function SCMWSIStepDetails({
  wsiGenerationStep,
  wsiGenerationContext,
  wsiSummaryTypedText,
  wsiSummaryTypingDone,
  wsiGeneratedCount,
  wsiSummaryExpanded,
  setWsiSummaryExpanded,
}: SCMWSIStepDetailsProps) {
  return (
    <div className="px-5 pb-4 pt-1 space-y-3 border-t border-gray-100 dark:border-gray-700">
      {wsiGenerationStep >= 1 && wsiGenerationContext && (
        <div className="pt-2">
          <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-0.5">Cargo analisado</p>
          <p className="text-xs text-gray-800">
            {wsiGenerationContext.title}{wsiGenerationContext.seniority ? <span className="text-gray-600 dark:text-gray-400"> · {wsiGenerationContext.seniority}</span> : ''}
          </p>
        </div>
      )}

      {wsiGenerationStep >= 2 && wsiGenerationContext && (
        <div className="space-y-2">
          {wsiGenerationContext.responsibilities.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Responsabilidades Chave</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.responsibilities.map((resp: string, i: number) => (
                  <span key={`resp-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">
                    {resp.length > 35 ? resp.slice(0, 35) + '...' : resp}
                  </span>
                ))}
              </div>
            </div>
          )}
          {wsiGenerationContext.technicalSkills.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Competências Técnicas</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.technicalSkills.map((skill: string, i: number) => (
                  <span key={`tech-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">{skill}</span>
                ))}
              </div>
            </div>
          )}
          {wsiGenerationContext.behavioralCompetencies.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Competências Comportamentais</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.behavioralCompetencies.map((comp: string, i: number) => (
                  <span key={`behav-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-full">{comp}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {wsiGenerationStep >= 3 && (
        <div>
          <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1">Metodologias Utilizadas para Gerar Perguntas</p>
          {wsiGenerationStep >= 4 && wsiGenerationContext?.methodologyBreakdown && Object.keys(wsiGenerationContext.methodologyBreakdown).length > 0 ? (
            <p className="text-xs text-gray-700">
              {Object.entries(wsiGenerationContext.methodologyBreakdown)
                .filter(([key]) => key !== 'Dreyfus')
                .map(([method, count]) => {
                  const labels: Record<string, string> = { 'CBI': 'CBI', 'Bloom': 'Bloom', 'BigFive': 'Big Five' }
                  return `${labels[method] || method} (${count as number})`
                }).join(' · ')}
              {wsiGenerationContext.methodologyBreakdown['Dreyfus'] ? ' · Dreyfus (calibração)' : ''}
            </p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {['CBI', 'Bloom', 'Big Five', 'Dreyfus'].map(m => (
                <span key={m} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-full">{m}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {wsiGenerationStep >= 4 && wsiGenerationContext && (
        <div className="space-y-4 pt-1">
          <div>
            <p className="text-base-ui text-gray-800">
              {wsiSummaryTypedText}
              {!wsiSummaryTypingDone && (
                <span className="inline-block w-[2px] h-[14px] bg-gray-900 dark:bg-gray-100 ml-0.5 align-middle animate-pulse" />
              )}
            </p>
          </div>

          {wsiSummaryTypingDone && (<>
            <div className="space-y-1.5 pl-1">
              {(wsiGenerationContext.blockBreakdown?.[2] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                  <p className="text-base-ui text-gray-800">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![2]} perguntas de elegibilidade</span>, para validar aderência mínima ao cargo
                  </p>
                </div>
              )}
              {(wsiGenerationContext.blockBreakdown?.[3] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                  <p className="text-base-ui text-gray-800">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![3]} perguntas técnicas</span>, para investigar o nível de conhecimento e experiência prática
                  </p>
                </div>
              )}
              {(wsiGenerationContext.blockBreakdown?.[4] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                  <p className="text-base-ui text-gray-800">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![4]} perguntas comportamentais</span>, para explorar as competências exigidas para a vaga
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-1">
              <p className="text-base-ui text-gray-800">
                Ao todo, a triagem será composta por <span className="font-semibold">{wsiGeneratedCount} perguntas</span>.
              </p>
              <p className="text-base-ui text-gray-800">
                O tempo médio estimado de triagem é de <span className="font-semibold">15 a 20 minutos</span>, considerando o tempo de leitura e resposta do candidato.
              </p>
            </div>

            {!wsiSummaryExpanded ? (
              <button onClick={() => setWsiSummaryExpanded(true)} className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 transition-colors">
                <ChevronDown className="w-3.5 h-3.5" />
                Ver detalhes completos
              </button>
            ) : (
              <>
                <div>
                  <p className="text-base-ui font-semibold text-gray-900 mb-1">Próximo passo</p>
                  <p className="text-base-ui text-gray-800">Selecione as perguntas em cada um dos blocos abaixo.</p>
                </div>
                <div className="space-y-1.5">
                  <p className="text-base-ui text-gray-800">
                    As perguntas foram geradas com base na metodologia <span className="font-semibold text-gray-900 dark:text-gray-50">WeDoTalent Skill Index</span>, considerando:
                  </p>
                  <div className="space-y-0.5 pl-1">
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Senioridade do cargo</p></div>
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Responsabilidades e competências mapeadas</p></div>
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">•</span><p className="text-base-ui text-gray-700">Metodologias de avaliação (CBI, Bloom, Big Five e Dreyfus)</p></div>
                  </div>
                </div>
                <p className="text-base-ui text-gray-700">
                  As perguntas estão organizadas em ordem de prioridade, mas você pode escolher aquelas que julgar mais adequadas ao contexto da vaga.
                </p>
                <p className="text-base-ui text-gray-800 font-semibold">
                  Caso deseje perguntas adicionais, utilize a opção de adicionar perguntas personalizadas manualmente em cada bloco.
                </p>
                <div className="border-t border-gray-100 pt-3">
                  <p className="text-base-ui font-semibold text-gray-900 mb-1.5">Finalização</p>
                  <p className="text-base-ui text-gray-800 mb-1">Após concluir a seleção das perguntas:</p>
                  <div className="space-y-0.5 pl-1">
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">1.</span><p className="text-base-ui text-gray-700">Salve as alterações</p></div>
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">2.</span><p className="text-base-ui text-gray-700">Inicie o disparo da triagem</p></div>
                    <div className="flex items-start gap-2"><span className="text-gray-400 mt-0.5">3.</span><p className="text-base-ui text-gray-700">A LIA realizará a avaliação inicial e sinalizará os candidatos aprovados para a próxima etapa</p></div>
                  </div>
                </div>
                {wsiGenerationContext.companyStandardFound && (
                  <div className="flex items-center gap-1.5 pt-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
                    <span className="text-xs text-gray-600">Perguntas padrão da empresa incluídas</span>
                  </div>
                )}
                <button onClick={() => setWsiSummaryExpanded(false)} className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 transition-colors pt-1">
                  <ChevronUp className="w-3.5 h-3.5" />
                  Recolher detalhes
                </button>
              </>
            )}
          </>)}
        </div>
      )}
    </div>
  )
}
