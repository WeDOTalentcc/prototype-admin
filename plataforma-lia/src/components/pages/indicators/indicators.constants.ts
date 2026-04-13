import React from "react"
import { TrendingUp, Users, AlertTriangle, Brain, Layout, Trophy, Target, BarChart3 } from "lucide-react"
import type { ActiveTab, ViewMode } from "./indicators.types"

// Dados dos recrutadores (mock data expandido)
export const recruitersData = {
  ana_silva: {
    name: "Ana Silva",
    role: "Recrutadora Sênior",
    avatar: "/avatars/ana.jpg",
    department: "Tech",
    activeJobs: 8,
    totalJobs: 12,
    totalCandidates: 234,
    scheduledInterviews: 15,
    completedInterviews: 42,
    totalHires: 5,
    avgTimeToFill: 28,
    conversionRate: 2.1,
    npsScore: 88,
    interviewsPerWeek: 12,
    candidateResponseRate: 76,
    offerAcceptanceRate: 85,
    qualityOfHireScore: 4.2,
    // Novas métricas para ranking e metas
    ranking: 1,
    totalScore: 92.8,
    goals: {
      monthly: {
        hires: { target: 6, current: 5, status: 'on_track' },
        timeToFill: { target: 30, current: 28, status: 'achieved' },
        nps: { target: 85, current: 88, status: 'exceeded' },
        interviews: { target: 40, current: 42, status: 'exceeded' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.2, status: 'exceeded' },
        conversionRate: { target: 2.0, current: 2.1, status: 'exceeded' }
      }
    },
    monthlyTrends: {
      interviews: [8, 12, 15, 18, 14, 16],
      hires: [2, 1, 3, 2, 1, 2],
      sourceQuality: [82, 85, 88, 84, 86, 89],
      nps: [85, 86, 87, 88, 87, 88],
      timeToFill: [32, 30, 29, 28, 27, 28]
    },
    sourcing: {
      linkedin: 45,
      referrals: 23,
      jobBoards: 18,
      headhunting: 14
    }
  },
  juliana_oliveira: {
    name: "Juliana Oliveira",
    role: "Recrutadora",
    avatar: "/avatars/juliana.jpg",
    department: "Design",
    activeJobs: 4,
    totalJobs: 7,
    totalCandidates: 98,
    scheduledInterviews: 6,
    completedInterviews: 24,
    totalHires: 4,
    avgTimeToFill: 25,
    conversionRate: 4.1,
    npsScore: 91,
    interviewsPerWeek: 6,
    candidateResponseRate: 84,
    offerAcceptanceRate: 92,
    qualityOfHireScore: 4.5,
    ranking: 2,
    totalScore: 89.3,
    goals: {
      monthly: {
        hires: { target: 3, current: 4, status: 'exceeded' },
        timeToFill: { target: 30, current: 25, status: 'exceeded' },
        nps: { target: 85, current: 91, status: 'exceeded' },
        interviews: { target: 20, current: 24, status: 'exceeded' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.5, status: 'exceeded' },
        conversionRate: { target: 3.5, current: 4.1, status: 'exceeded' }
      }
    },
    monthlyTrends: {
      interviews: [4, 6, 8, 6, 5, 7],
      hires: [2, 1, 2, 2, 1, 2],
      sourceQuality: [85, 88, 91, 89, 87, 92],
      nps: [88, 89, 90, 91, 90, 91],
      timeToFill: [28, 27, 26, 25, 26, 25]
    },
    sourcing: {
      linkedin: 52,
      referrals: 28,
      jobBoards: 12,
      headhunting: 8
    }
  },
  carlos_mendes: {
    name: "Carlos Mendes",
    role: "Recrutador",
    avatar: "/avatars/carlos.jpg",
    department: "Sales",
    activeJobs: 6,
    totalJobs: 9,
    totalCandidates: 156,
    scheduledInterviews: 8,
    completedInterviews: 28,
    totalHires: 3,
    avgTimeToFill: 32,
    conversionRate: 1.9,
    npsScore: 82,
    interviewsPerWeek: 8,
    candidateResponseRate: 68,
    offerAcceptanceRate: 78,
    qualityOfHireScore: 3.9,
    ranking: 3,
    totalScore: 79.2,
    goals: {
      monthly: {
        hires: { target: 4, current: 3, status: 'behind' },
        timeToFill: { target: 30, current: 32, status: 'behind' },
        nps: { target: 85, current: 82, status: 'behind' },
        interviews: { target: 30, current: 28, status: 'behind' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 3.9, status: 'behind' },
        conversionRate: { target: 2.0, current: 1.9, status: 'behind' }
      }
    },
    monthlyTrends: {
      interviews: [6, 8, 10, 8, 7, 9],
      hires: [1, 1, 2, 1, 0, 1],
      sourceQuality: [75, 78, 82, 79, 76, 81],
      nps: [78, 79, 80, 82, 81, 82],
      timeToFill: [35, 34, 33, 32, 33, 32]
    },
    sourcing: {
      linkedin: 38,
      referrals: 31,
      jobBoards: 22,
      headhunting: 9
    }
  },
  pedro_costa: {
    name: "Pedro Costa",
    role: "Head de Talent Acquisition",
    avatar: "/avatars/pedro.jpg",
    department: "Leadership",
    activeJobs: 3,
    totalJobs: 15,
    totalCandidates: 89,
    scheduledInterviews: 4,
    completedInterviews: 18,
    totalHires: 2,
    avgTimeToFill: 35,
    conversionRate: 2.2,
    npsScore: 85,
    interviewsPerWeek: 4,
    candidateResponseRate: 72,
    offerAcceptanceRate: 88,
    qualityOfHireScore: 4.3,
    ranking: 4,
    totalScore: 82.1,
    goals: {
      monthly: {
        hires: { target: 3, current: 2, status: 'behind' },
        timeToFill: { target: 30, current: 35, status: 'behind' },
        nps: { target: 85, current: 85, status: 'on_track' },
        interviews: { target: 20, current: 18, status: 'behind' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.3, status: 'exceeded' },
        conversionRate: { target: 2.5, current: 2.2, status: 'behind' }
      }
    },
    monthlyTrends: {
      interviews: [3, 4, 5, 4, 3, 4],
      hires: [1, 0, 1, 1, 0, 1],
      sourceQuality: [80, 83, 85, 82, 81, 86],
      nps: [83, 84, 85, 85, 84, 85],
      timeToFill: [38, 37, 36, 35, 36, 35]
    },
    sourcing: {
      linkedin: 41,
      referrals: 35,
      jobBoards: 15,
      headhunting: 9
    }
  }
}


export const TABS: Array<{ id: ActiveTab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "strategic", label: "Indicadores Estratégicos", icon: TrendingUp },
  { id: "recruiters", label: "Performance dos Recrutadores", icon: Users },
  { id: "alerts", label: "Alertas e Monitoramento", icon: AlertTriangle },
  { id: "predictions", label: "Previsoes e Tendencias", icon: Brain },
  { id: "agent_control", label: "Centro de Controle IA", icon: Brain },
]

export const VIEW_MODES: Array<{ id: ViewMode; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "cards", label: "Cards Individuais", icon: Layout },
  { id: "ranking", label: "Classificação Geral", icon: Trophy },
  { id: "goals", label: "Metas e Objetivos", icon: Target },
  { id: "comparison", label: "Comparacao", icon: BarChart3 },
]
