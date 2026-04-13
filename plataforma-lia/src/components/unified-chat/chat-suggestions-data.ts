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
  description?: string
  category: 'metricas' | 'candidatos' | 'vagas' | 'pipeline' | 'analise' | 'previsao' | 'comparacao'
}

export const CATEGORY_INFO = {
  metricas: { label: 'Métricas', icon: BarChart3 },
  candidatos: { label: 'Candidatos', icon: Users },
  vagas: { label: 'Vagas', icon: Briefcase },
  pipeline: { label: 'Pipeline', icon: Filter },
  analise: { label: 'Análise', icon: Brain },
  previsao: { label: 'Previsões', icon: TrendingUp },
  comparacao: { label: 'Comparar', icon: Target },
}

export const QUERY_EXAMPLES: QueryExample[] = [
  { id: 'q1', icon: BarChart3, question: 'Quantos candidatos estão ativos no funil?', category: 'metricas' },
  { id: 'q2', icon: TrendingUp, question: 'Qual é a taxa de conversão do meu funil este mês?', category: 'metricas' },
  { id: 'q3', icon: Clock, question: 'Qual o tempo médio para fechar uma vaga?', category: 'metricas' },
  { id: 'q4', icon: BarChart3, question: 'Quantas contratações fizemos este trimestre?', category: 'metricas' },
  { id: 'q5', icon: AlertCircle, question: 'Quantas vagas estão atrasadas no SLA?', category: 'metricas' },
  { id: 'q6', icon: Star, question: 'Quem são os melhores candidatos para a vaga de Desenvolvedor?', category: 'candidatos' },
  { id: 'q7', icon: Users, question: 'Quantos candidatos aguardam entrevista?', category: 'candidatos' },
  { id: 'q8', icon: CheckCircle, question: 'Quais candidatos têm nota LIA acima de 80?', category: 'candidatos' },
  { id: 'q9', icon: Search, question: 'Encontre candidatos com experiência em React e Node.js', category: 'candidatos' },
  { id: 'q10', icon: Users, question: 'Quais candidatos têm perfil de liderança?', category: 'candidatos' },
  { id: 'q11', icon: Globe, question: 'Buscar candidatos na Busca Global para a vaga de Data Analyst', category: 'candidatos' },
  { id: 'q12', icon: Briefcase, question: 'Quais vagas estão abertas há mais de 30 dias?', category: 'vagas' },
  { id: 'q13', icon: AlertCircle, question: 'Quais vagas estão sem candidatos?', category: 'vagas' },
  { id: 'q14', icon: Building, question: 'Quantas vagas temos por departamento?', category: 'vagas' },
  { id: 'q15', icon: Target, question: 'Qual vaga tem a melhor taxa de conversão?', category: 'vagas' },
  { id: 'q16', icon: Clock, question: 'Quais vagas precisam de atenção urgente?', category: 'vagas' },
  { id: 'q17', icon: Filter, question: 'Quantos candidatos temos em cada etapa do funil?', category: 'pipeline' },
  { id: 'q18', icon: AlertCircle, question: 'Onde está o gargalo do meu processo seletivo?', category: 'pipeline' },
  { id: 'q19', icon: TrendingUp, question: 'Como está a progressão dos candidatos esta semana?', category: 'pipeline' },
  { id: 'q20', icon: Clock, question: 'Quais candidatos estão parados há mais de 5 dias?', category: 'pipeline' },
  { id: 'q21', icon: Brain, question: 'Quais são as principais recomendações para hoje?', category: 'analise' },
  { id: 'q22', icon: FileText, question: 'Analise o perfil de personalidade ideal para esta vaga', category: 'analise' },
  { id: 'q23', icon: MessageSquare, question: 'Resuma os feedbacks das últimas entrevistas', category: 'analise' },
  { id: 'q24', icon: FileText, question: 'Qual o perfil mais comum entre candidatos aprovados?', category: 'analise' },
  { id: 'q25', icon: Zap, question: 'Sugira melhorias para o processo de triagem', category: 'analise' },
  { id: 'q26', icon: TrendingUp, question: 'Quando devo fechar a vaga de Product Manager?', category: 'previsao' },
  { id: 'q27', icon: Calendar, question: 'Quantas contratações vamos fazer este mês?', category: 'previsao' },
  { id: 'q28', icon: Target, question: 'Qual a probabilidade de sucesso do candidato João Silva?', category: 'previsao' },
  { id: 'q29', icon: Clock, question: 'Estimativa de tempo para preencher as vagas abertas', category: 'previsao' },
  { id: 'q30', icon: Users, question: 'Compare os 3 finalistas da vaga de UX Designer', category: 'comparacao' },
  { id: 'q31', icon: BarChart3, question: 'Compare o desempenho deste mês com o anterior', category: 'comparacao' },
  { id: 'q32', icon: Building, question: 'Qual departamento contrata mais rápido?', category: 'comparacao' },
  { id: 'q33', icon: Target, question: 'Compare a qualidade dos candidatos entre fontes', category: 'comparacao' },
]
