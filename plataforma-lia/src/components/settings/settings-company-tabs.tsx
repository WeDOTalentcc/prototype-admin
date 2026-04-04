"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Building, Globe, MessageSquare, Target, Network,
  Upload, FileText, Heart, Edit, Trash2, Plus
} from "lucide-react"
import {
  BasicDataSection,
  AddressSection,
  SocialMediaSection,
  SegmentSection,
  BranchesSection
} from "./institutional-tab-sections"

export interface SettingsCompanyTabProps {
  onSettingsChange: (changed: boolean) => void
}

type InstitutionalSubTab = 'basic' | 'address' | 'social' | 'segment' | 'branches'

const subTabs = [
  { id: 'basic' as const, name: 'Dados Básicos', icon: Building },
  { id: 'address' as const, name: 'Endereço', icon: Globe },
  { id: 'social' as const, name: 'Redes Sociais', icon: MessageSquare },
  { id: 'segment' as const, name: 'Segmento', icon: Target },
  { id: 'branches' as const, name: 'Filiais', icon: Network }
]

export function InstitutionalTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<InstitutionalSubTab>('basic')

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors motion-reduce:transition-none font-crimson ${
                  activeSubTab === tab.id
 ? 'bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary'
                    : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover text-lia-text-primary'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {activeSubTab === 'basic' && <BasicDataSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'address' && <AddressSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'social' && <SocialMediaSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'segment' && <SegmentSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'branches' && <BranchesSection />}
    </div>
  )
}

export function CultureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Heart className="w-4 h-4" />
            Identidade Corporativa
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              Missão
            </label>
            <textarea
              rows={3}
              defaultValue="Melhorar a qualidade de vida diária de todos os que servimos por meio de serviços de alimentação e facilities únicos e inovadores."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              Visão
            </label>
            <textarea
              rows={3}
              defaultValue="Ser a empresa líder mundial em serviços de qualidade de vida, criando valor para todas as partes interessadas."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              Propósito Institucional
            </label>
            <textarea
              rows={3}
              defaultValue="Conectar pessoas, lugares e experiências para criar um mundo melhor através de serviços essenciais que melhoram a vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Valores da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {[
              { value: 'Espírito de Serviço', description: 'Nos concentramos nas necessidades das pessoas que servimos' },
              { value: 'Espírito de Equipe', description: 'Construímos relacionamentos duradouros baseados na confiança' },
              { value: 'Espírito de Progresso', description: 'Inovamos e nos adaptamos para um mundo em mudança' },
              { value: 'Sustentabilidade', description: 'Comprometidos com um planeta mais sustentável' }
            ].map((item) => (
              <div key={item.value} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-lia-text-primary">
                    {item.value}
                  </h4>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <p className="text-xs text-lia-text-primary">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <Button variant="outline" className="gap-2" size="sm">
            <Plus className="w-4 h-4" />
            Adicionar Valor
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export function StructureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Network className="w-4 h-4" />
            Upload de Organograma
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-8 text-center bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <Upload className="w-12 h-12 mx-auto mb-4 text-lia-text-primary" />
            <h4 className="text-sm font-medium text-lia-text-primary mb-2">
              Faça upload do organograma da empresa
            </h4>
            <p className="text-sm text-lia-text-primary mb-4">
              Formatos aceitos: PNG, JPG, PDF, SVG até 10MB
            </p>
            <Button variant="outline">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Estrutura de Cargos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-6 text-center mb-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <FileText className="w-8 h-8 mx-auto mb-2 text-lia-text-primary" />
            <p className="text-sm text-lia-text-primary mb-2">
              Upload da planilha de cargos e descrições
            </p>
            <p className="text-xs text-lia-text-primary mb-3">Excel (.xlsx, .xls) ou CSV até 5MB</p>
            <Button variant="outline" size="sm">
              Upload de Cargos
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
