"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { 
  Target, Eye, Heart, Brain, Plus, X, 
  CheckCircle2, Save, RotateCcw, Pencil, 
  Lightbulb, Users, Compass, Award, HelpCircle,
  Building2, MapPin, Calendar, Briefcase, TrendingUp, Leaf, Code, Globe
} from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { BigFiveRadar } from "./BigFiveRadar"
import { textStyles } from "@/lib/design-tokens"

export interface CultureProfile {
  id?: string
  company_id?: string
  mission: string | null
  vision: string | null
  values: string[]
  evp_bullets: string[]
  core_competencies: string[]
  culture_description?: string | null
  openness_score: number
  conscientiousness_score: number
  extraversion_score: number
  agreeableness_score: number
  stability_score: number
  website_url?: string
  linkedin_url?: string
  analyzed_pages?: string[]
  last_analysis_at?: string
  confidence_score?: number
  source?: string
  industry?: string
  employee_count?: number
  company_size?: string
  headquarters?: string
  locations?: string[]
  founded_year?: number
  work_model?: string
  growth_opportunities?: string
  team_dynamics?: string
  leadership_style?: string
  dei_initiatives?: string
  sustainability?: string
  social_impact?: string
  tech_stack?: string[]
  engineering_culture?: string
}

interface CultureProfilePreviewProps {
  profile: CultureProfile
  onAccept: (profile: CultureProfile) => void
  onSaveAdjustments: (profile: CultureProfile) => void
  onReanalyze: () => void
  isLoading?: boolean
}

