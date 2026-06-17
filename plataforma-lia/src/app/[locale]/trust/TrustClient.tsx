"use client"

import React from"react"
import Link from"next/link"
import { Chip } from"@/components/ui/chip"
import { Award, BadgeCheck, Building2, Download, FileText, Shield, ArrowRight, CheckCircle2, ExternalLink, Mail, Clock, Globe, Server, Brain, MessageSquare, Users, Database, Lock } from"lucide-react"

const certifications = [
  { 
    id: 1, 
    name: 'SOC 2 Type II', 
    status: 'in_progress', 
    targetDate: '2026-06',
    issuer: 'Em processo via Vanta/Drata', 
    description: 'Controles de Segurança, Disponibilidade, Integridade e Confidencialidade',
    icon: Shield
  },
  { 
    id: 2, 
    name: 'ISO 27001:2022', 
    status: 'planned', 
    targetDate: '2026-12',
    issuer: 'Planejado', 
    description: 'Sistema de Gestão de Segurança da Informação',
    icon: Award
  },
  { 
    id: 3, 
    name: 'LGPD Compliance', 
    status: 'active', 
    issued: '2025-01-01',
    expires: '2026-12-31',
    issuer: 'Privacy Tools Brasil', 
    description: 'Lei Geral de Proteção de Dados - Conformidade total com legislação brasileira',
    icon: Lock
  },
  { 
    id: 4, 
    name: 'AI Bias Audit (NYC LL144)', 
    status: 'planned', 
    targetDate: '2026-09',
    issuer: 'Warden AI', 
    description: 'Auditoria de viés algorítmico para IA de recrutamento',
    icon: Brain
  },
]

const subprocessors = [
  { id: 1, name: 'Anthropic', service: 'Inteligência Artificial (Claude)', country: 'EUA', region: 'Global', purpose: 'Motor principal de IA para análise conversacional, triagem e geração de pareceres', category: 'ai', certifications: 'SOC 2 Type II' },
  { id: 2, name: 'Google Cloud', service: 'IA e Speech-to-Text (Gemini)', country: 'EUA', region: 'São Paulo (southamerica-east1)', purpose: 'Transcrição de áudio, fallback de IA e análise multimodal', category: 'ai', certifications: 'ISO 27001, SOC 2, LGPD' },
  { id: 3, name: 'Deepgram', service: 'Speech-to-Text', country: 'EUA', region: 'Global', purpose: 'Transcrição em tempo real de entrevistas por voz', category: 'voice', certifications: 'SOC 2 Type II' },
  { id: 4, name: 'OpenMic.ai', service: 'Voice Screening', country: 'EUA', region: 'Global', purpose: 'Plataforma de entrevistas assíncronas por voz', category: 'voice', certifications: 'Em verificação' },
  { id: 5, name: 'WorkOS', service: 'Autenticação Enterprise', country: 'EUA', region: 'Global', purpose: 'SSO (SAML/OIDC), SCIM Directory Sync, MFA e Audit Logs', category: 'security', certifications: 'SOC 2 Type II, GDPR' },
  { id: 6, name: 'Pearch AI', service: 'Banco de Candidatos', country: 'EUA', region: 'Global', purpose: 'Busca semântica em 800M+ perfis profissionais', category: 'sourcing', certifications: 'Em verificação' },
  { id: 7, name: 'Mailgun (Sinch)', service: 'Email Transacional', country: 'EUA', region: 'Global', purpose: 'Notificações, convites e comunicação por email', category: 'communication', certifications: 'ISO 27001, SOC 2, GDPR' },
  { id: 8, name: 'Meta (WhatsApp Business)', service: 'Mensagens WhatsApp', country: 'EUA', region: 'Brasil', purpose: 'Comunicação com candidatos via WhatsApp Business API', category: 'communication', certifications: 'ISO 27001' },
  { id: 9, name: 'Microsoft', service: 'Graph API (Calendar)', country: 'EUA', region: 'Brasil (Azure)', purpose: 'Integração de calendário e agendamento de entrevistas', category: 'communication', certifications: 'ISO 27001, SOC 2, LGPD' },
  { id: 10, name: 'Merge.dev', service: 'Unified ATS API', country: 'EUA', region: 'Global', purpose: 'Integração unificada com 40+ sistemas ATS/HRIS', category: 'integration', certifications: 'SOC 2 Type II, SOC 2 Type I' },
  { id: 11, name: 'Stripe', service: 'Pagamentos e Billing', country: 'EUA', region: 'Global', purpose: 'Processamento de pagamentos, subscriptions e faturas', category: 'billing', certifications: 'PCI DSS Level 1, SOC 2' },
  { id: 12, name: 'HubSpot', service: 'CRM', country: 'EUA', region: 'Global', purpose: 'Gestão de relacionamento com clientes e onboarding', category: 'crm', certifications: 'SOC 2 Type II, ISO 27001' },
  { id: 13, name: 'Neon', service: 'PostgreSQL Database', country: 'EUA', region: 'São Paulo (sa-east-1)', purpose: 'Banco de dados relacional principal', category: 'infrastructure', certifications: 'SOC 2 Type II' },
  { id: 14, name: 'Upstash', service: 'Redis Cache', country: 'EUA', region: 'São Paulo', purpose: 'Cache de alta performance e rate limiting', category: 'infrastructure', certifications: 'SOC 2 Type II' },
  { id: 15, name: 'Replit', service: 'Cloud Hosting', country: 'EUA', region: 'Global', purpose: 'Hospedagem de aplicação (ambiente de desenvolvimento)', category: 'infrastructure', certifications: 'Em verificação' },
  { id: 16, name: 'Privacy Tools', service: 'LGPD Compliance', country: 'Brasil', region: 'Brasil', purpose: 'Portal do titular de dados e gestão de consentimento', category: 'compliance', certifications: 'LGPD Nativo' },
]

