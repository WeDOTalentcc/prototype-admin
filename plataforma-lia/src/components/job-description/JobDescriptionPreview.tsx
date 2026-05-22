"use client";

import { formatBRL } from"@/lib/pricing";
import { cn } from"@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card";
import { Separator } from"@/components/ui/separator";
import { 
  Lightbulb, 
  AlertTriangle, 
  Building2, 
  MapPin, 
  Briefcase, 
  Users,
  CheckCircle2,
  Circle
} from"lucide-react";
import {
  JobDescriptionPreviewData,
  Responsibility,
  Competency,
  SECTION_TITLES,
  WORK_MODEL_LABELS,
  CONTRACT_TYPE_LABELS,
} from"./types";

interface JobDescriptionPreviewProps {
  data: JobDescriptionPreviewData;
  onEditResponsibility?: (index: number, resp: Responsibility) => void;
  onRemoveResponsibility?: (index: number) => void;
  onEditCompetency?: (type:"technical" |"behavioral", index: number, comp: Competency) => void;
  onRemoveCompetency?: (type:"technical" |"behavioral", index: number) => void;
  className?: string;
}

function SuggestionBadge({ isNew }: { isNew: boolean }) {
  if (!isNew) return null;
  return (
    <Chip density="relaxed" variant="neutral" className="ml-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-default dark:border-lia-border-default">
      <Lightbulb className="w-3 h-3 mr-1" />
      Sugerido pela LIA
    </Chip>
  );
}

function AlertBadge({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <Chip density="relaxed" variant="warning" className="ml-2">
      <AlertTriangle className="w-3 h-3 mr-1" />
      {message}
    </Chip>
  );
}

function MetadataRow({ data }: { data: JobDescriptionPreviewData }) {
  const workModelLabel = WORK_MODEL_LABELS[data.work_model];
  const workModelDisplay = data.work_model ==="hibrido" && data.office_days_per_week
    ? `${workModelLabel} (${data.office_days_per_week}x/semana)`
    : workModelLabel;

  return (
    <div className="flex flex-wrap gap-3 text-sm text-lia-text-tertiary">
      {data.department && (
        <div className="flex items-center gap-1">
          <Building2 className="w-4 h-4" />
          <span>{data.department}</span>
        </div>
      )}
      {data.seniority && (
        <div className="flex items-center gap-1">
          <Users className="w-4 h-4" />
          <span>{data.seniority}</span>
        </div>
      )}
      <div className="flex items-center gap-1">
        <Briefcase className="w-4 h-4" />
        <span>{CONTRACT_TYPE_LABELS[data.contract_type]}</span>
      </div>
      <div className="flex items-center gap-1">
        <MapPin className="w-4 h-4" />
        <span>{workModelDisplay}</span>
      </div>
      {data.location && (
        <div className="flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          <span>{data.location}</span>
        </div>
      )}
    </div>
  );
}

