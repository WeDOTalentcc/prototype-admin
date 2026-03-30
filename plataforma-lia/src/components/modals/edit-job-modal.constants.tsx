"use client"

import { Globe, Building, Shield, Lock } from 'lucide-react'

export const WORK_MODELS = [
  { value: 'presencial', label: 'Presencial' },
  { value: 'híbrido', label: 'Híbrido' },
  { value: 'remoto', label: 'Remoto' },
]

export const CONTRACT_TYPES = [
  { value: 'CLT', label: 'CLT' },
  { value: 'PJ', label: 'PJ' },
  { value: 'Estágio', label: 'Estágio' },
  { value: 'Freelancer', label: 'Freelancer' },
  { value: 'Temporário', label: 'Temporário' },
]

export const SENIORITY_LEVELS = [
  { value: 'Estágio', label: 'Estágio' },
  { value: 'Júnior', label: 'Júnior' },
  { value: 'Pleno', label: 'Pleno' },
  { value: 'Sênior', label: 'Sênior' },
  { value: 'Especialista', label: 'Especialista' },
  { value: 'Coordenador', label: 'Coordenador' },
  { value: 'Gerente', label: 'Gerente' },
  { value: 'Diretor', label: 'Diretor' },
]

export const STATUS_OPTIONS = [
  { value: 'Ativa', label: 'Ativa' },
  { value: 'Rascunho', label: 'Rascunho' },
  { value: 'Paralisada', label: 'Paralisada' },
  { value: 'Aguardando aprovação', label: 'Aguardando aprovação' },
  { value: 'Aprovada', label: 'Aprovada' },
  { value: 'Reaberta', label: 'Reaberta' },
  { value: 'Interna', label: 'Interna' },
  { value: 'Fechada (preenchida)', label: 'Fechada (preenchida)' },
  { value: 'Fechada (expirada)', label: 'Fechada (expirada)' },
  { value: 'Cancelada', label: 'Cancelada' },
  { value: 'Arquivada', label: 'Arquivada' },
  { value: 'Concluída', label: 'Concluída' },
]

export const STAGE_OPTIONS = [
  { value: 'Planejamento', label: 'Planejamento' },
  { value: 'Aprovação', label: 'Aprovação' },
  { value: 'Publicada', label: 'Publicada' },
  { value: 'Triagem', label: 'Triagem' },
  { value: 'Entrevistas', label: 'Entrevistas' },
  { value: 'Finalização', label: 'Finalização' },
  { value: 'Encerrada', label: 'Encerrada' },
]

export const VISIBILITY_OPTIONS = [
  { value: 'public', label: 'Pública', icon: <Globe className="w-3.5 h-3.5" /> },
  { value: 'internal', label: 'Interna', icon: <Building className="w-3.5 h-3.5" /> },
  { value: 'confidential', label: 'Confidencial', icon: <Shield className="w-3.5 h-3.5" /> },
  { value: 'hidden', label: 'Oculta', icon: <Lock className="w-3.5 h-3.5" /> },
]

export const TECH_CATEGORIES = [
  { value: 'Linguagens', label: 'Linguagens' },
  { value: 'Frameworks', label: 'Frameworks' },
  { value: 'Banco de Dados', label: 'Banco de Dados' },
  { value: 'Cloud', label: 'Cloud' },
  { value: 'Containers', label: 'Containers' },
  { value: 'CI/CD', label: 'CI/CD' },
  { value: 'Outros', label: 'Outros' },
]

export const SKILL_LEVELS = [
  { value: 'Básico', label: 'Básico' },
  { value: 'Intermediário', label: 'Intermediário' },
  { value: 'Avançado', label: 'Avançado' },
]

export const COMPETENCY_WEIGHTS = [
  { value: 'Essencial', label: 'Essencial' },
  { value: 'Importante', label: 'Importante' },
  { value: 'Desejável', label: 'Desejável' },
]

export const inputStyle = 'h-9 text-xs text-lia-text-primary bg-gray-50 border-lia-border-subtle focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20'
export const selectTriggerStyle = 'h-9 text-xs text-lia-text-primary bg-gray-50 border-lia-border-subtle focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20'
