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
    <div className="px-5 pb-4 pt-1 space-y-3 border-t border-lia-border-subtle">
      {wsiGenerationStep >= 1 && wsiGenerationContext && (
        <div className="pt-2">
          <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-0.5">Cargo analisado</p>
          <p className="text-xs text-lia-text-primary">
            {wsiGenerationContext.title}{wsiGenerationContext.seniority ? <span className="text-lia-text-secondary"> · {wsiGenerationContext.seniority}</span> : ''}
          </p>
        </div>
      )}

      {wsiGenerationStep >= 2 && wsiGenerationContext && (
        <div className="space-y-2">
          {wsiGenerationContext.responsibilities.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Responsabilidades Chave</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.responsibilities.map((resp: string, i: number) => (
                  <span key={`resp-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">
                    {resp.length > 35 ? resp.slice(0, 35) + '...' : resp}
                  </span>
                ))}
              </div>
            </div>
          )}
          {wsiGenerationContext.technicalSkills.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Competências Técnicas</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.technicalSkills.map((skill: string, i: number) => (
                  <span key={`tech-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{skill}</span>
                ))}
              </div>
            </div>
          )}
          {wsiGenerationContext.behavioralCompetencies.length > 0 && (
            <div>
              <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-1">Competências Comportamentais</p>
              <div className="flex flex-wrap gap-1">
                {wsiGenerationContext.behavioralCompetencies.map((comp: string, i: number) => (
                  <span key={`behav-${i}`} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{comp}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {wsiGenerationStep >= 3 && (
        <div>
          <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider mb-1">Metodologias Utilizadas para Gerar Perguntas</p>
          {wsiGenerationStep >= 4 && wsiGenerationContext?.methodologyBreakdown && Object.keys(wsiGenerationContext.methodologyBreakdown).length > 0 ? (
            <p className="text-xs text-lia-text-secondary">
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
                <span key={m} className="inline-flex px-2.5 py-0.5 text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle rounded-full">{m}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {wsiGenerationStep >= 4 && wsiGenerationContext && (
        <div className="space-y-4 pt-1">
          <div>
            <p className="text-base-ui text-lia-text-primary">
              {wsiSummaryTypedText}
              {!wsiSummaryTypingDone && (
                <span className="inline-block w-[2px] h-[14px] bg-lia-btn-primary-bg ml-0.5 align-middle animate-pulse motion-reduce:animate-none" />
              )}
            </p>
          </div>

          {wsiSummaryTypingDone && (<>
            <div className="space-y-1.5 pl-1">
              {(wsiGenerationContext.blockBreakdown?.[2] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-lia-text-disabled mt-0.5">•</span>
                  <p className="text-base-ui text-lia-text-primary">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![2]} perguntas de elegibilidade</span>, para validar aderência mínima ao cargo
                  </p>
                </div>
              )}
              {(wsiGenerationContext.blockBreakdown?.[3] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-lia-text-disabled mt-0.5">•</span>
                  <p className="text-base-ui text-lia-text-primary">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![3]} perguntas técnicas</span>, para investigar o nível de conhecimento e experiência prática
                  </p>
                </div>
              )}
              {(wsiGenerationContext.blockBreakdown?.[4] || 0) > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-lia-text-disabled mt-0.5">•</span>
                  <p className="text-base-ui text-lia-text-primary">
                    <span className="font-semibold">{wsiGenerationContext.blockBreakdown![4]} perguntas comportamentais</span>, para explorar as competências exigidas para a vaga
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-1">
              <p className="text-base-ui text-lia-text-primary">
                Ao todo, a triagem será composta por <span className="font-semibold">{wsiGeneratedCount} perguntas</span>.
              </p>
              <p className="text-base-ui text-lia-text-primary">
                O tempo médio estimado de triagem é de <span className="font-semibold">15 a 20 minutos</span>, considerando o tempo de leitura e resposta do candidato.
              </p>
            </div>

            {!wsiSummaryExpanded ? (
              <button onClick={() => setWsiSummaryExpanded(true)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none">
                <ChevronDown className="w-3.5 h-3.5" />
                Ver detalhes completos
              </button>
            ) : (
              <>
                <div>
                  <p className="text-base-ui font-semibold text-lia-text-primary mb-1">Próximo passo</p>
                  <p className="text-base-ui text-lia-text-primary">Selecione as perguntas em cada um dos blocos abaixo.</p>
                </div>
                <div className="space-y-1.5">
                  <p className="text-base-ui text-lia-text-primary">
                    As perguntas foram geradas com base na metodologia <span className="font-semibold text-lia-text-primary">WeDoTalent Skill Index</span>, considerando:
                  </p>
                  <div className="space-y-0.5 pl-1">
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Senioridade do cargo</p></div>
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Responsabilidades e competências mapeadas</p></div>
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">•</span><p className="text-base-ui text-lia-text-secondary">Metodologias de avaliação (CBI, Bloom, Big Five e Dreyfus)</p></div>
                  </div>
                </div>
                <p className="text-base-ui text-lia-text-secondary">
                  As perguntas estão organizadas em ordem de prioridade, mas você pode escolher aquelas que julgar mais adequadas ao contexto da vaga.
                </p>
                <p className="text-base-ui text-lia-text-primary font-semibold">
                  Caso deseje perguntas adicionais, utilize a opção de adicionar perguntas personalizadas manualmente em cada bloco.
                </p>
                <div className="border-t border-lia-border-subtle pt-3">
                  <p className="text-base-ui font-semibold text-lia-text-primary mb-1.5">Finalização</p>
                  <p className="text-base-ui text-lia-text-primary mb-1">Após concluir a seleção das perguntas:</p>
                  <div className="space-y-0.5 pl-1">
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">1.</span><p className="text-base-ui text-lia-text-secondary">Salve as alterações</p></div>
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">2.</span><p className="text-base-ui text-lia-text-secondary">Inicie o disparo da triagem</p></div>
                    <div className="flex items-start gap-2"><span className="lia-text-secondary mt-0.5">3.</span><p className="text-base-ui text-lia-text-secondary">A LIA realizará a avaliação inicial e sinalizará os candidatos aprovados para a próxima etapa</p></div>
                  </div>
                </div>
                {wsiGenerationContext.companyStandardFound && (
                  <div className="flex items-center gap-1.5 pt-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                    <span className="text-xs text-lia-text-secondary">Perguntas padrão da empresa incluídas</span>
                  </div>
                )}
                <button onClick={() => setWsiSummaryExpanded(false)} className="flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none pt-1">
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