export function CultureProfilePreview({
  profile,
  onAccept,
  onSaveAdjustments,
  onReanalyze,
  isLoading = false
}: CultureProfilePreviewProps) {
  const [editedProfile, setEditedProfile] = useState<CultureProfile>(profile)
  const [isEditing, setIsEditing] = useState(false)
  const [newValue, setNewValue] = useState("")
  const [newEvp, setNewEvp] = useState("")
  const [newCompetency, setNewCompetency] = useState("")
  const [acceptedAll, setAcceptedAll] = useState(false)

  useEffect(() => {
    setEditedProfile({
      ...profile,
      core_competencies: profile.core_competencies || []
    })
  }, [profile])

  const hasChanges = JSON.stringify(profile) !== JSON.stringify(editedProfile)

  const updateField = <K extends keyof CultureProfile>(field: K, value: CultureProfile[K]) => {
    setEditedProfile(prev => ({ ...prev, [field]: value }))
  }

  const addValue = () => {
    if (newValue.trim()) {
      updateField("values", [...editedProfile.values, newValue.trim()])
      setNewValue("")
    }
  }

  const removeValue = (index: number) => {
    updateField("values", editedProfile.values.filter((_, i) => i !== index))
  }

  const addEvp = () => {
    if (newEvp.trim()) {
      updateField("evp_bullets", [...editedProfile.evp_bullets, newEvp.trim()])
      setNewEvp("")
    }
  }

  const removeEvp = (index: number) => {
    updateField("evp_bullets", editedProfile.evp_bullets.filter((_, i) => i !== index))
  }

  const addCompetency = () => {
    if (newCompetency.trim()) {
      updateField("core_competencies", [...(editedProfile.core_competencies || []), newCompetency.trim()])
      setNewCompetency("")
    }
  }

  const removeCompetency = (index: number) => {
    updateField("core_competencies", (editedProfile.core_competencies || []).filter((_, i) => i !== index))
  }

  const handleBigFiveChange = (scores: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    stability: number
  }) => {
    setEditedProfile(prev => ({
      ...prev,
      openness_score: scores.openness,
      conscientiousness_score: scores.conscientiousness,
      extraversion_score: scores.extraversion,
      agreeableness_score: scores.agreeableness,
      stability_score: scores.stability
    }))
  }

  const confidencePercent = Math.round((profile.confidence_score || 0.7) * 100)
  const isLowConfidence = confidencePercent <= 20

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center bg-gray-900">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className={textStyles.h3}>
              Perfil Cultural Identificado
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Confiança: {confidencePercent}% • Fonte: {profile.source === 'auto' ? 'IA' : 'Manual'}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsEditing(!isEditing)}
          className="gap-2"
        >
          <Pencil className="w-3.5 h-3.5" />
          {isEditing ? "Visualizar" : "Editar"}
        </Button>
      </div>
      
      {isLowConfidence && (
        <div className="rounded-md border border-amber-200 dark:border-amber-800/50 bg-amber-50 dark:bg-amber-900/20 p-3">
          <div className="flex items-start gap-2">
            <HelpCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-amber-800 dark:text-amber-300">Site com proteção anti-bot</p>
              <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                O site da empresa usa carregamento dinâmico (JavaScript/SPA) que não permite leitura automática. Clique em &quot;Editar&quot; acima para preencher manualmente as informações copiando do site da empresa.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="rounded-2xl border border-gray-200 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Missão
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            {isEditing ? (
              <textarea
                value={editedProfile.mission || ""}
                onChange={(e) => updateField("mission", e.target.value)}
                rows={3}
                className="w-full px-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 resize-none"
                placeholder="Descreva a missão da empresa..."
              />
            ) : (
              <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                {editedProfile.mission || "Não identificada"}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Visão
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            {isEditing ? (
              <textarea
                value={editedProfile.vision || ""}
                onChange={(e) => updateField("vision", e.target.value)}
                rows={3}
                className="w-full px-3 py-2 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-gray-500/20 focus:border-gray-500 resize-none"
                placeholder="Descreva a visão da empresa..."
              />
            ) : (
              <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                {editedProfile.vision || "Não identificada"}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Heart className="w-4 h-4" />
              Valores ({editedProfile.values.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-2">
              {editedProfile.values.map((value, index) => (
                <span
                  key={index}
                  className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium 
                    ${isEditing 
                      ? "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300 pr-1" 
                      : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                    }`}
                >
                  {value}
                  {isEditing && (
                    <button
                      onClick={() => removeValue(index)}
                      className="ml-1 p-0.5 rounded-full hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </span>
              ))}
              {editedProfile.values.length === 0 && (
                <span className="text-xs text-gray-600 italic">Nenhum valor identificado</span>
              )}
            </div>
            {isEditing && (
              <div className="flex gap-2 mt-3">
                <input
                  type="text"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addValue()}
                  placeholder="Novo valor..."
                  className="flex-1 px-3 py-1.5 text-xs rounded-md border border-emerald-200 dark:border-emerald-800 bg-white dark:bg-gray-900"
                />
                <Button size="sm" variant="ghost" onClick={addValue} className="h-8 px-2">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border border-amber-100 dark:border-amber-900/30 bg-amber-50/50 dark:bg-amber-900/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-amber-700 dark:text-amber-300 flex items-center gap-2">
              <Award className="w-4 h-4" />
              EVP - Proposta de Valor ({editedProfile.evp_bullets.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <ul className="space-y-1.5">
              {editedProfile.evp_bullets.map((evp, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-xs text-gray-800 dark:text-gray-200"
                >
                  <Lightbulb className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                  <span className="flex-1">{evp}</span>
                  {isEditing && (
                    <button
                      onClick={() => removeEvp(index)}
                      className="p-0.5 rounded-full hover:bg-amber-200 dark:hover:bg-amber-800 transition-colors"
                    >
                      <X className="w-3 h-3 text-amber-600" />
                    </button>
                  )}
                </li>
              ))}
              {editedProfile.evp_bullets.length === 0 && (
                <li className="text-xs text-gray-600 italic">Nenhum diferencial identificado</li>
              )}
            </ul>
            {isEditing && (
              <div className="flex gap-2 mt-3">
                <input
                  type="text"
                  value={newEvp}
                  onChange={(e) => setNewEvp(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addEvp()}
                  placeholder="Novo diferencial..."
                  className="flex-1 px-3 py-1.5 text-xs rounded-md border border-amber-200 dark:border-amber-800 bg-white dark:bg-gray-900"
                />
                <Button size="sm" variant="ghost" onClick={addEvp} className="h-8 px-2">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/20 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-4 px-4">
          <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            <Users className="w-4 h-4" />
            Competências Comportamentais ({(editedProfile.core_competencies || []).length})
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <div className="flex flex-wrap gap-2">
            {(editedProfile.core_competencies || []).map((competency, index) => (
              <span
                key={index}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium 
                  ${isEditing 
                    ? "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 pr-1" 
                    : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  }`}
              >
                {competency}
                {isEditing && (
                  <button
                    onClick={() => removeCompetency(index)}
                    className="ml-1 p-0.5 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </span>
            ))}
            {(editedProfile.core_competencies || []).length === 0 && (
              <span className="text-xs text-gray-600 italic">Nenhuma competência identificada</span>
            )}
          </div>
          {isEditing && (
            <div className="flex gap-2 mt-3">
              <input
                type="text"
                value={newCompetency}
                onChange={(e) => setNewCompetency(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addCompetency()}
                placeholder="Nova competência... Ex: Liderança, Comunicação"
                className="flex-1 px-3 py-1.5 text-xs rounded-md border border-purple-200 dark:border-purple-800 bg-white dark:bg-gray-900"
              />
              <Button size="sm" variant="ghost" onClick={addCompetency} className="h-8 px-2">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-2xl bg-gray-50/50 dark:bg-gray-800/20 backdrop-blur-sm border border-gray-200 dark:border-gray-700/50">
        <CardHeader className="pb-2 pt-4 px-4">
          <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            <Compass className="w-4 h-4" />
            Perfil Organizacional (Big Five)
            <Popover>
              <PopoverTrigger asChild>
                <button className="ml-1 p-0.5 rounded-full hover:bg-gray-200/50 dark:hover:bg-gray-700/50 transition-colors">
                  <HelpCircle className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-96 p-4 text-xs" side="top" align="start">
                <div className="space-y-3">
                  <h4 className="font-semibold text-gray-950 dark:text-gray-50">Metodologia Big Five (OCEAN)</h4>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    O modelo Big Five é a metodologia científica mais validada para análise de personalidade, 
                    amplamente utilizada em psicologia organizacional.
                  </p>
                  
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                    <h5 className="font-medium text-gray-800 dark:text-gray-200 mb-1.5">Como definimos os scores (0-100):</h5>
                    <ul className="space-y-1.5 text-gray-600 dark:text-gray-400">
                      <li><strong className="text-gray-700 dark:text-gray-300">Abertura (0-100):</strong> Baixo = tradicional, processos rígidos. Alto = inovadora, experimental, criativa.</li>
                      <li><strong className="text-gray-700 dark:text-gray-300">Conscienciosidade (0-100):</strong> Baixo = informal, flexível. Alto = estruturada, organizada, focada em qualidade.</li>
                      <li><strong className="text-gray-700 dark:text-gray-300">Extroversão (0-100):</strong> Baixo = trabalho individual, introspecção. Alto = colaborativa, comunicativa, trabalho em equipe.</li>
                      <li><strong className="text-gray-700 dark:text-gray-300">Amabilidade (0-100):</strong> Baixo = competitiva, foco em resultados. Alto = empática, foco em pessoas, diversidade.</li>
                      <li><strong className="text-gray-700 dark:text-gray-300">Estabilidade (0-100):</strong> Baixo = dinâmica, alta pressão, mudanças frequentes. Alto = ambiente calmo, previsível, baixo estresse.</li>
                    </ul>
                  </div>
                  
                  <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-md p-2.5 mt-2">
                    <p className="text-amber-800 dark:text-amber-200 leading-relaxed">
                      <strong>Nota:</strong> Este perfil é gerado por <strong>inferência</strong> a partir da análise do site da empresa 
                      e <strong>não garante acuracidade</strong>. Para maior precisão, recomendamos que a empresa aplique um 
                      <strong> assessment de cultura organizacional</strong> com metodologia validada para definir seu perfil.
                    </p>
                  </div>
                  
                  <p className="text-gray-500 dark:text-gray-500 italic text-micro pt-1">
                    Fonte: Goldberg (1990), Costa & McCrae (1992)
                  </p>
                </div>
              </PopoverContent>
            </Popover>
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <BigFiveRadar
            scores={{
              openness: editedProfile.openness_score,
              conscientiousness: editedProfile.conscientiousness_score,
              extraversion: editedProfile.extraversion_score,
              agreeableness: editedProfile.agreeableness_score,
              stability: editedProfile.stability_score
            }}
            onScoresChange={handleBigFiveChange}
            isEditable={isEditing}
            size={180}
          />
        </CardContent>
      </Card>

      {(editedProfile.industry || editedProfile.employee_count || editedProfile.headquarters || editedProfile.founded_year) && (
        <Card className="rounded-2xl border border-gray-200 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Informações da Empresa
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {editedProfile.industry && (
                <div className="flex items-start gap-2">
                  <Briefcase className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-micro text-gray-500 dark:text-gray-400 block">Indústria</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">{editedProfile.industry}</span>
                  </div>
                </div>
              )}
              {(editedProfile.employee_count || editedProfile.company_size) && (
                <div className="flex items-start gap-2">
                  <Users className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-micro text-gray-500 dark:text-gray-400 block">Tamanho</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">
                      {editedProfile.employee_count ? `${editedProfile.employee_count.toLocaleString()} funcionários` : editedProfile.company_size}
                    </span>
                  </div>
                </div>
              )}
              {editedProfile.headquarters && (
                <div className="flex items-start gap-2">
                  <MapPin className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-micro text-gray-500 dark:text-gray-400 block">Sede</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">{editedProfile.headquarters}</span>
                  </div>
                </div>
              )}
              {editedProfile.founded_year && (
                <div className="flex items-start gap-2">
                  <Calendar className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-micro text-gray-500 dark:text-gray-400 block">Fundação</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">{editedProfile.founded_year}</span>
                  </div>
                </div>
              )}
              {editedProfile.locations && editedProfile.locations.length > 0 && (
                <div className="flex items-start gap-2 col-span-2">
                  <Globe className="w-3.5 h-3.5 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-micro text-gray-500 dark:text-gray-400 block">Localidades</span>
                    <span className="text-xs text-gray-800 dark:text-gray-200">{editedProfile.locations.join(", ")}</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {(editedProfile.work_model || editedProfile.growth_opportunities || editedProfile.team_dynamics || editedProfile.leadership_style) && (
        <Card className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Modelo de Trabalho e Crescimento
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {editedProfile.work_model && (
              <div>
                <span className="text-micro text-gray-600 dark:text-gray-400 font-medium block mb-1">Modelo de Trabalho</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.work_model}</p>
              </div>
            )}
            {editedProfile.growth_opportunities && (
              <div>
                <span className="text-micro text-gray-600 dark:text-gray-400 font-medium block mb-1">Oportunidades de Crescimento</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.growth_opportunities}</p>
              </div>
            )}
            {editedProfile.team_dynamics && (
              <div>
                <span className="text-micro text-gray-600 dark:text-gray-400 font-medium block mb-1">Dinâmica de Equipe</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.team_dynamics}</p>
              </div>
            )}
            {editedProfile.leadership_style && (
              <div>
                <span className="text-micro text-gray-600 dark:text-gray-400 font-medium block mb-1">Estilo de Liderança</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.leadership_style}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {(editedProfile.dei_initiatives || editedProfile.sustainability || editedProfile.social_impact) && (
        <Card className="rounded-2xl border border-green-100 dark:border-green-900/30 bg-green-50/50 dark:bg-green-900/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-green-700 dark:text-green-300 flex items-center gap-2">
              <Leaf className="w-4 h-4" />
              Responsabilidade Social
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {editedProfile.dei_initiatives && (
              <div>
                <span className="text-micro text-green-600 dark:text-green-400 font-medium block mb-1">Diversidade, Equidade e Inclusão</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.dei_initiatives}</p>
              </div>
            )}
            {editedProfile.sustainability && (
              <div>
                <span className="text-micro text-green-600 dark:text-green-400 font-medium block mb-1">Sustentabilidade</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.sustainability}</p>
              </div>
            )}
            {editedProfile.social_impact && (
              <div>
                <span className="text-micro text-green-600 dark:text-green-400 font-medium block mb-1">Impacto Social</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.social_impact}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {((editedProfile.tech_stack && editedProfile.tech_stack.length > 0) || editedProfile.engineering_culture) && (
        <Card className="rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-800/20 backdrop-blur-sm">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <Code className="w-4 h-4" />
              Tecnologia
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {editedProfile.tech_stack && editedProfile.tech_stack.length > 0 && (
              <div>
                <span className="text-micro text-slate-600 dark:text-slate-400 font-medium block mb-2">Stack Tecnológico</span>
                <div className="flex flex-wrap gap-1.5">
                  {editedProfile.tech_stack.map((tech, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-micro font-medium bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {editedProfile.engineering_culture && (
              <div>
                <span className="text-micro text-slate-600 dark:text-slate-400 font-medium block mb-1">Cultura de Engenharia</span>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">{editedProfile.engineering_culture}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between pt-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onReanalyze}
          disabled={isLoading}
          className="gap-2 text-gray-600 hover:text-gray-900"
        >
          <RotateCcw className="w-4 h-4" />
          Refazer Análise
        </Button>

        <div className="flex gap-2">
          {hasChanges && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSaveAdjustments(editedProfile)}
              disabled={isLoading}
              className="gap-2 border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <Save className="w-4 h-4" />
              Salvar Ajustes
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => {
              setAcceptedAll(true)
              setTimeout(() => {
                onAccept(editedProfile)
              }, 800)
            }}
            disabled={isLoading || acceptedAll}
            className={`gap-2 bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-all duration-300 ease-in-out ${
              acceptedAll ? 'scale-105 ring-2 ring-gray-900/50 ring-offset-2 dark:ring-gray-50/50' : 'hover:scale-[1.02]'
            }`}
          >
            <CheckCircle2 
              className={`w-4 h-4 transition-all duration-300 ${
                acceptedAll ? 'scale-125' : ''
              }`} 
            />
            <span className="transition-all duration-300">
              {acceptedAll 
                ? "Aceito! ✓" 
                : hasChanges 
                  ? "Aceitar com Ajustes" 
                  : "Aceitar Tudo"
              }
            </span>
          </Button>
        </div>
      </div>
    </div>
  )
}
