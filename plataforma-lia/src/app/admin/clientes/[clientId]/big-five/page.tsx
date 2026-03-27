"use client"

import React, { use, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Brain,
  Lightbulb,
  Target,
  Users,
  Heart,
  Shield,
  Save,
  Eye,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  Info
} from "lucide-react"

interface TraitConfig {
  weight: number
  idealValue: number
}

interface BigFiveConfig {
  openness: TraitConfig
  conscientiousness: TraitConfig
  extraversion: TraitConfig
  agreeableness: TraitConfig
  neuroticism: TraitConfig
}

const defaultConfig: BigFiveConfig = {
  openness: { weight: 50, idealValue: 70 },
  conscientiousness: { weight: 70, idealValue: 75 },
  extraversion: { weight: 60, idealValue: 65 },
  agreeableness: { weight: 65, idealValue: 70 },
  neuroticism: { weight: 40, idealValue: 30 }
}

const traits = [
  {
    key: 'openness' as keyof BigFiveConfig,
    name: 'Abertura',
    fullName: 'Abertura à Experiência',
    icon: Lightbulb,
    color: '#DC143C',
    bgColor: 'bg-status-error/10 dark:bg-status-error/20',
    borderColor: 'border-status-error/30 dark:border-status-error/30',
    description: 'Criatividade, curiosidade e disposição para novas experiências. Pessoas com alta abertura são imaginativas e apreciam a arte.'
  },
  {
    key: 'conscientiousness' as keyof BigFiveConfig,
    name: 'Conscienciosidade',
    fullName: 'Conscienciosidade',
    icon: Target,
    color: '#2E8B57',
    bgColor: 'bg-status-success/10 dark:bg-status-success/20',
    borderColor: 'border-status-success/30 dark:border-status-success/30',
    description: 'Organização, disciplina e orientação para objetivos. Alta conscienciosidade indica responsabilidade e persistência.'
  },
  {
    key: 'extraversion' as keyof BigFiveConfig,
    name: 'Extroversão',
    fullName: 'Extroversão',
    icon: Users,
    color: '#FFA500',
    bgColor: 'bg-wedo-orange/10 dark:bg-wedo-orange/20',
    borderColor: 'border-wedo-orange/30 dark:border-wedo-orange/30',
    description: 'Energia social, assertividade e busca por estímulos. Extrovertidos são comunicativos e entusiasmados.'
  },
  {
    key: 'agreeableness' as keyof BigFiveConfig,
    name: 'Amabilidade',
    fullName: 'Amabilidade',
    icon: Heart,
    color: '#8B4B8C',
    bgColor: 'bg-wedo-purple/10 dark:bg-wedo-purple/20',
    borderColor: 'border-wedo-purple/30 dark:border-wedo-purple/30',
    description: 'Cooperação, empatia e consideração pelos outros. Alta amabilidade indica altruísmo e confiança.'
  },
  {
    key: 'neuroticism' as keyof BigFiveConfig,
    name: 'Neuroticismo',
    fullName: 'Neuroticismo',
    icon: Shield,
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    borderColor: 'border-gray-300 dark:border-gray-600',
    description: 'Tendência a experienciar emoções negativas. Baixo neuroticismo indica estabilidade emocional e resiliência.'
  }
]

