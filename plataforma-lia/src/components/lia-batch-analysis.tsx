"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LIAIcon } from "@/components/ui/lia-icon"
import {
  Brain, Zap, Target, TrendingUp, Users, CheckCircle, AlertCircle,
  Play, Pause, RefreshCw, Download, Filter, BarChart3, PieChart,
  ArrowUp, ArrowDown, User, Building, MapPin, Briefcase, Info
} from "lucide-react"

interface Candidate {
  id: string
  name: string
  position: string
  location: string
  company?: string
  score?: number
  skills?: string[]
  cv_text?: string
  experience_years?: number
  seniority_level?: string
}

interface ScoreBreakdown {
  match_tecnico: number
  fit_personalidade: number
  relevancia_experiencia: number
  alinhamento_cultural: number
}

interface CandidateAnalysisResult {
  candidate_id: string
  candidate_name: string
  lia_score: number
  fit_score: number
  archetype: string
  strengths: string[]
  gaps: string[]
  recommendation: string
  recommendation_level: string
  explanation: string
  score_breakdown?: ScoreBreakdown
  potential_roles?: string[]
}

interface AnalysisResponse {
  success: boolean
  total_analyzed: number
  average_score: number
  results: CandidateAnalysisResult[]
  insights?: {
    byPosition: Record<string, { count: number; avgScore: number }>
    byLocation: Record<string, { count: number; avgScore: number }>
    skills: Record<string, number>
  }
  recommendations?: string[]
  alerts?: { type: string; message: string }[]
}

interface LIABatchAnalysisProps {
  candidates: Candidate[]
  jobVacancyId?: string
  jobTitle?: string
  jobRequirements?: string[]
  jobDescription?: string
  onAnalysisComplete?: (results: AnalysisResponse) => void
}

