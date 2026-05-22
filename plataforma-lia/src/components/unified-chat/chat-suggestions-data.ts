import type React from "react"
import {
  Search, Users, BarChart3, Calendar,
  TrendingUp, Target, FileText, Briefcase, Building,
  Clock, AlertCircle, CheckCircle, Star, Filter,
  MessageSquare, Globe, Zap, Brain
} from "lucide-react"

export interface QueryExample {
  id: string
  icon: React.ElementType
  question: string
  category: 'metricas' | 'candidatos' | 'vagas' | 'pipeline' | 'analise' | 'previsao' | 'comparacao'
  /** descrição livre opcional, usada como tooltip ou hint de busca */
  description?: string
}

export const CATEGORY_INFO: Record<string, { icon: React.ElementType; label?: string }> = {
  metricas: { icon: BarChart3 },
  candidatos: { icon: Users },
  vagas: { icon: Briefcase },
  pipeline: { icon: Filter },
  analise: { icon: Brain },
  previsao: { icon: TrendingUp },
  comparacao: { icon: Target },
}

export interface QueryStructure {
  id: string
  icon: React.ElementType
  category: 'metricas' | 'candidatos' | 'vagas' | 'pipeline' | 'analise' | 'previsao' | 'comparacao'
}

export const QUERY_STRUCTURES: QueryStructure[] = [
  { id: 'q1', icon: BarChart3, category: 'metricas' },
  { id: 'q2', icon: TrendingUp, category: 'metricas' },
  { id: 'q3', icon: Clock, category: 'metricas' },
  { id: 'q4', icon: BarChart3, category: 'metricas' },
  { id: 'q5', icon: AlertCircle, category: 'metricas' },
  { id: 'q6', icon: Star, category: 'candidatos' },
  { id: 'q7', icon: Users, category: 'candidatos' },
  { id: 'q8', icon: CheckCircle, category: 'candidatos' },
  { id: 'q9', icon: Search, category: 'candidatos' },
  { id: 'q10', icon: Users, category: 'candidatos' },
  { id: 'q11', icon: Globe, category: 'candidatos' },
  { id: 'q12', icon: Briefcase, category: 'vagas' },
  { id: 'q13', icon: AlertCircle, category: 'vagas' },
  { id: 'q14', icon: Building, category: 'vagas' },
  { id: 'q15', icon: Target, category: 'vagas' },
  { id: 'q16', icon: Clock, category: 'vagas' },
  { id: 'q17', icon: Filter, category: 'pipeline' },
  { id: 'q18', icon: AlertCircle, category: 'pipeline' },
  { id: 'q19', icon: TrendingUp, category: 'pipeline' },
  { id: 'q20', icon: Clock, category: 'pipeline' },
  { id: 'q21', icon: Brain, category: 'analise' },
  { id: 'q22', icon: FileText, category: 'analise' },
  { id: 'q23', icon: MessageSquare, category: 'analise' },
  { id: 'q24', icon: FileText, category: 'analise' },
  { id: 'q25', icon: Zap, category: 'analise' },
  { id: 'q26', icon: TrendingUp, category: 'previsao' },
  { id: 'q27', icon: Calendar, category: 'previsao' },
  { id: 'q28', icon: Target, category: 'previsao' },
  { id: 'q29', icon: Clock, category: 'previsao' },
  { id: 'q30', icon: Users, category: 'comparacao' },
  { id: 'q31', icon: BarChart3, category: 'comparacao' },
  { id: 'q32', icon: Building, category: 'comparacao' },
  { id: 'q33', icon: Target, category: 'comparacao' },
]

export const QUERY_EXAMPLES: QueryExample[] = QUERY_STRUCTURES.map(s => ({
  ...s,
  question: '',
}))
