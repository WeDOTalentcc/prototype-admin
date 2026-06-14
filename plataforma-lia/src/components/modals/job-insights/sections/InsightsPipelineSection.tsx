"use client"

import {
  Brain,
  GitBranch,
  CalendarCheck,
  PhoneCall,
  MessageCircleX,
  Calendar,
  MapPin,
  Building2,
  UserCircle,
  Award,
  Clock,
  Lightbulb,
  Users,
} from "lucide-react"
import type { JobInsightData } from "../job-insights.types"

interface LiaFunnelMetrics {
  pipeline_lia: number
  triagens_agendadas: number
  triagens_realizadas: number
  sem_resposta: number
  entrevistas_agendadas: number
  isEstimated: boolean
}

interface DemographicDistribution {
  name: string
  count: number
  percentage: number
}

interface DemographicData {
  cities: DemographicDistribution[]
  workModels: DemographicDistribution[]
  genders: DemographicDistribution[]
  ageRanges: DemographicDistribution[]
  educationLevels: DemographicDistribution[]
  experienceYears: DemographicDistribution[]
}

interface InsightsPipelineSectionProps {
  jobs: JobInsightData[]
  liaFunnelMetrics: LiaFunnelMetrics
  demographicData: DemographicData
}

function DemoCard({
  icon: Icon,
  title,
  items,
}: {
  icon: React.ElementType
  title: string
  items: DemographicDistribution[]
}) {
  return (
    <div data-testid="insights-pipeline-section" className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 text-lia-text-tertiary" />
        {title}
      </h3>
      <div className="space-y-2">
        {items.length > 0 ? (
          items.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <span className="text-xs text-lia-text-secondary">{item.name}</span>
              <div className="flex items-center gap-2">
                <div className="w-16 h-2 bg-lia-interactive-active rounded-full overflow-hidden">
                  <div className="h-full bg-lia-btn-primary-bg" style={{ width: `${item.percentage}%` }} />
                </div>
                <span className="text-xs text-lia-text-secondary w-8 text-right">{item.count}</span>
              </div>
            </div>
          ))
        ) : (
          <p className="text-xs text-lia-text-tertiary italic">Dados não disponíveis</p>
        )}
      </div>
    </div>
  )
}

export function InsightsPipelineSection({
  jobs,
  liaFunnelMetrics,
  demographicData,
}: InsightsPipelineSectionProps) {
  const hasDemographics =
    demographicData.cities.length > 0 ||
    demographicData.workModels.length > 0 ||
    demographicData.genders.length > 0 ||
    demographicData.ageRanges.length > 0 ||
    demographicData.educationLevels.length > 0 ||
    demographicData.experienceYears.length > 0

  return (
    <div className="space-y-4">
      {/* ── Funil de Triagem IA ────────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Funil de Triagem IA
          {liaFunnelMetrics.isEstimated && (
            <span className="text-xs text-lia-text-muted font-normal ml-1">(estimativa)</span>
          )}
        </h3>
        <div className="grid grid-cols-5 gap-3">
          {[
            { Icon: GitBranch, label: "Funil LIA", value: liaFunnelMetrics.pipeline_lia, color: "text-lia-text-primary" },
            { Icon: CalendarCheck, label: "Triagens Agendadas", value: liaFunnelMetrics.triagens_agendadas, color: "text-lia-text-primary" },
            { Icon: PhoneCall, label: "Triagens Realizadas", value: liaFunnelMetrics.triagens_realizadas, color: "text-status-success" },
            { Icon: MessageCircleX, label: "Sem Resposta", value: liaFunnelMetrics.sem_resposta, color: "text-lia-text-secondary" },
            { Icon: Calendar, label: "Entrevistas Agendadas", value: liaFunnelMetrics.entrevistas_agendadas, color: "text-lia-text-primary" },
          ].map(({ Icon, label, value, color }) => (
            <div key={label} className="bg-lia-bg-primary rounded-xl p-3 border border-lia-border-subtle">
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className={`w-3.5 h-3.5 ${color === "text-status-success" ? "text-status-success" : "text-lia-text-tertiary"}`} />
                <span className="text-xs text-lia-text-secondary">{label}</span>
              </div>
              <p className={`text-xl font-semibold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Demographics ────────────────────────────────────────────────── */}
      {hasDemographics ? (
        <div className="grid grid-cols-3 gap-4">
          <DemoCard icon={MapPin} title="Por Cidade" items={demographicData.cities} />
          <DemoCard icon={Building2} title="Por Modelo de Trabalho" items={demographicData.workModels} />
          <DemoCard icon={UserCircle} title="Por Gênero" items={demographicData.genders} />
          {demographicData.ageRanges.length > 0 && (
            <DemoCard icon={Calendar} title="Por Faixa Etária" items={demographicData.ageRanges} />
          )}
          {demographicData.educationLevels.length > 0 && (
            <DemoCard icon={Award} title="Por Escolaridade" items={demographicData.educationLevels} />
          )}
          {demographicData.experienceYears.length > 0 && (
            <DemoCard icon={Clock} title="Por Anos de Experiência" items={demographicData.experienceYears} />
          )}
        </div>
      ) : (
        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Dados Demográficos
          </h3>
          <p className="text-xs text-lia-text-tertiary italic">
            Dados demográficos não disponíveis para as vagas selecionadas.
          </p>
        </div>
      )}

      {/* ── Competências Requeridas ─────────────────────────────────────── */}
      {jobs.some((job) => job.behavioral_competencies && job.behavioral_competencies.length > 0) && (
        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Competências Requeridas
          </h3>
          <div className="space-y-3 max-h-44 overflow-y-auto">
            {jobs
              .filter((job) => job.behavioral_competencies && job.behavioral_competencies.length > 0)
              .map((job) => (
                <div key={job.id} className="bg-lia-bg-primary rounded-xl p-2.5 border border-lia-border-subtle">
                  <span className="text-xs font-medium text-lia-text-tertiary">{job.title}</span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {job.behavioral_competencies?.map((comp, i) => (
                      <span key={i} className="text-micro px-2 py-0.5 rounded-full bg-wedo-purple/15 text-wedo-purple-text">
                        {comp.competency}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── Benefícios Oferecidos ───────────────────────────────────────── */}
      {jobs.some((job) => job.benefits && job.benefits.length > 0) && (
        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Benefícios Oferecidos
          </h3>
          <div className="space-y-3 max-h-44 overflow-y-auto">
            {jobs
              .filter((job) => job.benefits && job.benefits.length > 0)
              .map((job) => (
                <div key={job.id} className="bg-lia-bg-primary rounded-xl p-2.5 border border-lia-border-subtle">
                  <span className="text-xs font-medium text-lia-text-tertiary">{job.title}</span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {job.benefits?.map((benefit, i) => (
                      <span key={i} className="text-micro px-2 py-0.5 rounded-full bg-status-success/15 text-status-success">
                        {benefit}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