export function LIABatchAnalysis({ 
  candidates, 
  jobVacancyId,
  jobTitle,
  jobRequirements,
  jobDescription,
  onAnalysisComplete 
}: LIABatchAnalysisProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentAnalyzingName, setCurrentAnalyzingName] = useState<string | null>(null)

  const startAnalysis = async () => {
    setIsAnalyzing(true)
    setProgress(0)
    setError(null)

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev
        return prev + Math.random() * 10
      })
    }, 500)

    try {
      setCurrentAnalyzingName("Preparando análise com IA...")

      const analysisType = jobVacancyId || jobTitle ? "contextual" : "general"
      
      const requestBody = {
        candidates: candidates.map(c => ({
          id: c.id,
          name: c.name,
          position: c.position || null,
          location: c.location || null,
          company: c.company || null,
          skills: c.skills || [],
          cv_text: c.cv_text || null,
          experience_years: c.experience_years || null,
          seniority_level: c.seniority_level || null
        })),
        job_vacancy_id: jobVacancyId || null,
        analysis_type: analysisType,
        job_title: jobTitle || null,
        job_requirements: jobRequirements || null,
        job_description: jobDescription || null
      }

      setCurrentAnalyzingName("Analisando candidatos com Claude AI...")

      const response = await fetch("/api/lia/api/v1/analysis/candidates", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Erro na análise: ${response.status}`)
      }

      const data: AnalysisResponse = await response.json()

      clearInterval(progressInterval)
      setProgress(100)
      setAnalysisResults(data)
      
      if (onAnalysisComplete) {
        onAnalysisComplete(data)
      }
    } catch (err) {
      clearInterval(progressInterval)
      const errorMessage = err instanceof Error ? err.message : "Erro ao realizar análise"
      setError(errorMessage)
      console.error("Analysis error:", err)
    } finally {
      setIsAnalyzing(false)
      setCurrentAnalyzingName(null)
    }
  }

  const exportResults = () => {
    if (!analysisResults) return

    const csvContent = [
      ["Nome", "Score LIA", "Fit Score", "Arquétipo", "Recomendação", "Pontos Fortes", "Gaps", "Explicação"].join(","),
      ...analysisResults.results.map(r => [
        r.candidate_name,
        r.lia_score,
        r.fit_score,
        r.archetype,
        r.recommendation_level,
        r.strengths.join("; "),
        r.gaps.join("; "),
        `"${r.explanation.replace(/"/g, '""')}"`
      ].join(","))
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `lia-analysis-${new Date().toISOString().split("T")[0]}.csv`
    link.click()
  }

  const getRecommendationBadge = (level: string) => {
    switch (level) {
      case "highly_recommended":
        return <Badge className="bg-green-100 text-green-700">Altamente Recomendado</Badge>
      case "recommended":
        return <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">Recomendado</Badge>
      case "potential":
        return <Badge className="bg-yellow-100 text-yellow-700">Potencial</Badge>
      case "low_match":
        return <Badge className="bg-orange-100 text-orange-700">Match Baixo</Badge>
      case "not_recommended":
        return <Badge className="bg-red-100 text-red-700">Não Recomendado</Badge>
      default:
        return <Badge variant="outline">{level}</Badge>
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 font-sans">
              <LIAIcon size="sm" />
              Análise Inteligente com LIA
            </CardTitle>
            <CardDescription>
              Análise em lote de {candidates.length} candidatos selecionados
              {jobTitle && <span className="ml-1">para "{jobTitle}"</span>}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {analysisResults && (
              <Button variant="outline" size="sm" onClick={exportResults}>
                <Download className="w-4 h-4 mr-2" />
                Exportar
              </Button>
            )}
            <Button
              size="sm"
              onClick={startAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Analisando...
                </>
              ) : analysisResults ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reanalisar
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Iniciar Análise
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-red-50 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {isAnalyzing && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Analisando candidatos com IA...</span>
              <span className="font-medium">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            {currentAnalyzingName && (
              <p className="text-xs text-gray-600 flex items-center gap-1">
                <Brain className="w-3 h-3 animate-pulse text-wedo-cyan" />
                {currentAnalyzingName}
              </p>
            )}
          </div>
        )}

        {analysisResults && !isAnalyzing && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Visão Geral</TabsTrigger>
              <TabsTrigger value="candidates">Top Candidatos</TabsTrigger>
              <TabsTrigger value="insights">Insights</TabsTrigger>
              <TabsTrigger value="recommendations">Recomendações</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-xs text-gray-600">Total</span>
                    </div>
                    <div className="text-2xl font-bold">{analysisResults.total_analyzed}</div>
                    <p className="text-xs text-gray-600">candidatos analisados</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <Target className="w-4 h-4 text-green-500" />
                      <span className="text-xs text-gray-600">Score Médio</span>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      {analysisResults.average_score}%
                    </div>
                    <p className="text-xs text-gray-600">compatibilidade</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <TrendingUp className="w-4 h-4 text-purple-500" />
                      <span className="text-xs text-gray-600">Alto Potencial</span>
                    </div>
                    <div className="text-2xl font-bold text-purple-600">
                      {analysisResults.results.filter(r => r.lia_score >= 85).length}
                    </div>
                    <p className="text-xs text-gray-600">candidatos 85%+</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <Zap className="w-4 h-4 text-orange-500" />
                      <span className="text-xs text-gray-600">Ação Imediata</span>
                    </div>
                    <div className="text-2xl font-bold text-orange-600">
                      {analysisResults.results.filter(r => r.recommendation_level === "highly_recommended").length}
                    </div>
                    <p className="text-xs text-gray-600">requerem contato</p>
                  </CardContent>
                </Card>
              </div>

              {analysisResults.alerts && analysisResults.alerts.length > 0 && (
                <div className="space-y-2">
                  {analysisResults.alerts.map((alert, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-2 p-3 rounded-md ${
                        alert.type === 'success' ? 'bg-green-50 text-green-700' :
                        alert.type === 'warning' ? 'bg-yellow-50 text-yellow-700' :
                        'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {alert.type === 'success' ? <CheckCircle className="w-4 h-4" /> :
                       alert.type === 'warning' ? <AlertCircle className="w-4 h-4" /> :
                       <Brain className="w-4 h-4 text-wedo-cyan" />}
                      <span className="text-sm">{alert.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="candidates" className="space-y-4">
              <div className="space-y-3">
                {analysisResults.results
                  .sort((a, b) => b.lia_score - a.lia_score)
                  .map((result) => {
                    const candidate = candidates.find(c => c.id === result.candidate_id)
                    return (
                      <Card key={result.candidate_id} className="hover:transition-shadow">
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3">
                              <div className="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
                                <User className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                              </div>
                              <div>
                                <h4 className="font-semibold">{result.candidate_name}</h4>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                  <Briefcase className="w-3 h-3" />
                                  {candidate?.position || "Cargo não informado"}
                                  {candidate?.company && (
                                    <>
                                      <span>•</span>
                                      <Building className="w-3 h-3" />
                                      {candidate.company}
                                    </>
                                  )}
                                  {candidate?.location && (
                                    <>
                                      <span>•</span>
                                      <MapPin className="w-3 h-3" />
                                      {candidate.location}
                                    </>
                                  )}
                                </div>
                                <div className="mt-2">
                                  <Badge variant="outline" className="text-xs">
                                    {result.archetype}
                                  </Badge>
                                </div>
                                <div className="mt-2 text-xs text-gray-600">
                                  <strong>Pontos Fortes:</strong> {result.strengths.join(", ")}
                                </div>
                                {result.gaps.length > 0 && (
                                  <div className="mt-1 text-xs text-gray-500">
                                    <strong>Gaps:</strong> {result.gaps.join(", ")}
                                  </div>
                                )}
                                <p className="mt-2 text-xs text-gray-600 italic">
                                  {result.explanation}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <div className="text-right">
                                <div className="text-2xl font-bold text-green-600">
                                  {result.lia_score}%
                                </div>
                                <p className="text-xs text-gray-600">Score LIA</p>
                              </div>
                              {getRecommendationBadge(result.recommendation_level)}
                              {result.score_breakdown && (
                                <div className="text-xs text-gray-500 mt-2 text-right">
                                  <div>Técnico: {result.score_breakdown.match_tecnico}%</div>
                                  <div>Personalidade: {result.score_breakdown.fit_personalidade}%</div>
                                  <div>Experiência: {result.score_breakdown.relevancia_experiencia}%</div>
                                  <div>Cultural: {result.score_breakdown.alinhamento_cultural}%</div>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
              </div>
            </TabsContent>

            <TabsContent value="insights" className="space-y-4">
              {analysisResults.insights?.skills && Object.keys(analysisResults.insights.skills).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Top Skills Identificadas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(analysisResults.insights.skills).map(([skill, percentage]) => (
                        <div key={skill} className="flex items-center gap-3">
                          <span className="text-sm w-20">{skill}</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600">{percentage}%</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-2 gap-4">
                {analysisResults.insights?.byPosition && Object.keys(analysisResults.insights.byPosition).length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Por Cargo</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(analysisResults.insights.byPosition).map(([position, data]) => (
                          <div key={position} className="flex items-center justify-between">
                            <span className="text-sm">{position}</span>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{data.count}</Badge>
                              <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                                {data.avgScore}%
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {analysisResults.insights?.byLocation && Object.keys(analysisResults.insights.byLocation).length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Por Localização</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(analysisResults.insights.byLocation).map(([location, data]) => (
                          <div key={location} className="flex items-center justify-between">
                            <span className="text-sm">{location}</span>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{data.count}</Badge>
                              <Badge className="bg-green-100 text-green-700">
                                {data.avgScore}%
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Distribuição de Arquétipos</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(
                      analysisResults.results.reduce((acc, r) => {
                        acc[r.archetype] = (acc[r.archetype] || 0) + 1
                        return acc
                      }, {} as Record<string, number>)
                    ).map(([archetype, count]) => (
                      <Badge key={archetype} variant="outline" className="text-xs">
                        {archetype}: {count}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              {analysisResults.recommendations && analysisResults.recommendations.length > 0 && (
                <div className="space-y-3">
                  {analysisResults.recommendations.map((rec, index) => (
                    <Card key={index} className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-3">
                          <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                          <div>
                            <p className="text-sm">{rec}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <Button className="flex-1">
                  <Users className="w-4 h-4 mr-2" />
                  Criar Lista de Contato
                </Button>
                <Button variant="outline" className="flex-1" onClick={exportResults}>
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Gerar Relatório Completo
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        )}

        {!analysisResults && !isAnalyzing && (
          <div className="text-center py-8">
            <LIAIcon size="lg" className="mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold mb-2">Análise Inteligente Pronta</h3>
            <p className="text-sm text-gray-600 mb-4">
              A LIA irá analisar todos os candidatos selecionados usando Claude AI e fornecer insights valiosos
              sobre compatibilidade, habilidades e recomendações de contratação.
            </p>
            <div className="flex justify-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Score de compatibilidade
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Arquétipo Big Five
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Recomendações
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