export default function ClientBigFivePage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  
  const [isEnabled, setIsEnabled] = useState(true)
  const [matchThreshold, setMatchThreshold] = useState(70)
  const [evaluationMode, setEvaluationMode] = useState<'suggestive' | 'eliminatory'>('suggestive')
  const [selectedJob, setSelectedJob] = useState<string>('dev-senior')
  const [traitWeights, setTraitWeights] = useState<BigFiveConfig>(defaultConfig)
  const [jobProfiles, setJobProfiles] = useState<Record<string, BigFiveConfig>>({
    'dev-senior': defaultConfig,
    'pm': { ...defaultConfig, extraversion: { weight: 80, idealValue: 75 }, agreeableness: { weight: 70, idealValue: 70 } },
    'sales': { ...defaultConfig, extraversion: { weight: 90, idealValue: 85 }, neuroticism: { weight: 60, idealValue: 25 } },
    'analyst': { ...defaultConfig, conscientiousness: { weight: 85, idealValue: 80 }, openness: { weight: 70, idealValue: 70 } },
    'hr': { ...defaultConfig, agreeableness: { weight: 85, idealValue: 80 }, extraversion: { weight: 75, idealValue: 70 } }
  })
  
  const [showPreview, setShowPreview] = useState(false)

  const handleWeightChange = (trait: keyof BigFiveConfig, value: number) => {
    setTraitWeights(prev => ({
      ...prev,
      [trait]: { ...prev[trait], weight: value }
    }))
  }

  const handleIdealValueChange = (trait: keyof BigFiveConfig, value: number) => {
    setTraitWeights(prev => ({
      ...prev,
      [trait]: { ...prev[trait], idealValue: value }
    }))
  }

  const handleJobChange = (jobId: string) => {
    setSelectedJob(jobId)
    if (jobProfiles[jobId]) {
      setTraitWeights(jobProfiles[jobId])
    }
  }

  const handleSaveProfile = () => {
    setJobProfiles(prev => ({
      ...prev,
      [selectedJob]: traitWeights
    }))
  }

  const sampleCandidateScores = {
    openness: 72,
    conscientiousness: 68,
    extraversion: 55,
    agreeableness: 78,
    neuroticism: 35
  }

  const calculateMatch = () => {
    let totalWeight = 0
    let weightedScore = 0
    
    traits.forEach(trait => {
      const config = traitWeights[trait.key]
      const candidateScore = sampleCandidateScores[trait.key]
      const diff = Math.abs(candidateScore - config.idealValue)
      const traitScore = Math.max(0, 100 - diff)
      
      weightedScore += traitScore * config.weight
      totalWeight += config.weight
    })
    
    return Math.round(weightedScore / totalWeight)
  }

  const matchScore = calculateMatch()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-6 h-6 text-wedo-purple" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Configuração Big Five
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Avaliação de personalidade e perfil comportamental para o cliente {clientId}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
          >
            <Eye className="w-4 h-4 mr-2" />
            {showPreview ? 'Ocultar Preview' : 'Ver Preview'}
          </Button>
          <Button 
            size="sm"
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            onClick={handleSaveProfile}
          >
            <Save className="w-4 h-4 mr-2" />
            Salvar Configuração
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
            <Brain className="w-4 h-4 text-wedo-cyan" />
            Configurações Gerais
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center justify-between p-4 rounded-md bg-gray-50 dark:bg-gray-800/50">
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Big Five Ativo
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Habilitar avaliação de personalidade
                </p>
              </div>
              <Switch 
                checked={isEnabled} 
                onCheckedChange={setIsEnabled}
              />
            </div>

            <div className="p-4 rounded-md bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Threshold de Match
                </p>
                <span className="text-sm font-semibold text-gray-900 dark:text-gray-50">{matchThreshold}%</span>
              </div>
              <Slider
                value={[matchThreshold]}
                onValueChange={(v) => setMatchThreshold(v[0])}
                min={0}
                max={100}
                step={5}
              />
              <p className="text-xs mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Mínimo para considerar compatível
              </p>
            </div>

            <div className="p-4 rounded-md bg-gray-50 dark:bg-gray-800/50">
              <p className="text-sm font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
                Modo de Avaliação
              </p>
              <Select value={evaluationMode} onValueChange={(v) => setEvaluationMode(v as 'suggestive' | 'eliminatory')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="suggestive">
                    <div className="flex items-center gap-2">
                      <Info className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                      <span>Sugestivo</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="eliminatory">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-3 h-3 text-status-warning" />
                      <span>Eliminatório</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                {evaluationMode === 'suggestive' 
                  ? 'Score aparece como sugestão' 
                  : 'Candidatos abaixo do threshold são filtrados'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
              <BarChart3 className="w-4 h-4 text-wedo-purple" />
              Perfis por Cargo
            </CardTitle>
            <Select value={selectedJob} onValueChange={handleJobChange}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Selecione um cargo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dev-senior">Desenvolvedor Senior</SelectItem>
                <SelectItem value="pm">Product Manager</SelectItem>
                <SelectItem value="sales">Vendedor</SelectItem>
                <SelectItem value="analyst">Analista de Dados</SelectItem>
                <SelectItem value="hr">Recursos Humanos</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {traits.map((trait) => {
              const Icon = trait.icon
              const config = traitWeights[trait.key]
              
              return (
                <Card key={trait.key} className={`${trait.bgColor} ${trait.borderColor} border`}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3 mb-4">
                      <div 
                        className="w-10 h-10 rounded-md flex items-center justify-center"
                        style={{ backgroundColor: `${trait.color}20` }}
                      >
                        <Icon className="w-5 h-5" style={{ color: trait.color }} />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {trait.fullName}
                        </h4>
                        <p className="text-xs mt-1 line-clamp-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {trait.description}
                        </p>
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
                            Peso/Importância
                          </span>
                          <span className="text-xs font-semibold" style={{ color: trait.color }}>
                            {config.weight}%
                          </span>
                        </div>
                        <Slider
                          value={[config.weight]}
                          onValueChange={(v) => handleWeightChange(trait.key, v[0])}
                          min={0}
                          max={100}
                          step={5}
                        />
                      </div>
                      
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>
                            Valor Ideal
                          </span>
                          <span className="text-xs font-semibold" style={{ color: trait.color }}>
                            {config.idealValue}%
                          </span>
                        </div>
                        <Slider
                          value={[config.idealValue]}
                          onValueChange={(v) => handleIdealValueChange(trait.key, v[0])}
                          min={0}
                          max={100}
                          step={5}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {showPreview && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Preview: Visualização do Candidato
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-md bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-wedo-purple/30 dark:border-wedo-purple/30">
                <div className="text-center mb-4">
                  <Brain className="w-10 h-10 mx-auto text-wedo-purple mb-2" />
                  <h4 className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    Avaliação de Perfil Comportamental
                  </h4>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Responda às perguntas para identificar seu perfil
                  </p>
                </div>
                
                <div className="space-y-3 mt-4">
                  <div className="p-3 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Exemplo de pergunta:</p>
                    <p className="text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                      "Costumo buscar novas experiências e ideias criativas no meu trabalho"
                    </p>
                    <div className="flex items-center gap-2 mt-3">
                      <span className="text-xs text-gray-500">Discordo</span>
                      <div className="flex-1 flex gap-1">
                        {[1, 2, 3, 4, 5].map(n => (
                          <button 
                            key={n} 
                            className={`flex-1 h-8 rounded text-xs font-medium transition-colors ${
                              n === 4 
                                ? 'bg-wedo-purple/15 dark:bg-wedo-purple/50 text-wedo-purple dark:text-wedo-purple border-2 border-wedo-purple/30' 
                                : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                            }`}
                          >
                            {n}
                          </button>
                        ))}
                      </div>
                      <span className="text-xs text-gray-500">Concordo</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <BarChart3 className="w-4 h-4 text-wedo-purple" />
                Preview: Resultado de Análise
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-md bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-status-success/30 dark:border-status-success/30">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-status-success/15 dark:bg-status-success/50 flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6 text-status-success" />
                    </div>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        Match de Personalidade
                      </p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        Compatibilidade com o perfil do cargo
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-status-success">{matchScore}%</p>
                    <p className="text-xs text-status-success">
                      {matchScore >= matchThreshold ? 'Compatível' : 'Abaixo do threshold'}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {traits.map((trait) => {
                    const candidateScore = sampleCandidateScores[trait.key]
                    const idealValue = traitWeights[trait.key].idealValue
                    const diff = Math.abs(candidateScore - idealValue)
                    const isClose = diff <= 15
                    
                    return (
                      <div key={trait.key} className="flex items-center gap-3">
                        <div 
                          className="w-8 h-8 rounded-md flex items-center justify-center"
                          style={{ backgroundColor: `${trait.color}20` }}
                        >
                          <trait.icon className="w-4 h-4" style={{ color: trait.color }} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                              {trait.name}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                                Ideal: {idealValue}%
                              </span>
                              <span className="text-xs font-semibold" style={{ color: trait.color }}>
                                {candidateScore}%
                              </span>
                            </div>
                          </div>
                          <div className="relative h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div 
                              className="absolute h-full rounded-full transition-all"
                              style={{ 
                                width: `${candidateScore}%`, 
                                backgroundColor: trait.color 
                              }}
                            />
                            <div 
                              className="absolute h-full w-1 bg-gray-900 dark:bg-white"
                              style={{ left: `${idealValue}%`, opacity: 0.5 }}
                            />
                          </div>
                        </div>
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                          isClose 
                            ? 'bg-status-success/15 dark:bg-status-success/50' 
                            : 'bg-status-warning/15 dark:bg-status-warning/50'
                        }`}>
                          {isClose 
                            ? <CheckCircle2 className="w-3 h-3 text-status-success" />
                            : <AlertCircle className="w-3 h-3 text-status-warning" />
                          }
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="p-3 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 border border-wedo-purple/30 dark:border-wedo-purple/30">
                  <div className="flex items-start gap-2">
                    <Brain className="w-4 h-4 text-wedo-purple mt-0.5" />
                    <div>
                      <p className="text-xs font-medium text-wedo-purple dark:text-wedo-purple">
                        Insight Comportamental
                      </p>
                      <p className="text-xs text-wedo-purple dark:text-wedo-purple mt-1">
                        Candidato apresenta perfil equilibrado com alta amabilidade e boa conscienciosidade. 
                        Adequado para funções que exigem trabalho em equipe e organização.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