function CompletenessIndicator({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  const isComplete = percentage >= 80;
  
  return (
    <div className="flex items-center gap-2">
      {isComplete ? (
        <CheckCircle2 className="w-4 h-4 text-status-success" />
      ) : (
        <Circle className="w-4 h-4 text-status-warning" />
      )}
      <span className={cn("text-sm font-medium",
        isComplete ?"text-status-success" :"text-status-warning"
      )}>
        {percentage}% completo
      </span>
    </div>
  );
}

export function JobDescriptionPreview({
  data,
  onEditResponsibility,
  onRemoveResponsibility,
  onEditCompetency,
  onRemoveCompetency,
  className,
}: JobDescriptionPreviewProps) {
  const requiredTech = data.technical_competencies.filter(c => c.level ==="required");
  const niceTech = data.technical_competencies.filter(c => c.level ==="nice_to_have");
  const requiredBeh = data.behavioral_competencies.filter(c => c.level ==="required");

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-2xl font-semibold">
              {data.title}
              {data.num_positions > 1 && (
                <span className="text-lia-text-tertiary ml-2">
                  ({data.num_positions} vagas)
                </span>
              )}
            </CardTitle>
            <MetadataRow data={data} />
          </div>
          <div className="flex flex-col items-end gap-2">
            <CompletenessIndicator score={data.completeness_score} />
            {data.suggestions_count > 0 && (
              <Chip variant="neutral" className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-default dark:border-lia-border-default">
                <Lightbulb className="w-3 h-3 mr-1" />
                {data.suggestions_count} sugestões
              </Chip>
            )}
          </div>
        </div>
        
        {data.is_affirmative && (
          <Chip variant="neutral" muted className="w-fit mt-2  border-wedo-purple/30/30">
            🏳️‍🌈 {data.affirmative_type ||"Vaga Afirmativa"}
          </Chip>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {data.company && (
          <section>
            <h3 className="text-lg font-semibold mb-2">{SECTION_TITLES.about}</h3>
            <p className="text-lia-text-tertiary">{data.company.about ||"[Descrição da empresa]"}</p>
          </section>
        )}

        {data.description && (
          <section>
            <h3 className="text-lg font-semibold mb-2">{SECTION_TITLES.the_role}</h3>
            <p className="text-lia-text-tertiary">{data.description}</p>
          </section>
        )}

        <Separator />

        {data.responsibilities.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.what_you_will_do}</h3>
            <ul className="space-y-2">
              {data.responsibilities.map((resp, index) => (
                <li key={`resp-${index}`} className="flex items-start gap-2">
                  <span className="text-lia-text-secondary mt-1">•</span>
                  <span className="flex-1">
                    {resp.description}
                    <SuggestionBadge isNew={resp.is_new} />
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <Separator />

        <section>
          <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.what_we_are_looking_for}</h3>
          
          {(requiredTech.length > 0 || requiredBeh.length > 0) && (
            <div className="mb-4">
              <h4 className="font-medium text-sm text-lia-text-tertiary mb-2">
                {SECTION_TITLES.required}
              </h4>
              
              {requiredTech.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs uppercase text-lia-text-tertiary mb-1">
                    {SECTION_TITLES.technical}
                  </p>
                  <ul className="space-y-1">
                    {requiredTech.map((comp) => (
                      <li key={comp.name || (comp as unknown as Record<string, unknown>).skill as string || String(comp)} className="flex items-center gap-2">
                        <span className="text-lia-text-secondary">•</span>
                        <span>
                          {comp.name}
                          {comp.years_experience && ` (${comp.years_experience}+ anos)`}
                          <SuggestionBadge isNew={comp.is_new} />
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {requiredBeh.length > 0 && (
                <div>
                  <p className="text-xs uppercase text-lia-text-tertiary mb-1">
                    {SECTION_TITLES.behavioral}
                  </p>
                  <ul className="space-y-1">
                    {requiredBeh.map((comp) => (
                      <li key={comp.name || (comp as unknown as Record<string, unknown>).skill as string || String(comp)} className="flex items-center gap-2">
                        <span className="text-lia-text-secondary">•</span>
                        <span>
                          {comp.name}
                          <SuggestionBadge isNew={comp.is_new} />
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {niceTech.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-lia-text-tertiary mb-2">
                {SECTION_TITLES.nice_to_have}
              </h4>
              <ul className="space-y-1">
                {niceTech.map((comp) => (
                  <li key={comp.name || (comp as unknown as Record<string, unknown>).skill as string || String(comp)} className="flex items-center gap-2">
                    <span className="text-lia-text-secondary">•</span>
                    <span>
                      {comp.name}
                      <SuggestionBadge isNew={comp.is_new} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <Separator />

        {data.company?.evp && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.why_join_us}</h3>
            <div className="space-y-2 text-sm">
              {data.company.evp.impact && (
                <p><strong>Impacto:</strong> {data.company.evp.impact}</p>
              )}
              {data.company.evp.growth && (
                <p><strong>Crescimento:</strong> {data.company.evp.growth}</p>
              )}
              {data.company.evp.team && (
                <p><strong>Time:</strong> {data.company.evp.team}</p>
              )}
              {data.company.evp.flexibility && (
                <p><strong>Flexibilidade:</strong> {data.company.evp.flexibility}</p>
              )}
              {data.company.evp.benefits && (
                <p><strong>Benefícios:</strong> {data.company.evp.benefits}</p>
              )}
            </div>
          </section>
        )}

        {data.compensation && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.compensation}</h3>
            <div className="space-y-2 text-sm">
              {data.compensation.salary_min && data.compensation.salary_max && (
                <p className="flex items-center">
                  <strong>Salário:</strong>
                  <span className="ml-2">
                    {formatBRL(data.compensation.salary_min)} - {formatBRL(data.compensation.salary_max)}
                  </span>
                  {data.compensation.has_alert && (
                    <AlertBadge message={data.compensation.alert_message} />
                  )}
                </p>
              )}
              {data.compensation.market_comparison && (
                <p className="flex items-center gap-2">
                  <strong>Comparativa de Mercado:</strong>
                  <Chip density="relaxed" variant="neutral" className="-dark border-wedo-cyan/30/30">
                    {data.compensation.market_comparison}
                  </Chip>
                </p>
              )}
              {data.compensation.market_percentile !== undefined && (
                <p>
                  <strong>Percentil de Mercado:</strong> {data.compensation.market_percentile}%
                </p>
              )}
              {data.compensation.bonus_percentage && (
                <p><strong>Bônus:</strong> {data.compensation.bonus_percentage}% anual</p>
              )}
              {data.compensation.benefits.length > 0 && (
                <p>
                  <strong>Benefícios:</strong>{""}
                  {data.compensation.benefits.map(b => b.name).join(",")}
                </p>
              )}
            </div>
          </section>
        )}

        {data.company?.values && data.company.values.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.our_values}</h3>
            <ul className="space-y-1 text-sm">
              {data.company.values.map((value) => (
                <li key={value.name}>
                  <strong>{value.name}:</strong> {value.description}
                </li>
              ))}
            </ul>
          </section>
        )}

        {data.company?.diversity_statement && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.diversity}</h3>
            <p className="text-sm text-lia-text-tertiary">{data.company.diversity_statement}</p>
          </section>
        )}

        <Separator />

        <div className="text-xs text-lia-text-tertiary flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Lightbulb className="w-3 h-3 text-lia-text-secondary" />
            = Sugerido pela LIA
          </span>
          <span className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-status-warning" />
            = Alerta
          </span>
          <span>✏️ = Editado</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default JobDescriptionPreview;