const resources = [
  { id: 1, name: 'Política de Privacidade', type: 'PDF', description: 'Como coletamos, usamos e protegemos seus dados' },
  { id: 2, name: 'Termos de Uso', type: 'PDF', description: 'Condições gerais de uso da plataforma' },
  { id: 3, name: 'DPA (Data Processing Agreement)', type: 'PDF', description: 'Acordo de processamento de dados para clientes enterprise' },
  { id: 4, name: 'Política de Segurança', type: 'PDF', description: 'Práticas e controles de segurança da informação' },
  { id: 5, name: 'Lista de Subprocessadores', type: 'PDF', description: 'Relação atualizada de terceiros que processam dados' },
  { id: 6, name: 'Relatório de IA Responsável', type: 'PDF', description: 'Práticas de ética e transparência em IA de recrutamento' },
]

const complianceFrameworks = [
  { name: 'LGPD', status: 'compliant', description: 'Lei Geral de Proteção de Dados (Brasil)' },
  { name: 'NYC LL144', status: 'planned', description: 'Lei de Auditoria de Viés em IA (Nova York)' },
  { name: 'EU AI Act', status: 'monitoring', description: 'Regulamento Europeu de Inteligência Artificial' },
  { name: 'SOX', status: 'compliant', description: 'Controles internos e auditoria' },
]

function getStatusBadge(status: string) {
  switch (status) {
    case 'active':
    case 'compliant':
      return (
        <Chip variant="success">
          <CheckCircle2 className="w-3 h-3" />
          Ativo
        </Chip>
      )
    case 'in_progress':
      return (
        <Chip variant="neutral" muted>
          <Clock className="w-3 h-3" />
          Em Progresso
        </Chip>
      )
    case 'planned':
    case 'monitoring':
      return <Chip variant="neutral">Planejado</Chip>
    default:
      return null
  }
}

function getCategoryIcon(category: string) {
  switch (category) {
    case 'ai': return Brain
    case 'voice': return MessageSquare
    case 'security': return Lock
    case 'sourcing': return Users
    case 'communication': return MessageSquare
    case 'integration': return Globe
    case 'billing': return FileText
    case 'crm': return Users
    case 'infrastructure': return Server
    case 'compliance': return Shield
    default: return Building2
  }
}

