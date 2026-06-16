"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { X, Brain, Download, Share2, FileText } from"lucide-react"
import { useScreeningGuide } from"./lia-screening/useScreeningGuide"
import { ScreeningOverviewSection } from"./lia-screening/ScreeningOverviewSection"
import { ScreeningApproachSection } from"./lia-screening/ScreeningApproachSection"
import { ScreeningQuestionsSection } from"./lia-screening/ScreeningQuestionsSection"
import { ScreeningPresentationSection } from"./lia-screening/ScreeningPresentationSection"
import { ScreeningFeedbackSection } from"./lia-screening/ScreeningFeedbackSection"
import { ScreeningTimelineSection } from"./lia-screening/ScreeningTimelineSection"

interface LiaScreeningGuideProps {
  isOpen: boolean
  onClose: () => void
  job: Record<string, unknown>
  candidate?: Record<string, unknown>
}

export function LiaScreeningGuide({ isOpen, onClose, job, candidate }: LiaScreeningGuideProps) {
  const {
    activeSection,
    setActiveSection,
    copiedSection,
    copyToClipboard,
    j,
    c,
    sections,
    screeningQuestions,
    approachStrategy,
    jobPresentation,
    feedbackStrategy,
  } = useScreeningGuide(job, candidate)

  if (!isOpen || !job) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl w-full max-w-6xl max-h-[95vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 bg-status-success/10 dark:bg-status-success/20">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-status-success/15 dark:bg-status-success/20 rounded-md flex items-center justify-center">
              <Brain className="w-6 h-6 text-wedo-cyan" />
            </div>
            <div>
              <h3 className="text-xl font-semibold font-sans text-lia-text-primary flex items-center gap-2">
                <Brain className="w-5 h-5 text-status-success" />
                Roteiro de Triagem
              </h3>
              <p className="text-sm text-lia-text-primary">
                Guia completo para triagem da vaga: {j.str('title')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              Exportar PDF
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Share2 className="w-4 h-4" />
              Compartilhar
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex">
          <div className="w-64 bg-lia-bg-primary dark:bg-lia-bg-secondary p-4">
            <div className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-md text-left transition-colors motion-reduce:transition-none ${
                    activeSection === section.id
                      ? 'bg-status-success/15 dark:bg-status-success/20 text-status-success dark:text-status-success'
                      : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse text-lia-text-primary'
                  }`}
                >
                  <section.icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{section.label}</span>
                </button>
              ))}
            </div>

            <div className="mt-6 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <h4 className="text-sm font-medium font-sans text-lia-text-primary mb-2">Informações da Vaga</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-lia-text-primary">Nível:</span>
                  <Chip variant="neutral">{j.str('level')}</Chip>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-lia-text-primary">Modalidade:</span>
                  <Chip variant="neutral">{j.str('workModel')}</Chip>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-lia-text-primary">Urgência:</span>
                  <div className="flex items-center gap-1">
                    {Array.from({length: 5}).map((_, i) => (
                      <div key={i} className={`w-2 h-2 rounded-full ${
                        i < (j.num('urgencyLevel', 3)) ? 'bg-status-error' : 'bg-lia-border-default'
                      }`} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 p-6">
            {activeSection === 'overview' && (
              <ScreeningOverviewSection requirements={j.arr<string>('requirements')} />
            )}

            {activeSection === 'approach' && (
              <ScreeningApproachSection
                approachStrategy={approachStrategy}
                candidateName={c?.str('name') || '[Nome]'}
                jobTitle={j.str('title')}
                copiedSection={copiedSection}
                onCopy={copyToClipboard}
              />
            )}

            {activeSection === 'questions' && (
              <ScreeningQuestionsSection
                screeningQuestions={screeningQuestions}
                copiedSection={copiedSection}
                onCopy={copyToClipboard}
              />
            )}

            {activeSection === 'presentation' && (
              <ScreeningPresentationSection
                jobPresentation={jobPresentation}
                jobTitle={j.str('title')}
                jobLocation={j.str('location')}
                jobWorkModel={j.str('workModel')}
                jobLevel={j.str('level')}
                jobSalary={j.str('salary')}
                copiedSection={copiedSection}
                onCopy={copyToClipboard}
              />
            )}

            {activeSection === 'feedback' && (
              <ScreeningFeedbackSection
                feedbackStrategy={feedbackStrategy}
                copiedSection={copiedSection}
                onCopy={copyToClipboard}
              />
            )}

            {activeSection === 'timeline' && (
              <ScreeningTimelineSection />
            )}
          </div>
        </div>

        <div className="p-6 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Chip variant="neutral" >
                Roteiro Personalizado para {j.str('title')}
              </Chip>
              <Chip density="relaxed" variant="neutral" >
                Gerado pela IA
              </Chip>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <FileText className="w-4 h-4" />
                Salvar Roteiro
              </Button>
              <Button className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Iniciar Triagem
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
