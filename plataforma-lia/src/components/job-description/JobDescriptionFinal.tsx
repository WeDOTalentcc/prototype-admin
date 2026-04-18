"use client";

import { formatBRL } from"@/lib/pricing";
import { cn } from"@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card";
import { Separator } from"@/components/ui/separator";
import { Button } from"@/components/ui/button";
import { 
  Building2, 
  MapPin, 
  Briefcase, 
  Users,
  Clock,
  Mail,
  ExternalLink,
  Copy,
  Download
} from"lucide-react";
import {
  JobDescriptionFinalData,
  SECTION_TITLES,
  WORK_MODEL_LABELS,
  CONTRACT_TYPE_LABELS,
} from"./types";

interface JobDescriptionFinalProps {
  data: JobDescriptionFinalData;
  onCopyMarkdown?: () => void;
  onDownloadPDF?: () => void;
  onPublish?: () => void;
  showActions?: boolean;
  className?: string;
}

function MetadataRow({ data }: { data: JobDescriptionFinalData }) {
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

export function JobDescriptionFinal({
  data,
  onCopyMarkdown,
  onDownloadPDF,
  onPublish,
  showActions = true,
  className,
}: JobDescriptionFinalProps) {
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
          
          {showActions && (
            <div className="flex gap-2">
              {onCopyMarkdown && (
                <Button variant="outline" size="sm" onClick={onCopyMarkdown}>
                  <Copy className="w-4 h-4 mr-1" />
                  Copiar
                </Button>
              )}
              {onDownloadPDF && (
                <Button variant="outline" size="sm" onClick={onDownloadPDF}>
                  <Download className="w-4 h-4 mr-1" />
                  PDF
                </Button>
              )}
              {onPublish && (
                <Button size="sm" onClick={onPublish}>
                  <ExternalLink className="w-4 h-4 mr-1" />
                  Publicar
                </Button>
              )}
            </div>
          )}
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
                  <span>{resp}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        <Separator />

        <section>
          <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.what_we_are_looking_for}</h3>
          
          {(data.required_technical.length > 0 || data.required_behavioral.length > 0) && (
            <div className="mb-4">
              <h4 className="font-medium text-sm text-lia-text-tertiary mb-2">
                {SECTION_TITLES.required}
              </h4>
              <ul className="space-y-1">
                {data.required_technical.map((skill, index) => (
                  <li key={`tech-${index}`} className="flex items-center gap-2">
                    <span className="text-lia-text-secondary">•</span>
                    <span>{skill}</span>
                  </li>
                ))}
                {data.required_behavioral.map((skill, index) => (
                  <li key={`beh-${index}`} className="flex items-center gap-2">
                    <span className="text-lia-text-secondary">•</span>
                    <span>{skill}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.nice_to_have.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-lia-text-tertiary mb-2">
                {SECTION_TITLES.nice_to_have}
              </h4>
              <ul className="space-y-1">
                {data.nice_to_have.map((skill, index) => (
                  <li key={skill} className="flex items-center gap-2">
                    <span className="text-lia-text-secondary">•</span>
                    <span>{skill}</span>
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
              {data.compensation.salary_min && data.compensation.salary_max && data.compensation.show_salary && (
                <p>
                  <strong>Salário:</strong>{""}
                  {formatBRL(data.compensation.salary_min)} - {formatBRL(data.compensation.salary_max)}
                </p>
              )}
              {data.compensation.bonus_percentage && (
                <p><strong>Bônus:</strong> {data.compensation.bonus_percentage}% anual</p>
              )}
              {data.compensation.plr && (
                <p><strong>PLR:</strong> {data.compensation.plr}</p>
              )}
              {data.compensation.equity && (
                <p><strong>Equity:</strong> {data.compensation.equity}</p>
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
              {data.company.values.map((value, index) => (
                <li key={value.name}>
                  <strong>{value.name}:</strong> {value.description}
                </li>
              ))}
            </ul>
          </section>
        )}

        <Separator />

        {data.interview_process.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.interview_process}</h3>
            <ol className="space-y-3">
              {data.interview_process.map((stage) => (
                <li key={stage.order} className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary flex items-center justify-center text-sm font-medium">
                    {stage.order}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <strong>{stage.name}</strong>
                      {stage.format && stage.duration && (
                        <span className="text-xs text-lia-text-tertiary">
                          ({stage.format}, {stage.duration})
                        </span>
                      )}
                    </div>
                    {stage.description && (
                      <p className="text-sm text-lia-text-tertiary mt-1">{stage.description}</p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
            {data.total_timeline && (
              <div className="mt-4 flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-lia-text-secondary" />
                <strong>Timeline total:</strong> {data.total_timeline}
              </div>
            )}
          </section>
        )}

        {data.company?.diversity_statement && (
          <section>
            <h3 className="text-lg font-semibold mb-3">{SECTION_TITLES.diversity}</h3>
            <p className="text-sm text-lia-text-tertiary">{data.company.diversity_statement}</p>
          </section>
        )}

        <Separator />

        <footer className="space-y-2">
          {data.apply_url && (
            <div className="flex items-center gap-2 text-sm">
              <span>📩</span>
              <strong>Candidate-se em:</strong>
              <a 
                href={data.apply_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-lia-text-primary hover:underline"
              >
                {data.apply_url}
              </a>
            </div>
          )}
          {data.contact_email && (
            <div className="flex items-center gap-2 text-sm">
              <Mail className="w-4 h-4" />
              <strong>Dúvidas?</strong>
              <a 
                href={`mailto:${data.contact_email}`}
                className="text-lia-text-primary hover:underline"
              >
                {data.contact_email}
              </a>
            </div>
          )}
        </footer>
      </CardContent>
    </Card>
  );
}

export default JobDescriptionFinal;