export default function PublicTrustCenterPage() {
  const activeCompliance = complianceFrameworks.filter(c => c.status === 'compliant').length
  
  return (
    <div className="min-h-screen bg-lia-bg-primary">
      <header className="bg-lia-bg-primary">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-lia-btn-primary-bg dark:bg-lia-bg-secondary flex items-center justify-center">
              <span className="text-white font-semibold text-lg">W</span>
            </div>
            <div>
              <h1 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">WeDo Talent</h1>
              <p className="text-xs text-lia-text-secondary">Centro de Confiança</p>
            </div>
          </div>
          <nav className="flex items-center gap-4">
            <Link 
              href="/privacidade" 
              className="text-sm text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
            >
              Portal LGPD
            </Link>
            <Link 
              href="/login" 
              className="text-sm px-4 py-2 rounded-xl bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
            >
              Acessar Plataforma
            </Link>
          </nav>
        </div>
      </header>

      <main id="main-content" className="max-w-6xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full  text-sm font-medium mb-4">
            <Shield className="w-4 h-4" />
            Segurança & Compliance
          </div>
          <h1 className="text-4xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-4">
            Centro de Confiança
          </h1>
          <p className="text-lg text-lia-text-secondary max-w-2xl mx-auto">
            Transparência sobre nossas práticas de segurança, certificações e como protegemos os dados dos nossos clientes e candidatos.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-status-success/15 flex items-center justify-center mx-auto mb-4">
              <BadgeCheck className="w-6 h-6 text-status-success" />
            </div>
            <div className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">{activeCompliance}</div>
            <p className="text-lia-text-secondary text-sm">Frameworks Ativos</p>
          </div>

          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-4">
              <Building2 className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">{subprocessors.length}</div>
            <p className="text-lia-text-secondary text-sm">Subprocessadores</p>
          </div>

          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-wedo-purple/15 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-6 h-6 text-wedo-purple" />
            </div>
            <div className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">{resources.length}</div>
            <p className="text-lia-text-secondary text-sm">Documentos</p>
          </div>

          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-status-warning/15 flex items-center justify-center mx-auto mb-4">
              <Globe className="w-6 h-6 text-status-warning" />
            </div>
            <div className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">33+</div>
            <p className="text-lia-text-secondary text-sm">Integrações</p>
          </div>
        </div>

        <section className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Award className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">Certificações & Compliance</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {certifications.map((cert) => {
              const IconComponent = cert.icon
              return (
                <div 
                  key={cert.id}
                  className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
                      <IconComponent className="w-6 h-6 text-lia-text-secondary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">{cert.name}</h3>
                        {getStatusBadge(cert.status)}
                      </div>
                      <p className="text-sm text-lia-text-secondary mb-3">{cert.description}</p>
                      <div className="text-xs text-lia-text-secondary">
                        <p>{cert.issuer}</p>
                        {cert.targetDate && <p>Previsão: {cert.targetDate}</p>}
                        {cert.expires && <p>Válido até: {new Date(cert.expires).toLocaleDateString('pt-BR')}</p>}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        <section className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Building2 className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">Subprocessadores</h2>
          </div>
          <p className="text-lia-text-secondary mb-6">
            Lista completa de terceiros que processam dados em nosso nome, conforme exigido pela LGPD e GDPR. 
            Todos os subprocessadores são avaliados quanto às suas práticas de segurança.
          </p>
          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-lia-bg-secondary border-b border-lia-border-subtle">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-medium text-lia-text-secondary uppercase">Empresa</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-lia-text-secondary uppercase">Serviço</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-lia-text-secondary uppercase">País</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-lia-text-secondary uppercase">Região de Dados</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-lia-text-secondary uppercase">Certificações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-lia-border-subtle">
                  {subprocessors.map((sub) => {
                    const IconComponent = getCategoryIcon(sub.category)
                    return (
                      <tr key={sub.id} className="hover:bg-lia-bg-secondary">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
                              <IconComponent className="w-4 h-4 text-lia-text-secondary" />
                            </div>
                            <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{sub.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-lia-text-secondary">{sub.service}</td>
                        <td className="px-6 py-4 text-sm text-lia-text-secondary">{sub.country}</td>
                        <td className="px-6 py-4 text-sm text-lia-text-secondary">{sub.region}</td>
                        <td className="px-6 py-4 text-xs text-lia-text-secondary">{sub.certifications}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <p className="text-xs text-lia-text-secondary mt-4">
            Última atualização: Janeiro 2026. Para notificações de alterações na lista de subprocessadores, entre em contato com nossa equipe.
          </p>
        </section>

        <section className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Download className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">Recursos para Download</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.map((resource) => (
              <button 
                key={resource.id}
                className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-4 flex items-start gap-4 hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none text-left"
              >
                <div className="w-10 h-10 rounded-md bg-status-error/15 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-status-error" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-lia-text-primary dark:text-lia-text-primary text-sm">{resource.name}</p>
                  <p className="text-xs text-lia-text-secondary mt-1">{resource.description}</p>
                </div>
                <Download className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
              </button>
            ))}
          </div>
        </section>

        <section className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Brain className="w-6 h-6 text-wedo-cyan" />
            <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">IA Responsável</h2>
          </div>
          
          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 mb-6">
            <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary mb-4">Metodologias de Avaliação</h3>
            <p className="text-sm text-lia-text-secondary mb-4">
              Nossa IA utiliza múltiplas metodologias científicas e auditáveis para avaliar candidatos de forma justa e transparente:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-lia-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                    <MessageSquare className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">WSI (WeDoTalent Skill Index)</h4>
                </div>
                <p className="text-xs text-lia-text-secondary">
                  Índice conversacional que combina IA com psicometria. Base teórica: CBI (McClelland), Taxonomia de Bloom, Modelo Dreyfus e Big Five. Avalia competências técnicas (70%) e comportamentais (30%) em 5-10 minutos.
                </p>
              </div>
              <div className="border border-lia-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-md bg-wedo-purple/15 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-wedo-purple" />
                  </div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">Rubric Evaluation (CV vs Vaga)</h4>
                </div>
                <p className="text-xs text-lia-text-secondary">
                  Análise estruturada do currículo contra requisitos da vaga usando rubricas ponderadas. Cada critério recebe pontuação de 1-5 com justificativa explícita e evidências do CV.
                </p>
              </div>
              <div className="border border-lia-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-md bg-status-success/15 flex items-center justify-center">
                    <Award className="w-4 h-4 text-status-success" />
                  </div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">IA Scoring</h4>
                </div>
                <p className="text-xs text-lia-text-secondary">
                  Score numérico (0-100) calculado a partir de múltiplos fatores: aderência técnica, experiência relevante, formação e fit cultural. Algoritmo documentado e auditável.
                </p>
              </div>
              <div className="border border-lia-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-md bg-status-warning/15 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-status-warning" />
                  </div>
                  <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">IA Opinion (Parecer)</h4>
                </div>
                <p className="text-xs text-lia-text-secondary">
                  Parecer qualitativo em linguagem natural explicando pontos fortes, gaps identificados e recomendação. Sempre acompanhado de justificativa baseada em evidências.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Transparência Algorítmica</h3>
                <ul className="space-y-2 text-sm text-lia-text-secondary">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Explicação automática de todas as decisões (LGPD Art. 20)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Todas as metodologias documentadas e auditáveis</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Candidatos podem solicitar explicação de avaliação</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Logs completos de decisão para auditoria</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Supervisão Humana (EU AI Act Art. 14)</h3>
                <ul className="space-y-2 text-sm text-lia-text-secondary">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>IA nunca toma decisão final de contratação/rejeição</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Recrutador humano revisa todas as recomendações</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Candidatos podem solicitar revisão humana</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Override humano sempre disponível</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Mitigação de Viés</h3>
                <ul className="space-y-2 text-sm text-lia-text-secondary">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Exclusão de campos protegidos (gênero, idade, etnia, estado civil)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Prompts com instruções anti-viés explícitas</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Auditoria anual de viés planejada (Warden AI)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Monitoramento de disparate impact por grupos demográficos</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Direitos do Candidato</h3>
                <ul className="space-y-2 text-sm text-lia-text-secondary">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Notificação de uso de IA na avaliação (NYC LL144)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Acesso aos dados usados na avaliação (LGPD Art. 18)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Explicação da lógica de decisão (LGPD Art. 20)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    <span>Solicitação de exclusão de dados (LGPD Art. 18-VI)</span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="mt-6 p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default">
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                <strong>Conformidade Regulatória:</strong> Nossa plataforma está em conformidade com LGPD (Brasil), 
                em preparação para NYC LL144 (Nova York) e monitorando requisitos do EU AI Act (União Europeia). 
                A IA de recrutamento é classificada como"alto risco" pelo EU AI Act, e implementamos controles proporcionais.
              </p>
            </div>
          </div>
        </section>

        <section className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-8">
          <div className="flex items-start gap-6">
            <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
              <Mail className="w-6 h-6 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">Dúvidas sobre Segurança?</h2>
              <p className="text-lia-text-secondary mb-4">
                Entre em contato com nossa equipe de segurança e compliance para questões sobre certificações, 
                auditorias, avaliações de fornecedores ou solicitações de DPA.
              </p>
              <div className="flex flex-wrap gap-4">
                <a 
                  href="mailto:security@wedotalent.com.br"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active text-sm font-medium transition-colors motion-reduce:transition-none"
                >
                  <Mail className="w-4 h-4" />
                  security@wedotalent.com.br
                </a>
                <a 
                  href="mailto:dpo@wedotalent.com.br"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary text-sm font-medium hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                >
                  <Shield className="w-4 h-4" />
                  DPO: dpo@wedotalent.com.br
                </a>
                <Link 
                  href="/privacidade"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary text-sm font-medium hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                >
                  <ExternalLink className="w-4 h-4" />
                  Portal LGPD
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-lia-bg-primary border-t border-lia-border-subtle mt-12">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between text-sm text-lia-text-secondary">
          <p>&copy; {new Date().getFullYear()} WeDo Talent. Todos os direitos reservados.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacidade" className="hover:text-lia-text-primary">Privacidade</Link>
            <Link href="/" className="hover:text-lia-text-primary">Termos</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
