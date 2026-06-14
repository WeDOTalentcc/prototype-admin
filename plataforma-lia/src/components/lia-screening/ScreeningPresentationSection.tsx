"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Building, Briefcase, Users, TrendingUp, Star, Heart,
  MapPin, Globe, Award, DollarSign, MessageSquare, CheckCircle, Copy
} from "lucide-react"

interface JobPresentation {
  company: string
  role: string
  team: string
  growth: string
  benefits: string[]
}

interface ScreeningPresentationSectionProps {
  jobPresentation: JobPresentation
  jobTitle: string
  jobLocation: string
  jobWorkModel: string
  jobLevel: string
  jobSalary: string
  copiedSection: string | null
  onCopy: (text: string, section: string) => void
}

export function ScreeningPresentationSection({
  jobPresentation, jobTitle, jobLocation, jobWorkModel, jobLevel, jobSalary,
  copiedSection, onCopy
}: ScreeningPresentationSectionProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-semibold text-lia-text-primary">Apresentação da Vaga e Empresa</h4>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onCopy(
            `${jobPresentation.company}\n\n${jobPresentation.role}\n\n${jobPresentation.team}\n\n${jobPresentation.growth}`,
            'presentation'
          )}
          className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
        >
          <Copy className="w-3 h-3" />
          {copiedSection === 'presentation' ? 'Copiado!' : 'Copiar Apresentação'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Building className="w-4 h-4 text-lia-text-secondary" />
              Sobre a Empresa
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-lia-text-secondary leading-relaxed">
              {jobPresentation.company}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-status-success" />
              Sobre a Vaga
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-lia-text-secondary leading-relaxed">
              {jobPresentation.role}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Users className="w-4 h-4 text-wedo-purple" />
              Sobre o Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-lia-text-secondary leading-relaxed">
              {jobPresentation.team}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-wedo-orange" />
              Crescimento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-lia-text-secondary leading-relaxed">
              {jobPresentation.growth}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Star className="w-4 h-4 text-status-warning" />
            Detalhes da Posição
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
              <MapPin className="w-5 h-5 text-lia-text-secondary mx-auto mb-1" />
              <div className="text-sm font-medium text-lia-text-secondary">Local</div>
              <div className="text-xs text-lia-text-secondary">{jobLocation}</div>
            </div>
            <div className="text-center p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
              <Globe className="w-5 h-5 text-status-success mx-auto mb-1" />
              <div className="text-sm font-medium text-status-success dark:text-status-success">Modalidade</div>
              <div className="text-xs text-status-success dark:text-status-success">{jobWorkModel}</div>
            </div>
            <div className="text-center p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
              <Award className="w-5 h-5 text-wedo-purple mx-auto mb-1" />
              <div className="text-sm font-medium text-wedo-purple-text dark:text-wedo-purple">Nível</div>
              <div className="text-xs text-wedo-purple-text dark:text-wedo-purple">{jobLevel}</div>
            </div>
            <div className="text-center p-3 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-md">
              <DollarSign className="w-5 h-5 text-wedo-orange mx-auto mb-1" />
              <div className="text-sm font-medium text-wedo-orange-text dark:text-wedo-orange">Salário</div>
              <div className="text-xs text-wedo-orange-text dark:text-wedo-orange">{jobSalary}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Heart className="w-4 h-4 text-wedo-magenta" />
            Benefícios e Vantagens
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {jobPresentation.benefits.map((benefit: string) => (
              <div key={benefit} className="flex items-center gap-2 p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="text-sm text-lia-text-primary">{benefit}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-status-success" />
            Script de Apresentação
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCopy(
              `Deixe eu te contar um pouco sobre nós e sobre esta oportunidade.\n\n${jobPresentation.company}\n\nPara esta posição de ${jobTitle}, ${jobPresentation.role}\n\n${jobPresentation.team}\n\n${jobPresentation.growth}\n\nO que mais te chama atenção nesta oportunidade?`,
              'presentation-script'
            )}
            className="gap-2"
          >
            <Copy className="w-3 h-3" />
            {copiedSection === 'presentation-script' ? 'Copiado!' : 'Copiar'}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default">
            <p className="text-sm text-lia-text-primary leading-relaxed">
              "Deixe eu te contar um pouco sobre nós e sobre esta oportunidade.
              <br /><br />
              <strong>{jobPresentation.company}</strong>
              <br /><br />
              Para esta posição de <strong>{jobTitle}</strong>, {jobPresentation.role}
              <br /><br />
              <strong>{jobPresentation.team}</strong>
              <br /><br />
              <strong>{jobPresentation.growth}</strong>
              <br /><br />
              O que mais te chama atenção nesta oportunidade?"
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
